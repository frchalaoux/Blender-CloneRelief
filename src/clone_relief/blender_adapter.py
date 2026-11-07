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
    ignored_component_sizes: tuple[int, ...] = ()

    def as_patch(self) -> MeshPatch:
        """Return the captured world-space geometry as a pure mesh patch."""
        return MeshPatch(self.vertices_world, self.faces)


def prepare_capture_view(context: bpy.types.Context) -> bool:
    """Set the active workspace to Solid, X-Ray off, and face selection mode."""
    changed = False
    screen = getattr(context, "screen", None)
    screens = (screen,) if screen is not None else tuple(getattr(bpy.data, "screens", ()))
    for screen in screens:
        for area in screen.areas:
            if area.type != "VIEW_3D":
                continue
            shading = area.spaces.active.shading
            if shading.type != "SOLID":
                shading.type = "SOLID"
                changed = True
            if shading.show_xray:
                shading.show_xray = False
                changed = True
            area.tag_redraw()
    tool_settings = getattr(context, "tool_settings", None)
    if tool_settings is not None and tuple(tool_settings.mesh_select_mode) != (False, False, True):
        tool_settings.mesh_select_mode = (False, False, True)
        changed = True
    return changed

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


def _connected_components(
    faces: tuple[bmesh.types.BMFace, ...],
) -> list[tuple[bmesh.types.BMFace, ...]]:
    """Return selected face components connected by shared edges."""
    remaining = set(faces)
    components: list[tuple[bmesh.types.BMFace, ...]] = []
    while remaining:
        stack = [remaining.pop()]
        component: list[bmesh.types.BMFace] = []
        while stack:
            face = stack.pop()
            component.append(face)
            for edge in face.edges:
                for neighbor in edge.link_faces:
                    if neighbor in remaining:
                        remaining.remove(neighbor)
                        stack.append(neighbor)
        components.append(tuple(component))
    return components


def _assert_one_connected_component(faces: tuple[bmesh.types.BMFace, ...]) -> None:
    """Reject face selections connected only by separate islands."""
    component_sizes = [len(component) for component in _connected_components(faces)]
    if len(component_sizes) > 1:
        component_sizes.sort(reverse=True)
        sizes = ", ".join(f"{size} faces" for size in component_sizes[:3])
        if len(component_sizes) > 3:
            sizes += ", …"
        raise ValueError(
            f"La sélection contient {len(component_sizes)} groupes de faces séparés "
            f"({sizes}). Gardez un seul groupe relié par des arêtes."
        )


def capture_selection(
    context: bpy.types.Context,
    *,
    role: str,
    allow_dominant_component: bool = False,
) -> CapturedSelection:
    """Capture selected faces into a compact world-space snapshot."""
    if role not in {"source", "target"}:
        raise ValueError("role must be 'source' or 'target'")
    obj, bm = active_edit_mesh(context)
    selected_faces = tuple(sorted((face for face in bm.faces if face.select), key=lambda face: face.index))
    if not selected_faces:
        role_name = "source" if role == "source" else "cible"
        raise ValueError(f"Aucune face sélectionnée pour la {role_name}.")
    components = _connected_components(selected_faces)
    ignored_component_sizes: tuple[int, ...] = ()
    if len(components) > 1:
        components.sort(key=len, reverse=True)
        component_sizes = tuple(len(component) for component in components)
        largest_size = component_sizes[0]
        other_total = sum(component_sizes[1:])
        if allow_dominant_component and largest_size >= 2 * other_total:
            selected_faces = tuple(sorted(components[0], key=lambda face: face.index))
            for component in components[1:]:
                for face in component:
                    face.select_set(False)
            bm.select_flush_mode()
            bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)
            ignored_component_sizes = component_sizes[1:]
        else:
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
        ignored_component_sizes=ignored_component_sizes,
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
