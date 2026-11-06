"""Resolution diagnostics and face-count safety estimates."""

from __future__ import annotations

import pytest

from clone_relief.density import analyze_resolution, estimate_face_count_upper_bound
from clone_relief.geometry import MeshPatch


def _grid_patch(spacing: float, steps: int = 4) -> MeshPatch:
    vertices = tuple(
        (x * spacing, y * spacing, 0.0)
        for y in range(steps + 1)
        for x in range(steps + 1)
    )
    faces = tuple(
        (
            y * (steps + 1) + x,
            y * (steps + 1) + x + 1,
            (y + 1) * (steps + 1) + x + 1,
            (y + 1) * (steps + 1) + x,
        )
        for y in range(steps)
        for x in range(steps)
    )
    return MeshPatch(vertices, faces)


def test_coarse_target_is_flagged_and_recommends_cuts_from_source_spacing() -> None:
    report = analyze_resolution(_grid_patch(0.1), _grid_patch(0.3))

    assert report.needs_subdivision
    assert report.p90_ratio == pytest.approx(3.0)
    assert report.recommended_cuts == 2
    assert report.target_median_edge == pytest.approx(0.3)


def test_target_near_source_spacing_is_not_flagged() -> None:
    report = analyze_resolution(_grid_patch(0.1), _grid_patch(0.14))

    assert report.p90_ratio == pytest.approx(1.4)
    assert not report.needs_subdivision
    assert report.recommended_cuts == 0


def test_face_estimate_includes_existing_faces_and_subdivision_growth() -> None:
    # Two affected triangles each split into four faces after one cut.
    assert estimate_face_count_upper_bound(10, (3, 3), cuts=1) == 16
    # A quad estimate is conservative because it is bounded by two triangles.
    assert estimate_face_count_upper_bound(10, (4,), cuts=1) == 17


@pytest.mark.parametrize(
    ("current", "sides", "cuts"),
    ((-1, (3,), 1), (1, (3, 3), 1), (5, (2,), 1), (5, (3,), 0)),
)
def test_invalid_face_estimates_are_rejected(
    current: int,
    sides: tuple[int, ...],
    cuts: int,
) -> None:
    with pytest.raises(ValueError):
        estimate_face_count_upper_bound(current, sides, cuts)
