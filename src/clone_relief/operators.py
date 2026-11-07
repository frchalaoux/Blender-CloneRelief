"""Minimal Blender operators for source/target capture and relief application."""

import bpy
import bmesh
from bpy.app.handlers import persistent
from bpy.props import EnumProperty, FloatProperty, IntProperty, StringProperty
from mathutils import Vector
from textwrap import wrap

from .density import ResolutionReport, analyze_resolution, estimate_face_count_upper_bound
from .blender_adapter import (
    CapturedSelection,
    active_edit_mesh,
    capture_selection,
    prepare_capture_view,
    topology_signature,
    validate_capture,
    write_world_coordinates,
)
from .relief import apply_relief, extract_relief

_SOURCE_CAPTURE: CapturedSelection | None = None
_TARGET_CAPTURE: CapturedSelection | None = None
_COMPARISON_COLLECTION_NAME = "Clone Relief Comparison (display only)"
_COMPONENT_INSPECTION_ITEMS: list[tuple[str, str, str]] = []
_COMPONENT_INSPECTION_CACHE: tuple[int, str, tuple[tuple[int, ...], ...]] | None = None


def _component_inspection_items(
    _operator: bpy.types.Operator,
    _context: bpy.types.Context,
) -> list[tuple[str, str, str]]:
    """Keep dynamic component enum strings alive for Blender's RNA property."""
    return _COMPONENT_INSPECTION_ITEMS or [("0", "Aucune composante chargée", "")]


def _operator_is_registered(operator_class: type[bpy.types.Operator]) -> bool:
    """Check Blender's operator registry by its ``module.name`` identifier."""
    module_name, operator_name = operator_class.bl_idname.split(".", 1)
    operator = getattr(getattr(bpy.ops, module_name), operator_name)
    try:
        operator.get_rna_type()
    except KeyError:
        return False
    return True


def _set_ui_status(
    context: bpy.types.Context,
    *,
    source: str | None = None,
    target: str | None = None,
    message: str | None = None,
    level: str | None = None,
) -> None:
    """Update optional sidebar status without coupling operators to UI setup."""
    settings = getattr(context.scene, "clone_relief_settings", None)
    if settings is None:
        return
    if source is not None:
        settings.source_status = source
    if target is not None:
        settings.target_status = target
    if message is not None:
        settings.last_message = message
        message_lines = getattr(settings, "message_lines", None)
        if message_lines is not None:
            message_lines.clear()
            region = getattr(context, "region", None)
            width = max(42, min(80, (region.width - 48) // 8)) if region and region.width else 42
            for line_text in wrap(
                message,
                width=width,
                break_long_words=False,
                break_on_hyphens=False,
            ) or [message]:
                line = message_lines.add()
                line.text = line_text
    if level is not None and hasattr(settings, "message_level"):
        settings.message_level = level


def _capture_component_note(capture: CapturedSelection) -> tuple[str, str]:
    """Describe minor disconnected groups excluded from a dominant capture."""
    if not capture.ignored_component_sizes:
        return "", "INFO"
    ignored_faces = sum(capture.ignored_component_sizes)
    ignored_groups = len(capture.ignored_component_sizes)
    group_word = "groupe" if ignored_groups == 1 else "groupes"
    disconnected_word = "disjoint" if ignored_groups == 1 else "disjoints"
    face_word = "face écartée" if ignored_faces == 1 else "faces écartées"
    return (
        f" Groupe principal retenu; {ignored_faces} {face_word} "
        f"sur {ignored_groups} {group_word} {disconnected_word}. Vérifie la sélection.",
        "WARNING",
    )


def _select_face_indices(
    context: bpy.types.Context,
    obj: bpy.types.Object,
    bm: bmesh.types.BMesh,
    face_indices: tuple[int, ...],
) -> None:
    """Replace the current Edit Mode selection with the requested faces."""
    context.tool_settings.mesh_select_mode = (False, False, True)
    for face in bm.faces:
        if face.select:
            face.select_set(False)
    for edge in bm.edges:
        if edge.select:
            edge.select_set(False)
    for vertex in bm.verts:
        if vertex.select:
            vertex.select_set(False)
    for index in face_indices:
        bm.faces[index].select_set(True)
    bm.select_flush_mode()
    bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)
    screen = getattr(context, "screen", None)
    if screen is not None:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()


def _restore_captured_face_selection(
    context: bpy.types.Context,
    capture: CapturedSelection | None,
    role_label: str,
) -> None:
    """Restore a captured face region as the current Edit Mode selection."""
    if capture is None:
        raise ValueError(f"Aucune sélection {role_label} capturée dans cette session.")
    obj, bm = active_edit_mesh(context)
    validate_capture(capture, obj, bm)
    _select_face_indices(context, obj, bm, capture.face_indices)


def _format_displacement(context: bpy.types.Context, value: float) -> str:
    """Format a world-space displacement in millimetres when units are known."""
    units = context.scene.unit_settings
    if units.system != "NONE":
        millimetres = value * units.scale_length * 1000.0
        if millimetres < 0.01:
            return f"{millimetres * 1000:.1f} µm"
        return f"{millimetres:.3f} mm"
    return f"{value:.6g} unités Blender"


def _direction_label(direction: str) -> str:
    """Return a concise user-facing description of the selected transfer mode."""
    if direction == "OUTWARD":
        return "unidirectionnel, au-dessus de la cible"
    return "bidirectionnel, creux et bosses"


def _visibility_threshold(context: bpy.types.Context) -> float:
    """Return the displacement below which the UI warns that relief is subtle."""
    units = context.scene.unit_settings
    if units.system != "NONE":
        return 0.00005 / units.scale_length  # 0.05 mm expressed in scene units.
    return 1e-5


def _through_selection_enabled(context: bpy.types.Context) -> bool:
    """Whether the active 3D View can select faces through the visible surface."""
    context_area = getattr(context, "area", None)
    area = context_area if context_area and context_area.type == "VIEW_3D" else None
    screen = getattr(context, "screen", None)
    if area is None and screen is not None:
        area = next((item for item in screen.areas if item.type == "VIEW_3D"), None)
    if area is None:
        return False
    space = area.spaces.active
    return space.shading.type == "WIREFRAME" or space.shading.show_xray


@persistent
def _prepare_after_file_load(_unused: object) -> None:
    """Restore Clone Relief's safe face-selection view after opening a blend."""
    global _SOURCE_CAPTURE, _TARGET_CAPTURE
    _SOURCE_CAPTURE = None
    _TARGET_CAPTURE = None
    prepare_capture_view(bpy.context)
    from .ui import apply_selection_opacity

    apply_selection_opacity(bpy.context)
    settings = getattr(bpy.context.scene, "clone_relief_settings", None)
    if settings is not None:
        _set_ui_status(
            bpy.context,
            source="Non capturée",
            target="Non capturée",
            message=(
                "Fichier ouvert : vue préparée en Solid, X-Ray désactivé et sélection de faces. "
                "Sélectionnez puis capturez la source."
            ),
            level="INFO",
        )


def _reject_through_selection(context: bpy.types.Context) -> None:
    """Correct through-selection settings and ask for a fresh surface selection."""
    if _through_selection_enabled(context):
        prepare_capture_view(context)
        raise ValueError(
            "La vue a été préparée : Solid, X-Ray désactivé, sélection de faces. "
            "Refaites la sélection de surface puis relancez la capture."
        )


def _evaluate_transfer(
    context: bpy.types.Context,
    *,
    intensity: float,
    gain: float,
    scale: float,
    falloff_fraction: float,
    max_displacement: float,
    direction: str,
) -> tuple[bpy.types.Object, bmesh.types.BMesh, CapturedSelection, tuple[tuple[float, float, float], ...], int, float]:
    """Validate captures and calculate a transfer without changing the mesh."""
    if _SOURCE_CAPTURE is None:
        raise ValueError("Aucune source capturée. Sélectionnez la source puis cliquez Capture Source.")
    if _TARGET_CAPTURE is None:
        raise ValueError("La source est conservée, mais la cible doit être recapturée avant l’aperçu ou l’application.")
    obj, bm = active_edit_mesh(context)
    signature = topology_signature(bm)
    validate_capture(_SOURCE_CAPTURE, obj, bm, current_signature=signature)
    validate_capture(_TARGET_CAPTURE, obj, bm, current_signature=signature)
    if set(_SOURCE_CAPTURE.face_indices).intersection(_TARGET_CAPTURE.face_indices):
        raise ValueError("Source et cible se chevauchent : recapturez une cible sans face commune")

    source = _SOURCE_CAPTURE.as_patch()
    # Every preview/apply uses the coordinates saved by Capture Target. This
    # makes reapplying with new settings replace the previous result instead
    # of stacking another transfer on the already modified mesh.
    target = _TARGET_CAPTURE.as_patch()
    field, _ = extract_relief(source)
    updated = apply_relief(
        field,
        target,
        intensity=intensity,
        gain=gain,
        scale=scale,
        falloff_fraction=falloff_fraction,
        max_displacement=max_displacement if max_displacement > 0.0 else None,
        direction=direction,
    )
    displacements = tuple(
        (Vector(result) - Vector(original)).length
        for original, result in zip(target.vertices, updated)
    )
    moved = sum(value > 1e-12 for value in displacements)
    maximum = max(displacements, default=0.0)
    return obj, bm, _TARGET_CAPTURE, updated, moved, maximum


class CLONERELIEF_OT_preview(bpy.types.Operator):
    """Estimate the transfer without changing target geometry."""

    bl_idname = "clone_relief.preview"
    bl_label = "Preview Clone Relief"
    bl_description = "Estimate coverage and maximum displacement without changing the mesh"

    intensity: FloatProperty(name="Intensity", default=1.0, min=0.0, max=1.0)
    gain: FloatProperty(name="Relief Gain", default=1.0, min=0.1, max=100.0)
    scale: FloatProperty(name="Pattern Scale", default=1.0, min=0.001, soft_max=4.0)
    falloff_fraction: FloatProperty(name="Edge Falloff", default=0.25, min=0.001, max=1.0)
    max_displacement: FloatProperty(name="Maximum Displacement", default=0.0, min=0.0, soft_max=0.1)
    direction: EnumProperty(
        name="Relief Direction",
        description="Keep the relief above the target or preserve positive and negative source details",
        items=(
            ("OUTWARD", "Unidirectionnel (+ normale)", "Only displace outward along target normals"),
            ("BIDIRECTIONAL", "Bidirectionnel (± normale)", "Keep positive and negative source deviations"),
        ),
        default="OUTWARD",
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.edit_object is not None and context.edit_object.type == "MESH"

    def execute(self, context: bpy.types.Context) -> set[str]:
        try:
            _obj, _bm, target, _updated, moved, maximum = _evaluate_transfer(
                context,
                intensity=self.intensity,
                gain=self.gain,
                scale=self.scale,
                falloff_fraction=self.falloff_fraction,
                max_displacement=self.max_displacement,
                direction=self.direction,
            )
        except (ValueError, RuntimeError, ArithmeticError) as error:
            message = str(error)
            _set_ui_status(context, message=message, level="ERROR")
            self.report({"ERROR"}, "Aperçu impossible. Consultez le détail dans le panneau Clone Relief.")
            return {"CANCELLED"}

        magnitude = _format_displacement(context, maximum)
        if moved == 0:
            message = "Aucun sommet ne bougerait. Vérifiez les captures et l’échelle du motif."
            level, report_level = "WARNING", "WARNING"
        elif maximum < _visibility_threshold(context):
            desired_gain = self.gain * (_visibility_threshold(context) / maximum)
            gain_advice = (
                f"Essayez Relief Gain ≈ {desired_gain:.1f}×. "
                if desired_gain <= 100.0
                else "Même 100× ne suffira probablement pas : choisissez une source plus texturée. "
            )
            message = (
                f"Aperçu très faible : {moved}/{len(target.vertex_indices)} sommets, "
                f"déplacement max. {magnitude}; mode {_direction_label(self.direction)}. {gain_advice}"
                "Densifiez si le diagnostic le recommande."
            )
            level, report_level = "WARNING", "WARNING"
        else:
            message = (
                f"Aperçu : {moved}/{len(target.vertex_indices)} sommets bougeraient; "
                f"déplacement max. {magnitude}; mode {_direction_label(self.direction)}. "
                "Le maillage n’a pas été modifié."
            )
            level, report_level = "INFO", "INFO"
        _set_ui_status(context, message=message, level=level)
        self.report({report_level}, "Aperçu terminé. Consultez le résultat détaillé dans Clone Relief.")
        return {"FINISHED"}


class CLONERELIEF_OT_copy_message(bpy.types.Operator):
    """Copy the full latest message to the system clipboard."""

    bl_idname = "clone_relief.copy_message"
    bl_label = "Copier le message Clone Relief"
    bl_description = "Copier le texte complet du dernier message dans le presse-papiers"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        settings = getattr(context.scene, "clone_relief_settings", None)
        return settings is not None and bool(settings.last_message)

    def execute(self, context: bpy.types.Context) -> set[str]:
        context.window_manager.clipboard = context.scene.clone_relief_settings.last_message
        self.report({"INFO"}, "Message copié dans le presse-papiers.")
        return {"FINISHED"}


def _subdivision_plan(
    context: bpy.types.Context,
    cuts: int,
) -> tuple[
    bpy.types.Object,
    bmesh.types.BMesh,
    tuple[bmesh.types.BMFace, ...],
    tuple[bmesh.types.BMEdge, ...],
    tuple[bmesh.types.BMFace, ...],
    ResolutionReport,
    int,
]:
    """Validate captures and calculate a bounded target subdivision plan."""
    if _SOURCE_CAPTURE is None or _TARGET_CAPTURE is None:
        raise ValueError("Capture source and target regions first")
    obj, bm = active_edit_mesh(context)
    signature = topology_signature(bm)
    validate_capture(_SOURCE_CAPTURE, obj, bm, current_signature=signature)
    validate_capture(_TARGET_CAPTURE, obj, bm, current_signature=signature)
    target_faces = tuple(bm.faces[index] for index in _TARGET_CAPTURE.face_indices)
    edges = tuple(sorted({edge for face in target_faces for edge in face.edges}, key=lambda edge: edge.index))
    if not target_faces or not edges:
        raise ValueError("Captured target has no faces or edges")
    affected = {face for edge in edges for face in edge.link_faces}
    affected_faces = tuple(sorted(affected, key=lambda face: face.index))
    source_patch = _SOURCE_CAPTURE.as_patch()
    target_patch = _TARGET_CAPTURE.as_patch()
    resolution = analyze_resolution(source_patch, target_patch)
    estimated_faces = estimate_face_count_upper_bound(
        len(bm.faces),
        tuple(len(face.verts) for face in affected_faces),
        cuts,
    )
    return obj, bm, target_faces, edges, affected_faces, resolution, estimated_faces


class CLONERELIEF_OT_capture_source(bpy.types.Operator):
    """Capture one connected source face region in Edit Mode."""

    bl_idname = "clone_relief.capture_source"
    bl_label = "Capture Relief Source"
    bl_description = "Store the selected connected face region as the relief source"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.edit_object is not None and context.edit_object.type == "MESH"

    def execute(self, context: bpy.types.Context) -> set[str]:
        global _SOURCE_CAPTURE, _TARGET_CAPTURE
        try:
            _reject_through_selection(context)
            capture = capture_selection(
                context,
                role="source",
                allow_dominant_component=True,
            )
        except (ValueError, RuntimeError) as error:
            previous = _SOURCE_CAPTURE
            if previous is None:
                source_status = f"Échec : {error}"
                preserved = "Aucune ancienne capture source à conserver."
            else:
                source_status = (
                    f"Capture conservée : {len(previous.face_indices)} faces / "
                    f"{len(previous.vertex_indices)} sommets"
                )
                preserved = "L’ancienne source capturée est conservée."
            message = f"Capture source refusée : {error} {preserved}"
            _set_ui_status(context, source=source_status, message=message, level="ERROR")
            self.report({"ERROR"}, "Capture Source refusée. Consultez le détail dans Clone Relief.")
            return {"CANCELLED"}
        _SOURCE_CAPTURE = capture
        _TARGET_CAPTURE = None
        source_status = f"{len(capture.face_indices)} faces / {len(capture.vertex_indices)} sommets"
        component_note, message_level = _capture_component_note(capture)
        if component_note:
            source_status += " (groupe principal)"
        _set_ui_status(
            context,
            source=source_status,
            target="Non capturée",
            message=f"Source capturée : {len(capture.face_indices)} faces, "
            f"{len(capture.vertex_indices)} sommets. Recapturez la cible.{component_note}",
            level=message_level,
        )
        self.report({message_level}, f"{capture.object_name} : source, {source_status} capturés")
        return {"FINISHED"}


class CLONERELIEF_OT_capture_target(bpy.types.Operator):
    """Capture one connected target face region on the source object."""

    bl_idname = "clone_relief.capture_target"
    bl_label = "Capture Relief Target"
    bl_description = "Store the selected target region and its starting geometry for repeatable applications"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.edit_object is not None and context.edit_object.type == "MESH"

    def execute(self, context: bpy.types.Context) -> set[str]:
        global _TARGET_CAPTURE
        if _SOURCE_CAPTURE is None:
            message = "Capturez d’abord la source."
            _set_ui_status(context, target="Non capturée", message=message, level="ERROR")
            self.report({"ERROR"}, "Capture Source d’abord. Détail dans le panneau Clone Relief.")
            return {"CANCELLED"}
        try:
            _reject_through_selection(context)
            capture = capture_selection(
                context,
                role="target",
                allow_dominant_component=True,
            )
            obj, bm = active_edit_mesh(context)
            validate_capture(_SOURCE_CAPTURE, obj, bm, current_signature=capture.topology_signature)
            if set(capture.face_indices).intersection(_SOURCE_CAPTURE.face_indices):
                raise ValueError("Source et cible se chevauchent; sélectionnez des faces distinctes.")
        except (ValueError, RuntimeError) as error:
            previous = _TARGET_CAPTURE
            if previous is None:
                target_status = f"Échec : {error}"
                preserved = "Aucune ancienne capture cible à conserver."
            else:
                target_status = (
                    f"Capture conservée : {len(previous.face_indices)} faces / "
                    f"{len(previous.vertex_indices)} sommets"
                )
                preserved = "L’ancienne cible capturée est conservée."
            message = f"Capture cible refusée : {error} {preserved}"
            _set_ui_status(context, target=target_status, message=message, level="ERROR")
            self.report({"ERROR"}, "Capture Target refusée. Consultez le détail dans Clone Relief.")
            return {"CANCELLED"}
        _TARGET_CAPTURE = capture
        target_status = f"{len(capture.face_indices)} faces / {len(capture.vertex_indices)} sommets"
        component_note, message_level = _capture_component_note(capture)
        if component_note:
            target_status += " (groupe principal)"
        _set_ui_status(
            context,
            target=target_status,
            message=f"Cible capturée : {len(capture.face_indices)} faces, "
            f"{len(capture.vertex_indices)} sommets.{component_note}",
            level=message_level,
        )
        self.report(
            {message_level},
            "Cible capturée. Consultez les comptes dans le panneau Clone Relief.",
        )
        return {"FINISHED"}


class CLONERELIEF_OT_restore_source_selection(bpy.types.Operator):
    """Reselect the source faces saved by Capture Source."""

    bl_idname = "clone_relief.restore_source_selection"
    bl_label = "Reselect Captured Source"
    bl_description = "Restore the captured source faces as the current selection"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.edit_object
        return (
            _SOURCE_CAPTURE is not None
            and obj is not None
            and obj.type == "MESH"
            and obj.as_pointer() == _SOURCE_CAPTURE.object_pointer
        )

    def execute(self, context: bpy.types.Context) -> set[str]:
        try:
            _restore_captured_face_selection(context, _SOURCE_CAPTURE, "source")
        except (ValueError, RuntimeError) as error:
            _set_ui_status(context, message=f"Sélection source non rétablie : {error}", level="ERROR")
            self.report({"ERROR"}, "Sélection source non rétablie. Consultez Clone Relief.")
            return {"CANCELLED"}
        _set_ui_status(
            context,
            message="Sélection source rétablie depuis sa capture. La géométrie n’a pas été modifiée.",
            level="INFO",
        )
        self.report({"INFO"}, "Sélection source rétablie.")
        return {"FINISHED"}


class CLONERELIEF_OT_restore_target_selection(bpy.types.Operator):
    """Reselect the target faces saved by Capture Target."""

    bl_idname = "clone_relief.restore_target_selection"
    bl_label = "Reselect Captured Target"
    bl_description = "Restore the captured target faces as the current selection"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.edit_object
        return (
            _TARGET_CAPTURE is not None
            and obj is not None
            and obj.type == "MESH"
            and obj.as_pointer() == _TARGET_CAPTURE.object_pointer
        )

    def execute(self, context: bpy.types.Context) -> set[str]:
        try:
            _restore_captured_face_selection(context, _TARGET_CAPTURE, "cible")
        except (ValueError, RuntimeError) as error:
            _set_ui_status(context, message=f"Sélection cible non rétablie : {error}", level="ERROR")
            self.report({"ERROR"}, "Sélection cible non rétablie. Consultez Clone Relief.")
            return {"CANCELLED"}
        _set_ui_status(
            context,
            message="Sélection cible rétablie depuis sa capture. La géométrie n’a pas été modifiée.",
            level="INFO",
        )
        self.report({"INFO"}, "Sélection cible rétablie.")
        return {"FINISHED"}


class CLONERELIEF_OT_apply(bpy.types.Operator):
    """Apply captured source relief to the captured target in one undo step."""

    bl_idname = "clone_relief.apply"
    bl_label = "Apply Clone Relief"
    bl_description = "Apply or replace the relief using the captured target geometry as the baseline"
    bl_options = {"REGISTER", "UNDO"}

    intensity: FloatProperty(name="Intensity", default=1.0, min=0.0, max=1.0)
    scale: FloatProperty(name="Pattern Scale", default=1.0, min=0.001, soft_max=4.0)
    falloff_fraction: FloatProperty(name="Edge Falloff", default=0.25, min=0.001, max=1.0)
    gain: FloatProperty(name="Relief Gain", default=1.0, min=0.1, max=100.0)
    max_displacement: FloatProperty(name="Maximum Displacement", default=0.0, min=0.0, soft_max=0.1)
    direction: EnumProperty(
        name="Relief Direction",
        description="Keep the relief above the target or preserve positive and negative source details",
        items=(
            ("OUTWARD", "Unidirectionnel (+ normale)", "Only displace outward along target normals"),
            ("BIDIRECTIONAL", "Bidirectionnel (± normale)", "Keep positive and negative source deviations"),
        ),
        default="OUTWARD",
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.edit_object is not None and context.edit_object.type == "MESH"

    def execute(self, context: bpy.types.Context) -> set[str]:
        try:
            obj, bm, target_capture, updated, moved, maximum = _evaluate_transfer(
                context,
                intensity=self.intensity,
                gain=self.gain,
                scale=self.scale,
                falloff_fraction=self.falloff_fraction,
                max_displacement=self.max_displacement,
                direction=self.direction,
            )
        except (ValueError, RuntimeError, ArithmeticError) as error:
            message = f"Relief non appliqué : {error}"
            _set_ui_status(context, message=message, level="ERROR")
            self.report({"ERROR"}, "Apply Relief refusé. Consultez le détail dans Clone Relief.")
            return {"CANCELLED"}

        write_world_coordinates(obj, bm, target_capture.vertex_indices, updated)
        magnitude = _format_displacement(context, maximum)
        warning_threshold = _visibility_threshold(context)
        if moved == 0:
            message = (
                "Aucun relief produit. La cible a été rétablie depuis sa géométrie capturée; "
                "la capture reste active pour ajuster les paramètres et réessayer."
            )
            level, report_level = "WARNING", "WARNING"
        elif maximum < warning_threshold:
            message = (
                f"Relief appliqué depuis la géométrie cible capturée, mais très faible : "
                f"{moved}/{len(target_capture.vertex_indices)} "
                f"sommets; déplacement max. {magnitude}; mode {_direction_label(self.direction)}. "
                "Ajustez les paramètres et réappliquez; le résultat repartira de la même géométrie capturée."
            )
            level, report_level = "WARNING", "WARNING"
        else:
            message = (
                f"Réussite : relief recalculé depuis la cible capturée sur "
                f"{moved}/{len(target_capture.vertex_indices)} sommets; déplacement max. {magnitude}; "
                f"mode {_direction_label(self.direction)}. Changez les paramètres puis réappliquez, "
                "ou recapturez une autre cible. Annuler avec Undo."
            )
            level, report_level = "INFO", "INFO"
        _set_ui_status(
            context,
            target=(
                f"{len(target_capture.face_indices)} faces / {len(target_capture.vertex_indices)} sommets "
                "— référence conservée"
            ),
            message=message,
            level=level,
        )
        self.report({report_level}, "Apply Relief terminé. Consultez le résultat détaillé dans Clone Relief.")
        return {"FINISHED"}


def _connected_face_components(
    bm: bmesh.types.BMesh,
) -> tuple[tuple[int, ...], ...]:
    """Return face-index groups connected by shared mesh edges, largest first."""
    bm.faces.index_update()
    unseen = set(bm.faces)
    components: list[tuple[int, ...]] = []
    while unseen:
        stack = [unseen.pop()]
        component: list[int] = []
        while stack:
            face = stack.pop()
            component.append(face.index)
            for edge in face.edges:
                for linked_face in edge.link_faces:
                    if linked_face in unseen:
                        unseen.remove(linked_face)
                        stack.append(linked_face)
        components.append(tuple(component))
    return tuple(sorted(components, key=len, reverse=True))


def _mesh_integrity_summary(obj: bpy.types.Object) -> dict[str, object]:
    """Collect inexpensive topology indicators without changing the mesh."""
    owns_bmesh = obj.mode != "EDIT"
    bm = bmesh.new() if owns_bmesh else bmesh.from_edit_mesh(obj.data)
    if owns_bmesh:
        bm.from_mesh(obj.data)
    try:
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        boundary_edges = sum(edge.is_boundary for edge in bm.edges)
        wire_edges = sum(edge.is_wire for edge in bm.edges)
        nonmanifold_edges = sum(
            not edge.is_manifold and not edge.is_boundary and not edge.is_wire
            for edge in bm.edges
        )
        nonmanifold_vertices = sum(not vertex.is_manifold for vertex in bm.verts)
        isolated_vertices = sum(not vertex.link_edges for vertex in bm.verts)
        degenerate_faces = sum(face.calc_area() <= 1e-18 for face in bm.faces)

        component_indices = _connected_face_components(bm)

        return {
            "vertices": len(bm.verts),
            "edges": len(bm.edges),
            "faces": len(bm.faces),
            "components": tuple(len(component) for component in component_indices),
            "boundary_edges": boundary_edges,
            "wire_edges": wire_edges,
            "nonmanifold_edges": nonmanifold_edges,
            "nonmanifold_vertices": nonmanifold_vertices,
            "isolated_vertices": isolated_vertices,
            "degenerate_faces": degenerate_faces,
        }
    finally:
        if owns_bmesh:
            bm.free()


class CLONERELIEF_OT_check_printability(bpy.types.Operator):
    """Report mesh continuity and manifold indicators without modifying it."""

    bl_idname = "clone_relief.check_printability"
    bl_label = "Check Mesh for 3D Printing"
    bl_description = "Report disconnected parts, open edges, non-manifold geometry, and degenerate faces"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.edit_object or context.active_object
        return obj is not None and obj.type == "MESH"

    def execute(self, context: bpy.types.Context) -> set[str]:
        obj = context.edit_object or context.active_object
        if obj is None or obj.type != "MESH":
            return {"CANCELLED"}
        try:
            report = _mesh_integrity_summary(obj)
        except (RuntimeError, ValueError) as error:
            _set_ui_status(context, message=f"Contrôle topologique impossible : {error}", level="ERROR")
            self.report({"ERROR"}, "Contrôle impossible. Consultez le panneau Clone Relief.")
            return {"CANCELLED"}

        components = report["components"]
        assert isinstance(components, tuple)
        component_text = ", ".join(f"{count:,}".replace(",", " ") for count in components[:5])
        if len(components) > 5:
            component_text += ", …"
        issues = any(
            report[key]
            for key in (
                "boundary_edges",
                "wire_edges",
                "nonmanifold_edges",
                "nonmanifold_vertices",
                "isolated_vertices",
                "degenerate_faces",
            )
        )
        level = "ERROR" if issues else "WARNING" if len(components) > 1 else "INFO"
        message = (
            f"Contrôle topologique — {obj.name} : "
            f"{report['vertices']:,} sommets, {report['edges']:,} arêtes, "
            f"{report['faces']:,} faces. ".replace(",", " ")
            + f"Composantes reliées par arêtes : {len(components)}"
            + (f" ({component_text} faces). " if component_text else ". ")
            + f"Bords : {report['boundary_edges']}; arêtes filaires : {report['wire_edges']}; "
            + f"arêtes non-manifold : {report['nonmanifold_edges']}; "
            + f"sommets non-manifold : {report['nonmanifold_vertices']}; "
            + f"sommets isolés : {report['isolated_vertices']}; "
            + f"faces dégénérées : {report['degenerate_faces']}. "
            + "Les auto-intersections et surfaces internes ne sont pas contrôlées."
        )
        if not issues and len(components) == 1:
            message = "Aucun défaut topologique détecté. " + message
        elif not issues:
            message = "Topologie des arêtes fermée; plusieurs composantes séparées à examiner. " + message
        _set_ui_status(context, message=message, level=level)
        self.report({level}, "Contrôle terminé. Consultez le panneau Clone Relief.")
        return {"FINISHED"}


class CLONERELIEF_OT_inspect_component(bpy.types.Operator):
    """Select and frame one disconnected face component for visual inspection."""

    bl_idname = "clone_relief.inspect_component"
    bl_label = "Locate Mesh Component"
    bl_description = "Select one disconnected component by face count and center the 3D view on it"

    component: EnumProperty(name="Composante", items=_component_inspection_items)

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.edit_object is not None and context.edit_object.type == "MESH"

    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event) -> set[str]:
        global _COMPONENT_INSPECTION_CACHE
        try:
            obj, bm = active_edit_mesh(context)
            components = _connected_face_components(bm)
            if len(components) < 2:
                self.report({"INFO"}, "Aucune composante séparée à localiser.")
                return {"CANCELLED"}
            signature = topology_signature(bm)
        except (ValueError, RuntimeError) as error:
            self.report({"ERROR"}, f"Localisation impossible : {error}")
            return {"CANCELLED"}

        _COMPONENT_INSPECTION_CACHE = (obj.as_pointer(), signature, components)
        _COMPONENT_INSPECTION_ITEMS[:] = [
            (
                str(index),
                f"Composante {index + 1} — {len(face_indices):,} faces".replace(",", " "),
                f"Sélectionner et cadrer {len(face_indices):,} faces reliées par des arêtes".replace(",", " "),
            )
            for index, face_indices in enumerate(components)
        ]
        self.component = "1"
        return context.window_manager.invoke_props_dialog(self, width=360)

    def draw(self, _context: bpy.types.Context) -> None:
        layout = self.layout
        layout.label(text="Choisis une composante; la vue sera cadrée sur sa sélection.")
        layout.prop(self, "component", text="")

    def execute(self, context: bpy.types.Context) -> set[str]:
        cache = _COMPONENT_INSPECTION_CACHE
        if cache is None:
            self.report({"ERROR"}, "Relance la localisation des composantes.")
            return {"CANCELLED"}
        try:
            obj, bm = active_edit_mesh(context)
            if obj.as_pointer() != cache[0] or topology_signature(bm) != cache[1]:
                raise ValueError("L’objet ou sa topologie a changé; relance le contrôle.")
            component_index = int(self.component)
            face_indices = cache[2][component_index]
            _select_face_indices(context, obj, bm, face_indices)
        except (IndexError, ValueError, RuntimeError) as error:
            self.report({"ERROR"}, f"Composante non sélectionnée : {error}")
            return {"CANCELLED"}

        framed = False
        screen = getattr(context, "screen", None)
        if screen is not None:
            area = context.area if context.area and context.area.type == "VIEW_3D" else next(
                (area for area in screen.areas if area.type == "VIEW_3D"),
                None,
            )
            region = next((region for region in area.regions if region.type == "WINDOW"), None) if area else None
            if area is not None and region is not None:
                try:
                    with context.temp_override(area=area, region=region):
                        framed = "FINISHED" in bpy.ops.view3d.view_selected(use_all_regions=False)
                except (RuntimeError, TypeError):
                    framed = False

        count = len(face_indices)
        message = (
            f"Composante {component_index + 1}/{len(cache[2])} sélectionnée : {count:,} faces. "
            .replace(",", " ")
            + ("Vue cadrée sur la composante. " if framed else "Sélection faite; centre la vue sur elle si nécessaire. ")
            + "Aucune géométrie n’a été modifiée."
        )
        _set_ui_status(context, message=message, level="INFO")
        self.report({"INFO"}, f"Composante sélectionnée : {count:,} faces.".replace(",", " "))
        return {"FINISHED"}


def _remove_comparison(context: bpy.types.Context) -> bool:
    """Remove generated comparison meshes and restore their source object."""
    collection = bpy.data.collections.get(_COMPARISON_COLLECTION_NAME)
    if collection is None:
        return False
    work_object = bpy.data.objects.get(str(collection.get("work_object", "")))
    was_hidden = bool(collection.get("work_was_hidden", False))
    work_mode = str(collection.get("work_mode", "OBJECT"))
    if work_object is not None:
        work_object.hide_set(was_hidden)
    for obj in tuple(collection.objects):
        if obj.get("clone_relief_comparison", False):
            mesh = obj.data if obj.type == "MESH" else None
            bpy.data.objects.remove(obj, do_unlink=True)
            if mesh is not None and mesh.users == 0:
                bpy.data.meshes.remove(mesh)
    if not collection.objects:
        bpy.data.collections.remove(collection)
    if work_object is not None and not was_hidden:
        work_object.select_set(True)
        context.view_layer.objects.active = work_object
        if work_mode != "OBJECT" and work_object.mode == "OBJECT":
            try:
                bpy.ops.object.mode_set(mode=work_mode)
            except RuntimeError:
                pass
    return True


class CLONERELIEF_OT_compare_target(bpy.types.Operator):
    """Show captured target baseline and current result as temporary meshes."""

    bl_idname = "clone_relief.compare_target"
    bl_label = "Compare Target Before and After"
    bl_description = "Create temporary side-by-side meshes from the captured target baseline and current result"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.edit_object is not None and context.edit_object.type == "MESH"

    def execute(self, context: bpy.types.Context) -> set[str]:
        if _TARGET_CAPTURE is None:
            self.report({"ERROR"}, "Capture Target before creating a comparison.")
            return {"CANCELLED"}
        try:
            obj, bm = active_edit_mesh(context)
            validate_capture(_TARGET_CAPTURE, obj, bm)
        except (ValueError, RuntimeError) as error:
            _set_ui_status(context, message=f"Comparaison impossible : {error}", level="ERROR")
            self.report({"ERROR"}, "Comparaison impossible. Consultez le panneau Clone Relief.")
            return {"CANCELLED"}

        if bpy.data.collections.get(_COMPARISON_COLLECTION_NAME) is not None:
            _remove_comparison(context)
            _set_ui_status(
                context,
                message="Comparaison précédente effacée. Relancez la commande pour la recréer.",
                level="INFO",
            )
            return {"FINISHED"}

        capture = _TARGET_CAPTURE
        world_matrix = obj.matrix_world
        after_vertices = tuple(
            tuple(float(value) for value in (world_matrix @ bm.verts[index].co))
            for index in capture.vertex_indices
        )
        before_vertices = capture.vertices_world
        differences = tuple(
            (Vector(after) - Vector(before)).length
            for before, after in zip(before_vertices, after_vertices)
        )
        moved = sum(value > 1e-12 for value in differences)
        if moved == 0:
            _set_ui_status(
                context,
                message="La cible correspond encore à sa référence; appliquez un relief avant de comparer.",
                level="WARNING",
            )
            self.report({"WARNING"}, "Aucun changement à comparer.")
            return {"CANCELLED"}

        bpy.ops.object.mode_set(mode="OBJECT")
        collection = bpy.data.collections.new(_COMPARISON_COLLECTION_NAME)
        context.scene.collection.children.link(collection)
        collection["work_object"] = obj.name
        collection["work_was_hidden"] = obj.hide_get()
        collection["work_mode"] = "EDIT"

        minimum = tuple(min(point[axis] for point in before_vertices) for axis in range(3))
        maximum = tuple(max(point[axis] for point in before_vertices) for axis in range(3))
        axis = max(range(3), key=lambda index: maximum[index] - minimum[index])
        span = max(maximum[axis] - minimum[axis], 1e-4)
        center = tuple((minimum[index] + maximum[index]) * 0.5 for index in range(3))
        offset = span * 1.5
        before_shift = tuple(-(offset if i == axis else 0.0) for i in range(3))
        after_shift = tuple(offset if i == axis else 0.0 for i in range(3))

        for name, points, shift in (
            ("Before - captured target", before_vertices, before_shift),
            ("After - current target", after_vertices, after_shift),
        ):
            mesh = bpy.data.meshes.new(f"{name} Mesh")
            mesh.from_pydata(
                [tuple(point[i] - center[i] + shift[i] for i in range(3)) for point in points],
                [],
                capture.faces,
            )
            mesh.update()
            comparison_obj = bpy.data.objects.new(name, mesh)
            collection.objects.link(comparison_obj)
            comparison_obj.location = center
            comparison_obj.hide_render = True
            comparison_obj["clone_relief_comparison"] = True

        obj.hide_set(True)
        bpy.ops.object.select_all(action="DESELECT")
        for name in ("Before - captured target", "After - current target"):
            bpy.data.objects[name].select_set(True)
        context.view_layer.objects.active = bpy.data.objects["After - current target"]
        magnitude = _format_displacement(context, max(differences, default=0.0))
        message = (
            f"Comparaison créée dans l’Outliner : Before - captured target et After - current target. "
            f"{moved}/{len(capture.vertex_indices)} sommets diffèrent; écart max. {magnitude}. "
            "Ces surfaces temporaires sont ouvertes et réservées à l’inspection; elles ne sont pas imprimables. "
            "Cliquez de nouveau sur la commande pour les effacer et revenir au maillage de travail."
        )
        _set_ui_status(context, message=message, level="INFO")
        self.report({"INFO"}, "Comparaison avant/après créée; détail dans Clone Relief.")
        return {"FINISHED"}


class CLONERELIEF_OT_clear_comparison(bpy.types.Operator):
    """Remove temporary before/after meshes and restore the work object."""

    bl_idname = "clone_relief.clear_comparison"
    bl_label = "Return to Work Mesh"
    bl_description = "Remove temporary comparison meshes and restore the working mesh"

    def execute(self, context: bpy.types.Context) -> set[str]:
        if not _remove_comparison(context):
            self.report({"INFO"}, "Aucune comparaison temporaire à effacer.")
            return {"CANCELLED"}
        _set_ui_status(context, message="Comparaison effacée; maillage de travail restauré.", level="INFO")
        return {"FINISHED"}


class CLONERELIEF_OT_export_stl(bpy.types.Operator):
    """Export only the active working mesh as a millimeter-scaled STL."""

    bl_idname = "clone_relief.export_stl"
    bl_label = "Export Working Mesh as STL"
    bl_description = "Export only the active mesh to STL in millimeters"

    filepath: StringProperty(subtype="FILE_PATH")
    filter_glob: StringProperty(default="*.stl", options={"HIDDEN"})

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.view_layer.objects.active
        return obj is not None and obj.type == "MESH" and not obj.get("clone_relief_comparison", False)

    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event) -> set[str]:
        obj = context.view_layer.objects.active
        if obj is None:
            return {"CANCELLED"}
        if not self.filepath:
            self.filepath = bpy.path.abspath(f"//{bpy.path.clean_name(obj.name)}.stl")
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        obj = context.view_layer.objects.active
        if obj is None or obj.type != "MESH" or obj.get("clone_relief_comparison", False):
            self.report({"ERROR"}, "Sélectionnez le maillage de travail, pas une surface de comparaison.")
            return {"CANCELLED"}
        previous_mode = obj.mode
        previous_active = context.view_layer.objects.active
        previous_selection = tuple(context.selected_objects)
        try:
            if obj.mode != "OBJECT":
                bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.object.select_all(action="DESELECT")
            obj.select_set(True)
            context.view_layer.objects.active = obj
            result = bpy.ops.wm.stl_export(
                filepath=self.filepath,
                check_existing=True,
                ascii_format=False,
                export_selected_objects=True,
                # STL has no unit metadata. Convert Blender units to mm using
                # the scene's meters-per-unit scale, without relying on the
                # scene display unit or applying the conversion twice.
                global_scale=1000.0 * context.scene.unit_settings.scale_length,
                use_scene_unit=False,
                forward_axis="Y",
                up_axis="Z",
                apply_modifiers=True,
            )
            if "FINISHED" not in result:
                raise RuntimeError("L’exporteur STL n’a pas terminé l’export.")
        except (RuntimeError, OSError) as error:
            _set_ui_status(context, message=f"Export STL échoué : {error}", level="ERROR")
            self.report({"ERROR"}, "Export STL échoué. Consultez le panneau Clone Relief.")
            return {"CANCELLED"}
        finally:
            if obj.mode != "OBJECT":
                bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.object.select_all(action="DESELECT")
            for selected_obj in previous_selection:
                if selected_obj.name in bpy.data.objects:
                    selected_obj.select_set(True)
            if previous_active is not None and previous_active.name in bpy.data.objects:
                context.view_layer.objects.active = previous_active
            if previous_mode != "OBJECT" and obj.name in bpy.data.objects and obj.select_get():
                context.view_layer.objects.active = obj
                try:
                    bpy.ops.object.mode_set(mode=previous_mode)
                except RuntimeError:
                    pass
        message = f"Export STL terminé en millimètres : {self.filepath}"
        _set_ui_status(context, message=message, level="INFO")
        self.report({"INFO"}, "Export STL terminé. Vérifiez les dimensions dans votre trancheur.")
        return {"FINISHED"}


class CLONERELIEF_OT_diagnose_resolution(bpy.types.Operator):
    """Compare captured target spacing with the source mesh spacing."""

    bl_idname = "clone_relief.diagnose_resolution"
    bl_label = "Diagnose Target Resolution"
    bl_description = "Compare source and target edge sizes and estimate useful local subdivision"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.edit_object is not None and context.edit_object.type == "MESH"

    def execute(self, context: bpy.types.Context) -> set[str]:
        try:
            _obj, _bm, _faces, _edges, _affected, resolution, _estimate = _subdivision_plan(context, 1)
        except (ValueError, RuntimeError, ArithmeticError) as error:
            _set_ui_status(context, message=f"Diagnostic impossible : {error}", level="ERROR")
            self.report({"ERROR"}, "Diagnostic impossible. Consultez le détail dans Clone Relief.")
            return {"CANCELLED"}
        ratio = resolution.p90_ratio
        source_edge = _format_displacement(context, resolution.source_median_edge)
        target_edge = _format_displacement(context, resolution.target_p90_edge)
        if resolution.needs_subdivision:
            message = (
                f"Cible trop grossière : arête cible P90 {target_edge}, contre "
                f"{source_edge} côté source ({ratio:.2f}×). Subdivision locale conseillée : "
                f"{resolution.recommended_cuts} coupe(s)."
            )
            level, report_level = "WARNING", "WARNING"
        else:
            message = (
                f"Résolution cible suffisante : arête P90 {target_edge}, contre "
                f"{source_edge} côté source ({ratio:.2f}×)."
            )
            level, report_level = "INFO", "INFO"
        self.report({report_level}, "Diagnostic terminé. Consultez le détail dans Clone Relief.")
        _set_ui_status(context, message=message, level=level)
        return {"FINISHED"}


class CLONERELIEF_OT_subdivide_target(bpy.types.Operator):
    """Show a cost estimate, then explicitly subdivide the captured target."""

    bl_idname = "clone_relief.subdivide_target"
    bl_label = "Densifier la cible capturée"
    bl_description = "Ajouter localement des faces à la cible après vérification de l’estimation"
    bl_options = {"REGISTER", "UNDO"}

    cuts: IntProperty(name="Cuts per Edge", default=1, min=1, max=8)
    max_added_faces: IntProperty(name="Maximum Added Faces", default=250000, min=1)

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.edit_object is not None and context.edit_object.type == "MESH"

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        try:
            plan = _subdivision_plan(context, self.cuts)
        except (ValueError, RuntimeError, ArithmeticError) as error:
            _set_ui_status(context, message=f"Subdivision annulée : {error}", level="ERROR")
            self.report({"ERROR"}, "Subdivision refusée. Consultez le détail dans Clone Relief.")
            return {"CANCELLED"}
        resolution = plan[5]
        self._resolution = resolution
        self._current_face_count = len(plan[1].faces)
        self._affected_face_sides = tuple(len(face.verts) for face in plan[4])
        if resolution.recommended_cuts:
            self.cuts = min(8, resolution.recommended_cuts)
        return context.window_manager.invoke_props_dialog(self, width=440)

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        resolution = getattr(self, "_resolution", None)
        current_face_count = getattr(self, "_current_face_count", None)
        affected_face_sides = getattr(self, "_affected_face_sides", None)
        if resolution is None or current_face_count is None or affected_face_sides is None:
            layout.label(text="Capture source and target, then reopen this dialog", icon="ERROR")
            return
        estimated_faces = estimate_face_count_upper_bound(
            current_face_count,
            affected_face_sides,
            self.cuts,
        )
        added = max(0, estimated_faces - current_face_count)
        layout.label(text=f"Source median edge: {resolution.source_median_edge:.6g} scene units")
        layout.label(text=f"Target P90 edge: {resolution.target_p90_edge:.6g} ({resolution.p90_ratio:.2f}x source)")
        layout.label(text=f"Selected target: {len(_TARGET_CAPTURE.face_indices)} faces on {_TARGET_CAPTURE.object_name}")
        layout.prop(self, "cuts")
        layout.prop(self, "max_added_faces")
        layout.label(text=f"Estimated upper bound: {estimated_faces:,} total faces (+{added:,})")
        if added > self.max_added_faces:
            layout.label(text="Estimate exceeds the added-face limit", icon="ERROR")
        elif not resolution.needs_subdivision:
            layout.label(text="Target is already near source spacing", icon="INFO")

    def execute(self, context: bpy.types.Context) -> set[str]:
        global _SOURCE_CAPTURE, _TARGET_CAPTURE
        try:
            obj, bm, target_faces, edges, affected_faces, resolution, estimated_faces = _subdivision_plan(
                context,
                self.cuts,
            )
            added_estimate = max(0, estimated_faces - len(bm.faces))
            if added_estimate > self.max_added_faces:
                raise ValueError(
                    f"Conservative estimate adds {added_estimate:,} faces; "
                    f"limit is {self.max_added_faces:,}"
                )
            before_faces = len(bm.faces)
            subdivision_result = bmesh.ops.subdivide_edges(
                bm,
                edges=list(edges),
                cuts=self.cuts,
                smooth=0.0,
                fractal=0.0,
                along_normal=0.0,
                use_grid_fill=True,
            )
            bm.verts.ensure_lookup_table()
            bm.edges.ensure_lookup_table()
            bm.faces.ensure_lookup_table()
            bmesh.update_edit_mesh(obj.data, loop_triangles=True, destructive=True)
        except (ValueError, RuntimeError, ArithmeticError) as error:
            _set_ui_status(context, message=f"Subdivision refusée : {error}", level="ERROR")
            self.report({"ERROR"}, "Subdivision refusée. Consultez le détail dans Clone Relief.")
            return {"CANCELLED"}

        _SOURCE_CAPTURE = None
        _TARGET_CAPTURE = None
        actual_added = len(bm.faces) - before_faces
        _set_ui_status(
            context,
            source="Recapture after subdivision",
            target="Recapture after subdivision",
            message=f"Subdivision réussie : {actual_added} faces ajoutées. Recapturez source et cible.",
            level="WARNING",
        )
        self.report({"INFO"}, "Subdivision terminée. Recapturez source et cible; détail dans Clone Relief.")
        return {"FINISHED"}


_CLASSES: tuple[type[bpy.types.Operator], ...] = (
    CLONERELIEF_OT_preview,
    CLONERELIEF_OT_copy_message,
    CLONERELIEF_OT_capture_source,
    CLONERELIEF_OT_capture_target,
    CLONERELIEF_OT_restore_source_selection,
    CLONERELIEF_OT_restore_target_selection,
    CLONERELIEF_OT_apply,
    CLONERELIEF_OT_check_printability,
    CLONERELIEF_OT_inspect_component,
    CLONERELIEF_OT_compare_target,
    CLONERELIEF_OT_clear_comparison,
    CLONERELIEF_OT_export_stl,
    CLONERELIEF_OT_diagnose_resolution,
    CLONERELIEF_OT_subdivide_target,
)


def register() -> None:
    """Register the minimal Clone Relief operator set."""
    for operator_class in _CLASSES:
        if not _operator_is_registered(operator_class):
            bpy.utils.register_class(operator_class)
    if _prepare_after_file_load not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_prepare_after_file_load)
    prepare_capture_view(bpy.context)


def unregister() -> None:
    """Unregister Clone Relief operators in reverse order."""
    if _prepare_after_file_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_prepare_after_file_load)
    for operator_class in reversed(_CLASSES):
        if _operator_is_registered(operator_class):
            try:
                bpy.utils.unregister_class(operator_class)
            except RuntimeError:
                # The class may already have been unregistered during a reload.
                pass
