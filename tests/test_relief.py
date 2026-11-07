"""Tests for relief extraction, sampling, and target displacement."""

from __future__ import annotations

from math import pi, sin

import pytest

from clone_relief.geometry import MeshPatch, boundary_vertices, project_points, tangent_frame
from clone_relief.relief import ReliefField, apply_relief, extract_relief, sample_relief


def grid_mesh(steps: int = 16, extent: float = 2.0, heights: tuple[float, ...] | None = None) -> MeshPatch:
    xy = tuple(
        (-extent + 2.0 * extent * x / steps, -extent + 2.0 * extent * y / steps)
        for y in range(steps + 1)
        for x in range(steps + 1)
    )
    z_values = heights if heights is not None else (0.0,) * len(xy)
    vertices = tuple((point[0], point[1], z_values[index]) for index, point in enumerate(xy))
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


def field_for_mesh(mesh: MeshPatch, period: float = 2.5, amplitude: float = 0.2) -> ReliefField:
    frame = tangent_frame(mesh)
    coordinates = project_points(mesh.vertices, frame)
    heights = tuple(amplitude * sin(2.0 * pi * point[0] / period) for point in coordinates)
    return ReliefField(coordinates, heights, mesh.faces)


def test_flat_source_has_zero_residual_and_leaves_flat_target_unchanged() -> None:
    mesh = grid_mesh()
    source, _ = extract_relief(mesh)
    updated = apply_relief(source, mesh, intensity=0.6)

    assert max(abs(height) for height in source.heights) < 1e-12
    assert updated == mesh.vertices


def test_extraction_preserves_complete_surface_profile_above_average_plane() -> None:
    steps = 64
    extent = 2.0
    period = 0.5
    amplitude = 0.1
    heights = tuple(
        amplitude * sin(2.0 * pi * (-extent + 2.0 * extent * y / steps) / period)
        for y in range(steps + 1)
        for _x in range(steps + 1)
    )
    mesh = grid_mesh(steps=steps, extent=extent, heights=heights)
    field, frame = extract_relief(mesh)
    expected = tuple(
        vertex[2] - frame.origin[2]
        for vertex in mesh.vertices
    )

    assert max(abs(actual - reference) for actual, reference in zip(field.heights, expected)) < 1e-8


def test_synthetic_sinusoid_is_interpolated_in_physical_coordinates() -> None:
    mesh = grid_mesh(steps=32, extent=2.0)
    source = field_for_mesh(mesh)
    updated = apply_relief(
        source,
        mesh,
        intensity=1.0,
        falloff_fraction=0.25,
        direction="BIDIRECTIONAL",
    )
    frame = tangent_frame(mesh)
    coordinates = project_points(mesh.vertices, frame)
    interior_errors: list[float] = []

    for index, coordinate in enumerate(coordinates):
        x, y, z = mesh.vertices[index]
        if abs(x) < 0.8 and abs(y) < 0.8:
            expected = 0.2 * sin(2.0 * pi * coordinate[0] / 2.5)
            interior_errors.append(abs((updated[index][2] - z) - expected))

    assert interior_errors
    assert sum(interior_errors) / len(interior_errors) < 0.025


def test_intensity_is_linear_and_zero_intensity_does_not_move_vertices() -> None:
    mesh = grid_mesh(steps=24)
    source = field_for_mesh(mesh)
    zero = apply_relief(source, mesh, intensity=0.0)
    sixty = apply_relief(source, mesh, intensity=0.6)
    full = apply_relief(source, mesh, intensity=1.0)

    assert zero == mesh.vertices
    for original, at_sixty, at_full in zip(mesh.vertices, sixty, full):
        delta_sixty = at_sixty[2] - original[2]
        delta_full = at_full[2] - original[2]
        assert delta_sixty == pytest.approx(0.6 * delta_full, abs=1e-12)


def test_gain_multiplies_extracted_relief_without_changing_intensity_semantics() -> None:
    mesh = grid_mesh(steps=24)
    source = field_for_mesh(mesh)
    single = apply_relief(source, mesh, intensity=0.6, gain=1.0)
    amplified = apply_relief(source, mesh, intensity=0.6, gain=4.0)

    for original, one_x, four_x in zip(mesh.vertices, single, amplified):
        assert four_x[2] - original[2] == pytest.approx(
            4.0 * (one_x[2] - original[2]),
            abs=1e-12,
        )

    with pytest.raises(ValueError, match="gain"):
        apply_relief(source, mesh, gain=0.0)
    with pytest.raises(ValueError, match="gain"):
        apply_relief(source, mesh, gain=100.1)


def test_default_unidirectional_mode_never_moves_target_below_its_surface() -> None:
    mesh = grid_mesh(steps=24)
    source = field_for_mesh(mesh)
    updated = apply_relief(source, mesh, intensity=1.0)
    displacements = tuple(new[2] - old[2] for old, new in zip(mesh.vertices, updated))

    assert min(displacements) >= -1e-12
    assert max(displacements) > 0.0
    assert all(abs(displacements[index]) < 1e-12 for index in boundary_vertices(mesh.faces))


def test_unidirectional_mode_preserves_source_profile_with_constant_upward_offset() -> None:
    mesh = grid_mesh(steps=32)
    source = field_for_mesh(mesh)
    updated = apply_relief(source, mesh, intensity=1.0, gain=1.0, falloff_fraction=0.1)
    floor = min(source.heights)
    coordinates = project_points(mesh.vertices, tangent_frame(mesh))

    for index, point in enumerate(mesh.vertices):
        if abs(point[0]) < 0.5 and abs(point[1]) < 0.5:
            expected = sample_relief(source, coordinates[index]) - floor
            assert updated[index][2] - point[2] == pytest.approx(expected, abs=1e-10)


def test_bidirectional_mode_preserves_positive_and_negative_source_relief() -> None:
    mesh = grid_mesh(steps=24)
    source = field_for_mesh(mesh)
    updated = apply_relief(source, mesh, intensity=1.0, direction="BIDIRECTIONAL")
    displacements = tuple(new[2] - old[2] for old, new in zip(mesh.vertices, updated))

    assert min(displacements) < 0.0
    assert max(displacements) > 0.0


def test_scale_changes_motif_wavelength_and_outside_samples_are_not_extrapolated() -> None:
    mesh = grid_mesh(steps=32)
    source = field_for_mesh(mesh)
    point = source.coordinates[len(source.coordinates) // 2]
    expected = 0.2 * sin(2.0 * pi * point[0] / 2.5)

    assert sample_relief(source, point) == pytest.approx(expected, abs=0.01)
    assert sample_relief(source, (1e6, 1e6)) is None

    doubled = apply_relief(
        source,
        mesh,
        intensity=1.0,
        scale=2.0,
        direction="BIDIRECTIONAL",
    )
    frame = tangent_frame(mesh)
    coordinates = project_points(mesh.vertices, frame)
    center_row = sorted(
        (coordinates[index][0], doubled[index][2] - mesh.vertices[index][2])
        for index, vertex in enumerate(mesh.vertices)
        if abs(vertex[0]) < 1e-12 and abs(vertex[1]) < 1.5
    )
    scale_errors = [
        abs(height - 0.2 * sin(2.0 * pi * x / 5.0))
        for x, height in center_row
        if abs(x) < 0.9
    ]
    assert scale_errors
    assert max(scale_errors) < 0.025


def test_apply_does_not_mutate_input_data_and_rejects_invalid_inputs() -> None:
    mesh = grid_mesh()
    original_vertices = mesh.vertices
    original_heights = tuple(field_for_mesh(mesh).heights)
    source = field_for_mesh(mesh)
    apply_relief(source, mesh)

    assert mesh.vertices is original_vertices
    assert source.heights == original_heights
    with pytest.raises(ValueError, match="intensity"):
        apply_relief(source, mesh, intensity=1.1)
    with pytest.raises(ValueError, match="scale"):
        apply_relief(source, mesh, scale=0.0)
    with pytest.raises(ValueError, match="direction"):
        apply_relief(source, mesh, direction="INVALID")
