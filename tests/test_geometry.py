from anatomia_app.catalog import CATALOG
from anatomia_app.geometry import build_demo_meshes


def test_demo_model_matches_catalog() -> None:
    meshes = build_demo_meshes()
    assert set(meshes) < set(CATALOG)
    assert len(meshes) == 20
    assert all(mesh.n_points > 0 and mesh.n_cells > 0 for mesh in meshes.values())
