"""Exercise Clone Relief capture, apply, and undo in Blender 4.5.8."""

from __future__ import annotations

import json
import math
import sys
from textwrap import wrap
from pathlib import Path

import bmesh
import bpy


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import clone_relief  # noqa: E402
from clone_relief import operators as relief_operators  # noqa: E402
from clone_relief.blender_adapter import (
    active_edit_mesh,
    capture_selection,
    topology_signature,
    validate_capture,
)  # noqa: E402


def _synthetic_mesh() -> tuple[bpy.types.Object, tuple[int, ...], tuple[int, ...]]:
    steps = 16
    extent = 1.0
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int, int]] = []
    source_face_indices: list[int] = []
    target_face_indices: list[int] = []
    patch_vertex_count = (steps + 1) * (steps + 1)

    for center_x, source in ((-2.5, True), (2.5, False)):
        start = len(vertices)
        for y_index in range(steps + 1):
            y = -extent + 2.0 * extent * y_index / steps
            for x_index in range(steps + 1):
                x = -extent + 2.0 * extent * x_index / steps
                z = 0.15 * math.sin(2.0 * math.pi * y / 0.5) if source else 0.0
                vertices.append((center_x + x, y, z))
        for y_index in range(steps):
            for x_index in range(steps):
                face = (
                    start + y_index * (steps + 1) + x_index,
                    start + y_index * (steps + 1) + x_index + 1,
                    start + (y_index + 1) * (steps + 1) + x_index + 1,
                    start + (y_index + 1) * (steps + 1) + x_index,
                )
                face_parts = (face,) if source else (
                    (face[0], face[1], face[2]),
                    (face[0], face[2], face[3]),
                )
                destination = source_face_indices if source else target_face_indices
                for face_part in face_parts:
                    if source or (
                        steps // 4 <= x_index < 3 * steps // 4
                        and steps // 4 <= y_index < 3 * steps // 4
                    ):
                        destination.append(len(faces))
                    faces.append(face_part)

    assert len(vertices) == patch_vertex_count * 2
    mesh = bpy.data.meshes.new("CloneReliefSyntheticMesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("CloneReliefSynthetic", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    return obj, tuple(source_face_indices), tuple(target_face_indices)


def _selected_faces(face_indices: tuple[int, ...]) -> None:
    bm = bmesh.from_edit_mesh(bpy.context.edit_object.data)
    bm.faces.ensure_lookup_table()
    bm.faces.index_update()
    for face in bm.faces:
        face.select_set(False)
    for index in face_indices:
        bm.faces[index].select_set(True)
    bmesh.update_edit_mesh(bpy.context.edit_object.data, loop_triangles=False, destructive=False)


def _positions(obj: bpy.types.Object) -> tuple[tuple[float, float, float], ...]:
    if obj.mode == "EDIT":
        bm = bmesh.from_edit_mesh(obj.data)
        bm.verts.index_update()
        bm.verts.ensure_lookup_table()
        return tuple(tuple(float(component) for component in vertex.co) for vertex in bm.verts)
    return tuple(tuple(float(component) for component in vertex.co) for vertex in obj.data.vertices)


def main() -> None:
    if bpy.app.version[:3] != (4, 5, 8):
        raise AssertionError(f"Expected Blender 4.5.8; got {bpy.app.version_string}")

    obj, source_faces, target_faces = _synthetic_mesh()
    target_vertex_indices = {vertex for face_index in target_faces for vertex in obj.data.polygons[face_index].vertices}
    source_vertex_indices = {vertex for face_index in source_faces for vertex in obj.data.polygons[face_index].vertices}

    view_area = next(
        (area for area in bpy.context.screen.areas if area.type == "VIEW_3D"),
        None,
    ) if bpy.context.screen else None
    if view_area is not None:
        view_area.spaces.active.shading.type = "WIREFRAME"
        view_area.spaces.active.shading.show_xray = True
    bpy.context.tool_settings.mesh_select_mode = (True, False, False)
    clone_relief.register()
    if view_area is not None and (
        view_area.spaces.active.shading.type != "SOLID"
        or view_area.spaces.active.shading.show_xray
    ):
        raise AssertionError("Addon registration did not prepare a visible-surface view")
    if tuple(bpy.context.tool_settings.mesh_select_mode) != (False, False, True):
        raise AssertionError("Addon registration did not enable face selection mode")
    settings = bpy.context.scene.clone_relief_settings
    if not math.isclose(settings.intensity, 1.0, abs_tol=1e-6) or not math.isclose(settings.scale, 1.0):
        raise AssertionError("Sidebar transfer settings have unexpected defaults")
    if not math.isclose(settings.falloff_fraction, 0.25):
        raise AssertionError("Sidebar falloff default is incorrect")
    if settings.relief_direction != "OUTWARD":
        raise AssertionError("Unidirectional outward transfer is not the default")
    if not hasattr(bpy.types, "CLONERELIEF_PT_sidebar"):
        raise AssertionError("Clone Relief sidebar panel was not registered")
    bpy.ops.object.mode_set(mode="EDIT")
    _selected_faces(source_faces)
    assert "FINISHED" in bpy.ops.clone_relief.capture_source()
    if not settings.source_status.startswith("256 faces / 289 sommets"):
        raise AssertionError("Source capture did not update sidebar status")
    _selected_faces((*source_faces, target_faces[0]))
    assert "FINISHED" in bpy.ops.clone_relief.capture_source()
    if relief_operators._SOURCE_CAPTURE.ignored_component_sizes != (1,):
        raise AssertionError("A small disconnected selection group was not reported")
    if len(relief_operators._SOURCE_CAPTURE.face_indices) != len(source_faces):
        raise AssertionError("Dominant source group was not captured by itself")
    valid_source_capture = relief_operators._SOURCE_CAPTURE
    _selected_faces((source_faces[0], source_faces[-1]))
    try:
        rejected_source = bpy.ops.clone_relief.capture_source()
    except RuntimeError as error:
        if "Capture Source refusée" not in str(error):
            raise
    else:
        if "CANCELLED" not in rejected_source:
            raise AssertionError("Disconnected source selection was accepted")
    if relief_operators._SOURCE_CAPTURE is not valid_source_capture:
        raise AssertionError("Failed source recapture discarded the valid capture")
    if "2 groupes" not in settings.last_message:
        raise AssertionError("Disconnected source error did not explain the component count")
    _selected_faces(source_faces)

    stale_capture = capture_selection(bpy.context, role="source")
    bm = bmesh.from_edit_mesh(obj.data)
    bm.verts.new((9.0, 9.0, 9.0))
    bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=True)
    current_obj, current_bm = active_edit_mesh(bpy.context)
    try:
        validate_capture(stale_capture, current_obj, current_bm)
    except ValueError as error:
        if "topology changed" not in str(error):
            raise
    else:
        raise AssertionError("Topology changes did not invalidate the source capture")

    _selected_faces(source_faces)
    assert "FINISHED" in bpy.ops.clone_relief.capture_source()
    _selected_faces(target_faces)
    assert "FINISHED" in bpy.ops.clone_relief.capture_target()
    if not settings.target_status.startswith("128 faces / 81 sommets"):
        raise AssertionError("Target capture did not update sidebar status")
    _selected_faces((*target_faces, source_faces[0]))
    assert "FINISHED" in bpy.ops.clone_relief.capture_target()
    if relief_operators._TARGET_CAPTURE.ignored_component_sizes != (1,):
        raise AssertionError("A small disconnected target group was not reported")
    if len(relief_operators._TARGET_CAPTURE.face_indices) != len(target_faces):
        raise AssertionError("Dominant target group was not captured by itself")
    valid_target_capture = relief_operators._TARGET_CAPTURE
    _selected_faces((target_faces[0], target_faces[-1]))
    try:
        rejected_target = bpy.ops.clone_relief.capture_target()
    except RuntimeError as error:
        if "Capture Target refusée" not in str(error):
            raise
    else:
        if "CANCELLED" not in rejected_target:
            raise AssertionError("Disconnected target selection was accepted")
    if relief_operators._TARGET_CAPTURE is not valid_target_capture:
        raise AssertionError("Failed target recapture discarded the valid capture")
    _selected_faces(target_faces)
    before = _positions(obj)
    assert "FINISHED" in bpy.ops.clone_relief.preview("EXEC_DEFAULT", True)
    if _positions(obj) != before:
        raise AssertionError("Preview changed mesh coordinates")
    if not settings.last_message.startswith("Aperçu"):
        raise AssertionError("Preview did not report its estimated effect")
    expected_lines = wrap(settings.last_message, width=42, break_long_words=False, break_on_hyphens=False)
    if [line.text for line in settings.message_lines] != expected_lines:
        raise AssertionError("Detailed message lines were not populated for selection and copy")
    assert "FINISHED" in bpy.ops.clone_relief.copy_message()
    if not bpy.app.background and bpy.context.window_manager.clipboard != settings.last_message:
        raise AssertionError("Copy Message did not place the full message on the clipboard")
    bpy.ops.ed.undo_push(message="Before Clone Relief Apply")
    assert "FINISHED" in bpy.ops.clone_relief.apply("EXEC_DEFAULT", True)
    if not settings.target_status.startswith("128 faces / 81 sommets"):
        raise AssertionError("Apply did not preserve the captured target baseline")
    if "sommets" not in settings.last_message or "déplacement max." not in settings.last_message:
        raise AssertionError("Apply did not report moved vertices and displacement")
    after_apply = _positions(obj)

    moved_target = [
        index
        for index in target_vertex_indices
        if math.dist(after_apply[index], before[index]) > 1e-12
    ]
    if not moved_target:
        raise AssertionError("Apply did not displace any target vertices")
    if any(after_apply[index][2] < before[index][2] - 1e-12 for index in target_vertex_indices):
        raise AssertionError("Default unidirectional transfer moved target vertices inward")
    if any(after_apply[index] != before[index] for index in source_vertex_indices):
        raise AssertionError("Apply changed source vertices")
    if any(
        after_apply[index] != before[index]
        for index in range(len(before))
        if index not in target_vertex_indices
    ):
        raise AssertionError("Apply changed vertices outside the target selection")

    bpy.ops.ed.undo()
    after_undo = _positions(obj)
    if after_undo != before:
        mismatches = [
            (index, before[index], after_undo[index])
            for index in range(min(len(before), len(after_undo)))
            if after_undo[index] != before[index]
        ]
        raise AssertionError(
            f"Undo did not restore exact coordinates: mode={obj.mode}, "
            f"mismatches={len(mismatches)}, first={mismatches[:3]}"
        )

    # M3: diagnose the captured regions and explicitly subdivide only the target.
    _selected_faces(source_faces)
    assert "FINISHED" in bpy.ops.clone_relief.capture_source()
    _selected_faces(target_faces)
    assert "FINISHED" in bpy.ops.clone_relief.capture_target()
    assert "FINISHED" in bpy.ops.clone_relief.diagnose_resolution()
    bm = bmesh.from_edit_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    selected_target_faces = {bm.faces[face_index] for face_index in target_faces}
    target_edges = {edge for face in selected_target_faces for edge in face.edges}
    target_boundary_coordinates = {
        tuple(float(component) for component in vertex.co)
        for edge in target_edges
        if edge.is_boundary or any(face not in selected_target_faces for face in edge.link_faces)
        for vertex in edge.verts
    }
    subdivision_before = _positions(obj)
    faces_before_subdivision = len(bm.faces)
    edges_before_subdivision = len(bm.edges)
    topology_before_subdivision = topology_signature(bm)
    boundary_edges_before = sum(edge.is_boundary for edge in bm.edges)
    try:
        rejected = bpy.ops.clone_relief.subdivide_target(
            "EXEC_DEFAULT",
            True,
            cuts=1,
            max_added_faces=1,
        )
    except RuntimeError as error:
        if "Subdivision refusée" not in str(error):
            raise
        if "Conservative estimate adds 480 faces" not in settings.last_message:
            raise AssertionError("Sidebar did not retain the detailed subdivision error")
    else:
        if "CANCELLED" not in rejected:
            raise AssertionError("Subdivision ignored the added-face safety limit")
    if topology_signature(bmesh.from_edit_mesh(obj.data)) != topology_before_subdivision:
        raise AssertionError("Rejected subdivision changed topology")
    bpy.ops.ed.undo_push(message="Before Clone Relief Subdivision")
    assert "FINISHED" in bpy.ops.clone_relief.subdivide_target(
        "EXEC_DEFAULT",
        True,
        cuts=1,
        max_added_faces=250000,
    )
    if settings.source_status != "Recapture after subdivision":
        raise AssertionError("Subdivision did not invalidate the sidebar capture status")
    after_subdivision = _positions(obj)
    bm = bmesh.from_edit_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    faces_after_subdivision = len(bm.faces)
    if len(bm.faces) <= faces_before_subdivision:
        raise AssertionError("Target subdivision did not add faces")
    if sum(edge.is_boundary for edge in bm.edges) != boundary_edges_before:
        raise AssertionError("Subdivision changed the mesh's open-boundary edge count")
    if not target_boundary_coordinates.issubset(set(after_subdivision)):
        raise AssertionError("Subdivision moved an original target boundary vertex")
    if any(after_subdivision[index] != subdivision_before[index] for index in source_vertex_indices):
        raise AssertionError("Subdivision changed source vertex coordinates")
    if "FINISHED" not in bpy.ops.ed.undo():
        raise AssertionError("Undo after subdivision did not finish")
    after_subdivision_undo = _positions(obj)
    if after_subdivision_undo != subdivision_before:
        raise AssertionError("Undo did not restore the pre-subdivision mesh exactly")
    bm = bmesh.from_edit_mesh(obj.data)
    if len(bm.faces) != faces_before_subdivision or len(bm.edges) != edges_before_subdivision:
        raise AssertionError("Undo did not restore the pre-subdivision topology counts")
    if topology_signature(bm) != topology_before_subdivision:
        raise AssertionError("Undo did not restore the pre-subdivision topology signature")

    print(
        "CLONE_RELIEF_SMOKE_OK "
        + json.dumps(
            {
                "blender": bpy.app.version_string,
                "source_faces": len(source_faces),
                "target_faces": len(target_faces),
                "moved_target_vertices": len(moved_target),
                "outside_target_unchanged": True,
                "undo_restored_exact_coordinates": True,
                "subdivision_added_faces": faces_after_subdivision - faces_before_subdivision,
                "subdivision_preserved_boundary_vertices": True,
                "subdivision_undo_restored_exact_mesh": True,
            },
            sort_keys=True,
        )
    )
    if obj.mode == "EDIT":
        bpy.ops.object.mode_set(mode="OBJECT")
    clone_relief.unregister()
    mesh = obj.data
    bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.meshes.remove(mesh)


main()
