"""BMesh-to-core conversion and topology-safe selection snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import blake2b
from struct import pack

import bmesh
import bpy
from mathutils import Vector

from .geometry import Face, MeshPatch, Vec3


@dataclass(frozen=True, slots=True)
class CapturedSelection:
    """Immutable compact selection snapshot tied to one mesh topology."""

    object_pointer: int
    object_name: str
    topology_signature: str
    vertex_indices: tuple[int, ...]
    face_indices: tuple[int, ...]
    faces: tuple[Face, ...]
    vertices_world: tuple[Vec3, ...]

    def as_patch(self) -> MeshPatch:
        """Return the captured world-space geometry as a pure mesh patch."""
        return MeshPatch(self.vertices_world, self.faces)


def active_edit_mesh(context: bpy.types.Context) -> tuple[bpy.types.Object, bmesh.types.BMesh]:
    """Return the active edit-mode mesh and its live BMesh or raise clearly."""
    obj = context.edit_object
    if obj is None or obj.type != "MESH" or obj.mode != "EDIT":
        raise ValueError("Select a mesh object and enter Edit Mode first")
    bm = bmesh.from_edit_mesh(obj.data)
    bm.verts.index_update()
    bm.edges.index_update()
    bm.faces.index_update()
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    return obj, bm


def topology_signature(bm: bmesh.types.BMesh) -> str:
    """Hash vertex/edge/face connectivity without copying the full mesh."""
    digest = blake2b(digest_size=20)
    digest.update(pack("<QQQ", len(bm.verts), len(bm.edges), len(bm.faces)))
    for edge in bm.edges:
        first, second = sorted((edge.verts[0].index, edge.verts[1].index))
        digest.update(pack("<II", first, second))
    for face in bm.faces:
        cycle = tuple(vertex.index for vertex in face.verts)
        canonical = min(cycle[index:] + cycle[:index] for index in range(len(cycle)))
        digest.update(pack("<I", len(canonical)))
        digest.update(pack(f"<{len(canonical)}I", *canonical))
    return digest.hexdigest()


def _assert_one_connected_component(faces: tuple[bmesh.types.BMFace, ...]) -> None:
    """Reject face selections connected only by separate islands."""
    remaining = set(faces)
    components = 0
    while remaining:
        components += 1
        if components > 1:
            raise ValueError("Selection must be one edge-connected region")
        stack = [remaining.pop()]
        while stack:
            face = stack.pop()
            for edge in face.edges:
                for neighbor in edge.link_faces:
                    if neighbor in remaining:
                        remaining.remove(neighbor)
                        stack.append(neighbor)


def capture_selection(
    context: bpy.types.Context,
    *,
    role: str,
) -> CapturedSelection:
    """Capture selected faces into a compact world-space snapshot."""
    if role not in {"source", "target"}:
        raise ValueError("role must be 'source' or 'target'")
    obj, bm = active_edit_mesh(context)
    selected_faces = tuple(sorted((face for face in bm.faces if face.select), key=lambda face: face.index))
    if not selected_faces:
        raise ValueError(f"No faces selected for {role}")
    _assert_one_connected_component(selected_faces)

    vertex_indices = tuple(sorted({vertex.index for face in selected_faces for vertex in face.verts}))
    local_index = {mesh_index: local for local, mesh_index in enumerate(vertex_indices)}
    local_faces = tuple(
        tuple(local_index[vertex.index] for vertex in face.verts)
        for face in selected_faces
    )
    world_matrix = obj.matrix_world
    vertices_world = tuple(
        tuple(float(value) for value in (world_matrix @ bm.verts[index].co))
        for index in vertex_indices
    )
    return CapturedSelection(
        object_pointer=obj.as_pointer(),
        object_name=obj.name,
        topology_signature=topology_signature(bm),
        vertex_indices=vertex_indices,
        face_indices=tuple(face.index for face in selected_faces),
        faces=local_faces,
        vertices_world=vertices_world,  # type: ignore[arg-type]
    )


def validate_capture(
    capture: CapturedSelection,
    obj: bpy.types.Object,
    bm: bmesh.types.BMesh,
    *,
    current_signature: str | None = None,
) -> None:
    """Ensure the selection still belongs to the same unchanged mesh topology."""
    if obj.as_pointer() != capture.object_pointer:
        raise ValueError(f"Captured {capture.object_name} data; return to that object")
    signature = current_signature if current_signature is not None else topology_signature(bm)
    if signature != capture.topology_signature:
        raise ValueError("Mesh topology changed after capture; capture source and target again")
    if any(index >= len(bm.verts) for index in capture.vertex_indices):
        raise ValueError("Captured vertex indices are no longer valid; capture again")


def current_patch(
    capture: CapturedSelection,
    obj: bpy.types.Object,
    bm: bmesh.types.BMesh,
) -> MeshPatch:
    """Build a patch from current vertex positions and captured connectivity."""
    if abs(obj.matrix_world.to_3x3().determinant()) <= 1e-15:
        raise ValueError("Object has a singular transform; apply or correct its scale first")
    world_matrix = obj.matrix_world
    coordinates = tuple(
        tuple(float(value) for value in (world_matrix @ bm.verts[index].co))
        for index in capture.vertex_indices
    )
    return MeshPatch(coordinates, capture.faces)  # type: ignore[arg-type]


def write_world_coordinates(
    obj: bpy.types.Object,
    bm: bmesh.types.BMesh,
    vertex_indices: tuple[int, ...],
    coordinates: tuple[Vec3, ...],
) -> None:
    """Write world-space results back into selected vertices' local coordinates."""
    if len(vertex_indices) != len(coordinates):
        raise ValueError("coordinate and target vertex counts differ")
    if abs(obj.matrix_world.to_3x3().determinant()) <= 1e-15:
        raise ValueError("Object has a singular transform; apply or correct its scale first")
    inverse_world = obj.matrix_world.inverted()
    for index, point in zip(vertex_indices, coordinates):
        bm.verts[index].co = inverse_world @ Vector(point)
    bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)
