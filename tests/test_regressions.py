"""Regression coverage for malformed or low-information mesh patches."""

from __future__ import annotations

import pytest

from clone_relief.geometry import MeshPatch, vertex_normals
from clone_relief.relief import ReliefField


def test_degenerate_face_fails_with_a_clear_normal_diagnostic() -> None:
    mesh = MeshPatch(
        vertices=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (2.0, 0.0, 0.0)),
        faces=((0, 1, 2),),
    )
    with pytest.raises(ValueError, match="normal at vertex"):
        vertex_normals(mesh)


def test_invalid_relief_face_indices_are_rejected() -> None:
    with pytest.raises(ValueError, match="valid vertex indices"):
        ReliefField(((0.0, 0.0), (1.0, 0.0), (0.0, 1.0)), (0.0, 0.0, 0.0), ((0, 1, 3),))
