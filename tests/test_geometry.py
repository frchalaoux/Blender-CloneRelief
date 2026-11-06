"""Tests for pure mesh topology, frames, and falloff helpers."""

from __future__ import annotations

import pytest

from clone_relief.geometry import MeshPatch, falloff_weights, tangent_frame


def grid_mesh(steps: int = 8, extent: float = 1.0) -> MeshPatch:
    vertices = tuple(
        (-extent + 2.0 * extent * x / steps, -extent + 2.0 * extent * y / steps, 0.0)
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


def test_falloff_is_zero_on_border_and_increases_inward() -> None:
    mesh = grid_mesh(steps=8)
    weights = falloff_weights(mesh, width_fraction=0.25)
    frame = tangent_frame(mesh)

    boundary_indices = {
        y * 9 + x
        for y in range(9)
        for x in range(9)
        if x in (0, 8) or y in (0, 8)
    }
    center = 4 * 9 + 4

    assert all(weights[index] == 0.0 for index in boundary_indices)
    assert 0.0 < weights[center] <= 1.0
    assert len(weights) == len(mesh.vertices)
    assert frame.normal == pytest.approx((0.0, 0.0, 1.0))


def test_invalid_patch_and_falloff_parameters_are_reported() -> None:
    with pytest.raises(ValueError, match="at least one vertex"):
        MeshPatch((), ())
    with pytest.raises(ValueError, match="interval"):
        falloff_weights(grid_mesh(), width_fraction=0.0)
