import numpy as np
import pyvista as pv

from anatomia_app.study_content import build_study_content, portuguese_name
from anatomia_app.zanatomy import (
    LIGHTWEIGHT_CELL_LIMIT,
    _simplify_geometry,
    recommended_cell_limit,
)


def test_portuguese_overrides_remove_english_fallbacks() -> None:
    assert portuguese_name("Incus", "Incus") == "Bigorna"
    assert portuguese_name("Anterior temporal branch", None) == "Ramo temporal anterior"
    assert portuguese_name("Unknown source term", None) == "Estrutura anatômica sem tradução validada"


def test_study_content_is_specific_to_structure_type() -> None:
    artery = build_study_content(
        "Artéria radial", "Radial artery", "Sistema cardiovascular"
    )
    nerve = build_study_content(
        "Nervo óptico", "Optic nerve (II)", "Sistema nervoso"
    )
    muscle = build_study_content(
        "Bíceps braquial", "Biceps brachii muscle", "Sistema muscular"
    )

    assert artery.classification == "Artéria ou ramo arterial"
    assert "irrigação" in artery.function
    assert nerve.function == "Conduz informações visuais da retina ao encéfalo."
    assert "Flexiona o cotovelo" in muscle.function
    assert all("inglês" not in item.description.casefold() for item in (artery, nerve, muscle))


def test_low_memory_windows_uses_lightweight_profile(monkeypatch) -> None:
    monkeypatch.delenv("ANATOMIA_3D_QUALIDADE", raising=False)
    assert recommended_cell_limit("win32", 8 * 1024**3) == LIGHTWEIGHT_CELL_LIMIT
    assert recommended_cell_limit("win32", 16 * 1024**3) is None
    assert recommended_cell_limit("darwin", 8 * 1024**3) is None

    monkeypatch.setenv("ANATOMIA_3D_QUALIDADE", "leve")
    assert recommended_cell_limit("darwin", 32 * 1024**3) == LIGHTWEIGHT_CELL_LIMIT
    monkeypatch.setenv("ANATOMIA_3D_QUALIDADE", "detalhada")
    assert recommended_cell_limit("win32", 8 * 1024**3) is None


def test_dense_geometry_is_reduced_to_cell_budget() -> None:
    sphere = pv.Sphere(theta_resolution=70, phi_resolution=70).triangulate()
    triangles = sphere.faces.reshape((-1, 4))[:, 1:]

    points, reduced, normals = _simplify_geometry(
        sphere.points,
        triangles,
        None,
        500,
    )

    assert len(reduced) <= 500
    assert len(points) < sphere.n_points
    assert normals is None
    assert np.min(reduced) >= 0
    assert np.max(reduced) < len(points)
