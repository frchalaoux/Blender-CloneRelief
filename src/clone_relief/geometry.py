"""Structures et opérations géométriques pures pour les patches de maillage."""

from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush
from math import isfinite, sqrt
from typing import TypeAlias

Vec2: TypeAlias = tuple[float, float]
Vec3: TypeAlias = tuple[float, float, float]
Face: TypeAlias = tuple[int, ...]


def _add(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _mul(a: Vec3, value: float) -> Vec3:
    return (a[0] * value, a[1] * value, a[2] * value)


def dot(a: Vec3, b: Vec3) -> float:
    """Return the scalar product of two 3D vectors."""
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a: Vec3, b: Vec3) -> Vec3:
    """Return the cross product of two 3D vectors."""
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def length(vector: Vec3) -> float:
    """Return the Euclidean length of a 3D vector."""
    return sqrt(dot(vector, vector))


def normalize(vector: Vec3, *, label: str = "vector") -> Vec3:
    """Normalize a vector or reject it when its length is numerically zero."""
    magnitude = length(vector)
    if not isfinite(magnitude) or magnitude <= 1e-15:
        raise ValueError(f"{label} has zero or invalid length")
    return _mul(vector, 1.0 / magnitude)


@dataclass(frozen=True, slots=True)
class MeshPatch:
    """Compact local mesh data; face indices address ``vertices``."""

    vertices: tuple[Vec3, ...]
    faces: tuple[Face, ...]

    def __post_init__(self) -> None:
        if not self.vertices:
            raise ValueError("mesh patch must contain at least one vertex")
        if not self.faces:
            raise ValueError("mesh patch must contain at least one face")
        for vertex in self.vertices:
            if len(vertex) != 3 or not all(isfinite(component) for component in vertex):
                raise ValueError("vertices must contain three finite coordinates")
        for face in self.faces:
            if len(face) < 3:
                raise ValueError("faces must contain at least three indices")
            if len(set(face)) < 3:
                raise ValueError("faces must reference at least three distinct vertices")
            if any(index < 0 or index >= len(self.vertices) for index in face):
                raise ValueError("face index is outside the vertex array")


@dataclass(frozen=True, slots=True)
class TangentFrame:
    """Deterministic right-handed local frame attached to a mesh patch."""

    origin: Vec3
    tangent_u: Vec3
    tangent_v: Vec3
    normal: Vec3


def mesh_edges(faces: tuple[Face, ...]) -> tuple[tuple[int, int], ...]:
    """Return sorted unique undirected edges used by the faces."""
    edges: set[tuple[int, int]] = set()
    for face in faces:
        for index, start in enumerate(face):
            end = face[(index + 1) % len(face)]
            edges.add((min(start, end), max(start, end)))
    return tuple(sorted(edges))


def adjacency(vertex_count: int, faces: tuple[Face, ...]) -> tuple[tuple[int, ...], ...]:
    """Build deterministic vertex adjacency from face edges."""
    neighbors: list[set[int]] = [set() for _ in range(vertex_count)]
    for first, second in mesh_edges(faces):
        neighbors[first].add(second)
        neighbors[second].add(first)
    return tuple(tuple(sorted(items)) for items in neighbors)


def _face_normal_area(vertices: tuple[Vec3, ...], face: Face) -> tuple[Vec3, float]:
    origin = vertices[face[0]]
    accumulated: Vec3 = (0.0, 0.0, 0.0)
    for index in range(1, len(face) - 1):
        accumulated = _add(
            accumulated,
            cross(_sub(vertices[face[index]], origin), _sub(vertices[face[index + 1]], origin)),
        )
    area_twice = length(accumulated)
    if area_twice <= 1e-15:
        return (0.0, 0.0, 0.0), 0.0
    return _mul(accumulated, 1.0 / area_twice), area_twice * 0.5


def vertex_normals(mesh: MeshPatch) -> tuple[Vec3, ...]:
    """Return area-weighted vertex normals; reject isolated/degenerate vertices."""
    sums: list[Vec3] = [(0.0, 0.0, 0.0) for _ in mesh.vertices]
    for face in mesh.faces:
        normal, area = _face_normal_area(mesh.vertices, face)
        if area == 0.0:
            continue
        weighted = _mul(normal, area)
        for index in face:
            sums[index] = _add(sums[index], weighted)
    return tuple(normalize(value, label=f"normal at vertex {index}") for index, value in enumerate(sums))


def tangent_frame(mesh: MeshPatch) -> TangentFrame:
    """Build a stable frame using the area-weighted normal and world axes."""
    normal_sum: Vec3 = (0.0, 0.0, 0.0)
    for face in mesh.faces:
        normal, area = _face_normal_area(mesh.vertices, face)
        normal_sum = _add(normal_sum, _mul(normal, area))
    normal = normalize(normal_sum, label="patch average normal")
    axes: tuple[Vec3, ...] = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    reference = min(axes, key=lambda axis: abs(dot(axis, normal)))
    tangent_u = normalize(cross(reference, normal), label="frame tangent")
    tangent_v = normalize(cross(normal, tangent_u), label="frame bitangent")
    origin = tuple(
        sum(vertex[axis] for vertex in mesh.vertices) / len(mesh.vertices)
        for axis in range(3)
    )
    return TangentFrame(origin, tangent_u, tangent_v, normal)  # type: ignore[arg-type]


def project_points(vertices: tuple[Vec3, ...], frame: TangentFrame) -> tuple[Vec2, ...]:
    """Project 3D points into a frame's tangent plane."""
    result: list[Vec2] = []
    for point in vertices:
        offset = _sub(point, frame.origin)
        result.append((dot(offset, frame.tangent_u), dot(offset, frame.tangent_v)))
    return tuple(result)


def surface_area(mesh: MeshPatch) -> float:
    """Return the sum of polygon areas using a triangle fan."""
    return sum(_face_normal_area(mesh.vertices, face)[1] for face in mesh.faces)


def boundary_vertices(faces: tuple[Face, ...]) -> tuple[int, ...]:
    """Return vertices incident to an edge used by exactly one patch face."""
    counts: dict[tuple[int, int], int] = {}
    for face in faces:
        for index, start in enumerate(face):
            end = face[(index + 1) % len(face)]
            edge = (min(start, end), max(start, end))
            counts[edge] = counts.get(edge, 0) + 1
    boundary = {
        vertex
        for edge, count in counts.items()
        if count == 1
        for vertex in edge
    }
    return tuple(sorted(boundary))


def geodesic_distances_from_boundary(mesh: MeshPatch) -> tuple[float, ...]:
    """Compute edge-graph distances from the patch boundary with Dijkstra."""
    boundary = boundary_vertices(mesh.faces)
    if not boundary:
        return (float("inf"),) * len(mesh.vertices)
    neighbors = adjacency(len(mesh.vertices), mesh.faces)
    distances = [float("inf")] * len(mesh.vertices)
    queue: list[tuple[float, int]] = []
    for index in boundary:
        distances[index] = 0.0
        heappush(queue, (0.0, index))
    while queue:
        distance, current = heappop(queue)
        if distance != distances[current]:
            continue
        for neighbor in neighbors[current]:
            edge_length = length(_sub(mesh.vertices[neighbor], mesh.vertices[current]))
            candidate = distance + edge_length
            if candidate < distances[neighbor]:
                distances[neighbor] = candidate
                heappush(queue, (candidate, neighbor))
    return tuple(distances)


def falloff_weights(mesh: MeshPatch, width_fraction: float = 0.25) -> tuple[float, ...]:
    """Return a smooth geodesic boundary mask using sqrt(area) as patch width."""
    if not isfinite(width_fraction) or width_fraction <= 0.0 or width_fraction > 1.0:
        raise ValueError("width_fraction must be in the interval (0, 1]")
    distances = geodesic_distances_from_boundary(mesh)
    boundary = set(boundary_vertices(mesh.faces))
    if not boundary:
        return (1.0,) * len(mesh.vertices)
    width = sqrt(surface_area(mesh)) * width_fraction
    if width <= 1e-15:
        raise ValueError("target patch has zero area")
    weights: list[float] = []
    for index, distance in enumerate(distances):
        if index in boundary:
            weights.append(0.0)
            continue
        t = max(0.0, min(1.0, distance / width))
        weights.append(t * t * (3.0 - 2.0 * t))
    return tuple(weights)
