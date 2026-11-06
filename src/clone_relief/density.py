"""Resolution diagnostics and bounded subdivision estimates without ``bpy``."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil, isfinite

from .geometry import MeshPatch, mesh_edges, length


@dataclass(frozen=True, slots=True)
class ResolutionReport:
    """Edge-size comparison between a source patch and a target patch."""

    source_median_edge: float
    target_median_edge: float
    target_p90_edge: float
    target_max_edge: float
    p90_ratio: float
    needs_subdivision: bool
    recommended_cuts: int


def _edge_lengths(mesh: MeshPatch) -> tuple[float, ...]:
    """Return finite positive edge lengths for a patch."""
    lengths = tuple(
        length(
            (
                mesh.vertices[second][0] - mesh.vertices[first][0],
                mesh.vertices[second][1] - mesh.vertices[first][1],
                mesh.vertices[second][2] - mesh.vertices[first][2],
            )
        )
        for first, second in mesh_edges(mesh.faces)
    )
    valid = tuple(value for value in lengths if isfinite(value) and value > 1e-15)
    if not valid:
        raise ValueError("mesh patch has no measurable nonzero edges")
    return valid


def _percentile(values: tuple[float, ...], fraction: float) -> float:
    """Return the nearest-rank percentile of already materialized values."""
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, ceil(fraction * len(ordered)) - 1))
    return ordered[index]


def analyze_resolution(
    source: MeshPatch,
    target: MeshPatch,
    *,
    threshold_ratio: float = 1.5,
) -> ResolutionReport:
    """Compare target edge sizes with source resolution and suggest uniform cuts.

    The source median edge length is the desired spacing. A target is flagged
    when its 90th-percentile edge is more than ``threshold_ratio`` times that
    spacing. Suggested cuts bring that percentile down to the source median.
    """
    if not isfinite(threshold_ratio) or threshold_ratio <= 1.0:
        raise ValueError("threshold_ratio must be finite and greater than 1")
    source_lengths = _edge_lengths(source)
    target_lengths = _edge_lengths(target)
    source_median = _percentile(source_lengths, 0.5)
    target_median = _percentile(target_lengths, 0.5)
    target_p90 = _percentile(target_lengths, 0.9)
    ratio = target_p90 / source_median
    cuts = max(0, ceil(ratio - 1e-12) - 1)
    return ResolutionReport(
        source_median_edge=source_median,
        target_median_edge=target_median,
        target_p90_edge=target_p90,
        target_max_edge=max(target_lengths),
        p90_ratio=ratio,
        needs_subdivision=ratio > threshold_ratio,
        recommended_cuts=cuts if ratio > threshold_ratio else 0,
    )


def estimate_face_count_upper_bound(
    current_face_count: int,
    affected_face_sides: tuple[int, ...],
    cuts: int,
) -> int:
    """Estimate an upper bound after uniformly subdividing affected edges.

    Triangles use the exact ``(cuts + 1) ** 2`` split count. For larger
    polygons, the estimate multiplies by their triangulated face count, making
    the result deliberately conservative. Adjacent faces affected at the
    target border should be included in ``affected_face_sides``.
    """
    if current_face_count < 0:
        raise ValueError("current_face_count must be nonnegative")
    if cuts < 1:
        raise ValueError("cuts must be at least one")
    if any(side_count < 3 for side_count in affected_face_sides):
        raise ValueError("affected faces must have at least three sides")
    if len(affected_face_sides) > current_face_count:
        raise ValueError("affected face count exceeds current face count")
    segments = cuts + 1
    estimated_affected = sum(
        max(1, side_count - 2) * segments * segments
        for side_count in affected_face_sides
    )
    return current_face_count - len(affected_face_sides) + estimated_affected
