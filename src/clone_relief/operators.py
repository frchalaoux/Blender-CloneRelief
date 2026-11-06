"""Minimal Blender operators for source/target capture and relief application."""

import bpy
import bmesh
from bpy.props import FloatProperty, IntProperty
from mathutils import Vector

from .density import ResolutionReport, analyze_resolution, estimate_face_count_upper_bound
from .blender_adapter import (
    CapturedSelection,
    active_edit_mesh,
    capture_selection,
    current_patch,
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
        _SOURCE_CAPTURE = None
        _TARGET_CAPTURE = None
        _set_ui_status(context, source="Not captured", target="Not captured", message="")
        try:
            _SOURCE_CAPTURE = capture_selection(context, role="source")
        except (ValueError, RuntimeError) as error:
            _set_ui_status(context, source=f"Failed: {error}")
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}
        source_status = f"{len(_SOURCE_CAPTURE.face_indices)} faces / {len(_SOURCE_CAPTURE.vertex_indices)} vertices"
        _set_ui_status(context, source=source_status, message="Source captured")
        self.report(
            {"INFO"},
            f"Source captured: {len(_SOURCE_CAPTURE.face_indices)} faces, {len(_SOURCE_CAPTURE.vertex_indices)} vertices",
        )
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
        _TARGET_CAPTURE = None
        if _SOURCE_CAPTURE is None:
            _set_ui_status(context, target="Not captured", message="Capture a source region first")
            self.report({"ERROR"}, "Capture a source region first")
            return {"CANCELLED"}
        try:
            capture = capture_selection(context, role="target")
            obj, bm = active_edit_mesh(context)
            validate_capture(_SOURCE_CAPTURE, obj, bm, current_signature=capture.topology_signature)
            if set(capture.face_indices).intersection(_SOURCE_CAPTURE.face_indices):
                raise ValueError("Source and target face selections must not overlap")
            _TARGET_CAPTURE = capture
        except (ValueError, RuntimeError) as error:
            _set_ui_status(context, target=f"Failed: {error}", message=str(error))
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}
        target_status = f"{len(capture.face_indices)} faces / {len(capture.vertex_indices)} vertices"
        _set_ui_status(context, target=target_status, message="Target captured")
        self.report(
            {"INFO"},
            f"Target captured: {len(capture.face_indices)} faces, {len(capture.vertex_indices)} vertices",
        )
        return {"FINISHED"}


class CLONERELIEF_OT_apply(bpy.types.Operator):
    """Apply captured source relief to the captured target in one undo step."""

    bl_idname = "clone_relief.apply"
    bl_label = "Apply Clone Relief"
    bl_description = "Transfer captured source microrelief to the captured target"
    bl_options = {"REGISTER", "UNDO"}

    intensity: FloatProperty(name="Intensity", default=0.60, min=0.0, max=1.0)
    scale: FloatProperty(name="Pattern Scale", default=1.0, min=0.001, soft_max=4.0)
    falloff_fraction: FloatProperty(name="Edge Falloff", default=0.25, min=0.001, max=1.0)
    max_displacement: FloatProperty(name="Maximum Displacement", default=0.0, min=0.0, soft_max=0.1)

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.edit_object is not None and context.edit_object.type == "MESH"

    def execute(self, context: bpy.types.Context) -> set[str]:
        global _TARGET_CAPTURE
        if _SOURCE_CAPTURE is None or _TARGET_CAPTURE is None:
            _set_ui_status(context, message="Capture both source and target regions first")
            self.report({"ERROR"}, "Capture both source and target regions first")
            return {"CANCELLED"}
        try:
            obj, bm = active_edit_mesh(context)
            signature = topology_signature(bm)
            validate_capture(_SOURCE_CAPTURE, obj, bm, current_signature=signature)
            validate_capture(_TARGET_CAPTURE, obj, bm, current_signature=signature)
            if set(_SOURCE_CAPTURE.face_indices).intersection(_TARGET_CAPTURE.face_indices):
                raise ValueError("Source and target face selections overlap; recapture the target")

            source = _SOURCE_CAPTURE.as_patch()
            target = current_patch(_TARGET_CAPTURE, obj, bm)
            field, _ = extract_relief(source)
            updated = apply_relief(
                field,
                target,
                intensity=self.intensity,
                scale=self.scale,
                falloff_fraction=self.falloff_fraction,
                max_displacement=self.max_displacement if self.max_displacement > 0.0 else None,
            )
            moved = sum(
                1
                for original, result in zip(target.vertices, updated)
                if (Vector(result) - Vector(original)).length > 1e-12
            )
            maximum = max(
                ((Vector(result) - Vector(original)).length for original, result in zip(target.vertices, updated)),
                default=0.0,
            )
            write_world_coordinates(obj, bm, _TARGET_CAPTURE.vertex_indices, updated)
        except (ValueError, RuntimeError, ArithmeticError) as error:
            _set_ui_status(context, message=str(error))
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}

        _TARGET_CAPTURE = None
        _set_ui_status(context, target="Not captured", message=f"Relief applied to {moved} vertices")
        self.report(
            {"INFO"},
            f"Relief applied: {moved} vertices moved, maximum displacement {maximum:.6g} scene units",
        )
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
            _set_ui_status(context, message=str(error))
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}
        ratio = resolution.p90_ratio
        message = (
            f"Source median edge {resolution.source_median_edge:.6g}; "
            f"target P90 {resolution.target_p90_edge:.6g} ({ratio:.2f}x); "
            f"recommended cuts: {resolution.recommended_cuts}"
        )
        self.report({"WARNING" if resolution.needs_subdivision else "INFO"}, message)
        _set_ui_status(context, message=message)
        return {"FINISHED"}


class CLONERELIEF_OT_subdivide_target(bpy.types.Operator):
    """Show a cost estimate, then explicitly subdivide the captured target."""

    bl_idname = "clone_relief.subdivide_target"
    bl_label = "Subdivide Captured Target"
    bl_description = "Locally subdivide target edges after reviewing the face-count estimate"
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
            _set_ui_status(context, message=str(error))
            self.report({"ERROR"}, str(error))
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
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}

        _SOURCE_CAPTURE = None
        _TARGET_CAPTURE = None
        actual_added = len(bm.faces) - before_faces
        _set_ui_status(
            context,
            source="Recapture after subdivision",
            target="Recapture after subdivision",
            message=f"Subdivision added {actual_added} faces; capture again",
        )
        self.report(
            {"INFO"},
            f"Target subdivided with {self.cuts} cut(s): {actual_added:,} faces added "
            f"(upper estimate +{added_estimate:,}; {len(edges):,} edges processed; "
            f"{len(subdivision_result.get('geom_inner', ())):,} inner elements; "
            f"source/target captures cleared)",
        )
        return {"FINISHED"}


_CLASSES: tuple[type[bpy.types.Operator], ...] = (
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


def unregister() -> None:
    """Unregister Clone Relief operators in reverse order."""
    for operator_class in reversed(_CLASSES):
        try:
            bpy.utils.unregister_class(operator_class)
        except RuntimeError:
            # The class may already have been unregistered during a reload.
            pass
