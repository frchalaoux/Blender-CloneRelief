"""Minimal Blender operators for source/target capture and relief application."""

import bpy
import bmesh
from bpy.app.handlers import persistent
from bpy.props import EnumProperty, FloatProperty, IntProperty
from mathutils import Vector
from textwrap import wrap

from .density import ResolutionReport, analyze_resolution, estimate_face_count_upper_bound
from .blender_adapter import (
    CapturedSelection,
    active_edit_mesh,
    capture_selection,
    current_patch,
    prepare_capture_view,
    topology_signature,
    validate_capture,
    write_world_coordinates,
)
from .relief import apply_relief, extract_relief

_SOURCE_CAPTURE: CapturedSelection | None = None
_TARGET_CAPTURE: CapturedSelection | None = None


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
    area = context.area if context.area and context.area.type == "VIEW_3D" else None
    if area is None and context.screen is not None:
        area = next((item for item in context.screen.areas if item.type == "VIEW_3D"), None)
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
    target = current_patch(_TARGET_CAPTURE, obj, bm)
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
    target_patch = current_patch(_TARGET_CAPTURE, obj, bm)
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
    bl_description = "Store the selected connected face region as the relief target"

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


class CLONERELIEF_OT_apply(bpy.types.Operator):
    """Apply captured source relief to the captured target in one undo step."""

    bl_idname = "clone_relief.apply"
    bl_label = "Apply Clone Relief"
    bl_description = "Transfer captured source microrelief to the captured target"
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
        global _TARGET_CAPTURE
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
        _TARGET_CAPTURE = None
        magnitude = _format_displacement(context, maximum)
        warning_threshold = _visibility_threshold(context)
        if moved == 0:
            message = "Aucun sommet déplacé : aucune modification géométrique. Vérifiez les captures."
            level, report_level = "WARNING", "WARNING"
        elif maximum < warning_threshold:
            message = (
                f"Relief appliqué, mais très faible : {moved}/{len(target_capture.vertex_indices)} "
                f"sommets; déplacement max. {magnitude}; mode {_direction_label(self.direction)}. "
                "Choisissez une source plus texturée, "
                "augmentez Relief Gain ou densifiez si le diagnostic le recommande. "
                "Pour remplacer cet essai, faites Undo puis recapturez la cible."
            )
            level, report_level = "WARNING", "WARNING"
        else:
            message = (
                f"Réussite : relief appliqué à {moved}/{len(target_capture.vertex_indices)} sommets; "
                f"déplacement max. {magnitude}; mode {_direction_label(self.direction)}. Annuler avec Undo."
            )
            level, report_level = "INFO", "INFO"
        _set_ui_status(
            context,
            target="À recapturer avant une nouvelle application",
            message=message,
            level=level,
        )
        self.report({report_level}, "Apply Relief terminé. Consultez le résultat détaillé dans Clone Relief.")
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
    CLONERELIEF_OT_apply,
    CLONERELIEF_OT_diagnose_resolution,
    CLONERELIEF_OT_subdivide_target,
)


def register() -> None:
    """Register the minimal Clone Relief operator set."""
    for operator_class in _CLASSES:
        bpy.utils.register_class(operator_class)
    if _prepare_after_file_load not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_prepare_after_file_load)
    prepare_capture_view(bpy.context)


def unregister() -> None:
    """Unregister Clone Relief operators in reverse order."""
    if _prepare_after_file_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_prepare_after_file_load)
    for operator_class in reversed(_CLASSES):
        try:
            bpy.utils.unregister_class(operator_class)
        except RuntimeError:
            # The class may already have been unregistered during a reload.
            pass
