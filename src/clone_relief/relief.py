"""Relief extraction and bounded spatial interpolation without ``bpy``."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from .geometry import (
    Face,
    MeshPatch,
    TangentFrame,
    Vec2,
    Vec3,
    _add,
    _mul,
    _sub,
    adjacency,
    boundary_vertices,
    dot,
    length,
    normalize,
    project_points,
    tangent_frame,
    vertex_normals,
)


@dataclass(frozen=True, slots=True)
class ReliefField:
    """Signed relief samples in a local 2D frame and their source faces."""

    coordinates: tuple[Vec2, ...]
    heights: tuple[float, ...]
    faces: tuple[Face, ...]

    def __post_init__(self) -> None:
        if len(self.coordinates) != len(self.heights):
            raise ValueError("relief coordinate and height counts differ")
        if not self.coordinates or not self.faces:
            raise ValueError("relief field must contain points and faces")
        if any(len(point) != 2 for point in self.coordinates):
            raise ValueError("relief coordinates must be 2D points")
        if not all(isfinite(value) for point in self.coordinates for value in point):
            raise ValueError("relief coordinates must be finite")
        if not all(isfinite(value) for value in self.heights):
            raise ValueError("relief heights must be finite")
        for face in self.faces:
            if (
                len(face) < 3
                or len(set(face)) < 3
                or any(index < 0 or index >= len(self.coordinates) for index in face)
            ):
                raise ValueError("relief faces must contain valid vertex indices")


@dataclass(frozen=True, slots=True)
class _Triangle:
    indices: tuple[int, int, int]
    bounds: tuple[float, float, float, float]
    centroid: Vec2


@dataclass(frozen=True, slots=True)
class _BVHNode:
    bounds: tuple[float, float, float, float]
    triangles: tuple[_Triangle, ...] = ()
    left: _BVHNode | None = None
    right: _BVHNode | None = None


def _bounds_for(triangles: tuple[_Triangle, ...]) -> tuple[float, float, float, float]:
    return (
        min(triangle.bounds[0] for triangle in triangles),
        min(triangle.bounds[1] for triangle in triangles),
        max(triangle.bounds[2] for triangle in triangles),
        max(triangle.bounds[3] for triangle in triangles),
    )


def _make_triangles(field: ReliefField) -> tuple[_Triangle, ...]:
    triangles: list[_Triangle] = []
    for face in field.faces:
        for index in range(1, len(face) - 1):
            indices = (face[0], face[index], face[index + 1])
            points = tuple(field.coordinates[item] for item in indices)
            triangles.append(
                _Triangle(
                    indices,
                    (
                        min(point[0] for point in points),
                        min(point[1] for point in points),
                        max(point[0] for point in points),
                        max(point[1] for point in points),
                    ),
                    (
                        sum(point[0] for point in points) / 3.0,
                        sum(point[1] for point in points) / 3.0,
                    ),
                )
            )
    if not triangles:
        raise ValueError("relief field contains no triangles")
    return tuple(triangles)


def _build_bvh(triangles: tuple[_Triangle, ...], leaf_size: int = 8) -> _BVHNode:
    bounds = _bounds_for(triangles)
    if len(triangles) <= leaf_size:
        return _BVHNode(bounds, triangles=triangles)
    x_span = bounds[2] - bounds[0]
    y_span = bounds[3] - bounds[1]
    axis = 0 if x_span >= y_span else 1
    ordered = tuple(sorted(triangles, key=lambda triangle: (triangle.centroid[axis], triangle.indices)))
    midpoint = len(ordered) // 2
    return _BVHNode(
        bounds,
        left=_build_bvh(ordered[:midpoint], leaf_size),
        right=_build_bvh(ordered[midpoint:], leaf_size),
    )


def _contains(bounds: tuple[float, float, float, float], point: Vec2, epsilon: float) -> bool:
    return (
        bounds[0] - epsilon <= point[0] <= bounds[2] + epsilon
        and bounds[1] - epsilon <= point[1] <= bounds[3] + epsilon
    )


def _query_bvh(node: _BVHNode, point: Vec2, epsilon: float) -> tuple[_Triangle, ...]:
    if not _contains(node.bounds, point, epsilon):
        return ()
    if node.triangles:
        return tuple(
            triangle for triangle in node.triangles
            if _contains(triangle.bounds, point, epsilon)
        )
    found: list[_Triangle] = []
    if node.left is not None:
        found.extend(_query_bvh(node.left, point, epsilon))
    if node.right is not None:
        found.extend(_query_bvh(node.right, point, epsilon))
    return tuple(found)


def _barycentric(point: Vec2, a: Vec2, b: Vec2, c: Vec2) -> tuple[float, float, float] | None:
    denominator = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(denominator) <= 1e-15:
        return None
    first = ((b[1] - c[1]) * (point[0] - c[0]) + (c[0] - b[0]) * (point[1] - c[1])) / denominator
    second = ((c[1] - a[1]) * (point[0] - c[0]) + (a[0] - c[0]) * (point[1] - c[1])) / denominator
    third = 1.0 - first - second
    tolerance = 1e-10
    if min(first, second, third) < -tolerance or max(first, second, third) > 1.0 + tolerance:
        return None
    return first, second, third


class ReliefSampler:
    """Reusable BVH sampler; build once and query many target vertices."""

    def __init__(self, field: ReliefField) -> None:
        self._field = field
        self._root = _build_bvh(_make_triangles(field))
        self._epsilon = max(
            self._root.bounds[2] - self._root.bounds[0],
            self._root.bounds[3] - self._root.bounds[1],
            1.0,
        ) * 1e-12

    def sample(self, point: Vec2) -> float | None:
        """Barycentrically sample a field or return None outside its domain."""
        candidates = _query_bvh(self._root, point, self._epsilon)
        for triangle in candidates:
            indices = triangle.indices
            weights = _barycentric(
                point,
                self._field.coordinates[indices[0]],
                self._field.coordinates[indices[1]],
                self._field.coordinates[indices[2]],
            )
            if weights is not None:
                return sum(self._field.heights[index] * weight for index, weight in zip(indices, weights))
        return None


def sample_relief(field: ReliefField, point: Vec2) -> float | None:
    """Sample a field once; repeated queries should reuse ``ReliefSampler``."""
    return ReliefSampler(field).sample(point)


def _smooth_once(
    vertices: tuple[Vec3, ...],
    neighbors: tuple[tuple[int, ...], ...],
    fixed: frozenset[int],
    factor: float,
) -> tuple[Vec3, ...]:
    result: list[Vec3] = []
    for index, point in enumerate(vertices):
        adjacent = neighbors[index]
        if index in fixed or not adjacent:
            result.append(point)
            continue
        average = tuple(
            sum(vertices[neighbor][axis] for neighbor in adjacent) / len(adjacent)
            for axis in range(3)
        )
        result.append(
            (
                point[0] + factor * (average[0] - point[0]),
                point[1] + factor * (average[1] - point[1]),
                point[2] + factor * (average[2] - point[2]),
            )
        )
    return tuple(result)


def smooth_reference(
    mesh: MeshPatch,
    *,
    iterations: int = 10,
    lambda_factor: float = 0.5,
    mu_factor: float = -0.53,
) -> tuple[Vec3, ...]:
    """Return Taubin-smoothed coordinates while pinning patch boundary vertices."""
    if iterations < 0:
        raise ValueError("iterations must be nonnegative")
    if not isfinite(lambda_factor) or not 0.0 < lambda_factor <= 1.0:
        raise ValueError("lambda_factor must be in (0, 1]")
    if not isfinite(mu_factor) or not -1.0 <= mu_factor < 0.0:
        raise ValueError("mu_factor must be in [-1, 0)")
    neighbors = adjacency(len(mesh.vertices), mesh.faces)
    fixed = frozenset(boundary_vertices(mesh.faces))
    current = mesh.vertices
    for _ in range(iterations):
        current = _smooth_once(current, neighbors, fixed, lambda_factor)
        current = _smooth_once(current, neighbors, fixed, mu_factor)
    return current


def extract_relief(
    mesh: MeshPatch,
    *,
    iterations: int = 10,
    lambda_factor: float = 0.5,
    mu_factor: float = -0.53,
) -> tuple[ReliefField, TangentFrame]:
    """Extract signed normal residuals relative to a smoothed source reference."""
    reference_vertices = smooth_reference(
        mesh,
        iterations=iterations,
        lambda_factor=lambda_factor,
        mu_factor=mu_factor,
    )
    reference = MeshPatch(reference_vertices, mesh.faces)
    normals = vertex_normals(reference)
    frame = tangent_frame(reference)
    coordinates = project_points(reference_vertices, frame)
    heights = tuple(dot(_sub(point, base), normal) for point, base, normal in zip(mesh.vertices, reference_vertices, normals))
    return ReliefField(coordinates, heights, mesh.faces), frame


def _target_falloff(mesh: MeshPatch, width_fraction: float) -> tuple[float, ...]:
    from .geometry import falloff_weights

    return falloff_weights(mesh, width_fraction)


def apply_relief(
    source: ReliefField,
    target: MeshPatch,
    *,
    intensity: float = 0.60,
    scale: float = 1.0,
    falloff_fraction: float = 0.25,
    max_displacement: float | None = None,
) -> tuple[Vec3, ...]:
    """Return updated target coordinates without mutating source or target.

    ``scale`` multiplies physical motif size: sampling at ``target / scale``
    makes a scale of 2 produce twice the wavelength. Samples outside the source
    chart are left unchanged.
    """
    if not isfinite(intensity) or intensity < 0.0 or intensity > 1.0:
        raise ValueError("intensity must be in the interval [0, 1]")
    if not isfinite(scale) or scale <= 0.0:
        raise ValueError("scale must be finite and greater than zero")
    if max_displacement is not None and (not isfinite(max_displacement) or max_displacement < 0.0):
        raise ValueError("max_displacement must be finite and nonnegative")
    frame = tangent_frame(target)
    target_coordinates = project_points(target.vertices, frame)
    normals = vertex_normals(target)
    weights = _target_falloff(target, falloff_fraction)
    sampler = ReliefSampler(source)
    output: list[Vec3] = []
    for index, point in enumerate(target.vertices):
        coordinate = (target_coordinates[index][0] / scale, target_coordinates[index][1] / scale)
        sampled = sampler.sample(coordinate)
        if sampled is None:
            output.append(point)
            continue
        displacement = sampled * intensity * weights[index]
        if max_displacement is not None:
            displacement = max(-max_displacement, min(max_displacement, displacement))
        output.append(_add(point, _mul(normals[index], displacement)))
    return tuple(output)
