from dataclasses import replace

import pyvista as pv

from anatomia_app.atlas import AtlasModel
from anatomia_app.catalog import Structure
from anatomia_app.female_reference import PARTS, add_female_reference
from anatomia_app.main_window import anatomical_profile_allows


def _base_atlas() -> AtlasModel:
    common = Structure("common", "Pelve", "Pelvis", "Sistema esquelético", "", "")
    male = Structure("male", "Próstata", "Prostata", "Órgãos e vísceras", "", "", anatomical_profile="masculino")
    mesh = pv.Sphere(theta_resolution=8, phi_resolution=8)
    return AtlasModel(
        meshes={"common": mesh, "male": mesh.copy()},
        structures=(common, male),
        label="Z-Anatomy teste",
        version="teste",
        source="teste",
        license_name="teste",
        attribution="teste",
        revision="teste",
        coverage_note="teste",
    )


def test_adds_complete_female_reproductive_subset() -> None:
    atlas = add_female_reference(_base_atlas())
    female = [item for item in atlas.structures if item.anatomical_profile == "feminino"]

    assert len(female) == len(PARTS) == 20
    assert {item.name for item in female} >= {"Útero", "Vagina", "Ovário direito", "Ovário esquerdo"}
    assert all(item.id in atlas.meshes and atlas.meshes[item.id].n_cells > 0 for item in female)
    assert all(item.region == "Pelve e períneo" for item in female)


def test_reference_is_registered_inside_pelvic_height() -> None:
    atlas = add_female_reference(_base_atlas())
    female_bounds = [atlas.meshes[item.id].bounds for item in atlas.structures if item.anatomical_profile == "feminino"]

    assert min(bounds[4] for bounds in female_bounds) > 0.79
    assert max(bounds[5] for bounds in female_bounds) < 0.96


def test_profile_selector_keeps_common_and_switches_specific_structures() -> None:
    common, male = _base_atlas().structures
    female = replace(male, id="female", anatomical_profile="feminino")

    assert anatomical_profile_allows(common, "masculino")
    assert anatomical_profile_allows(common, "feminino")
    assert anatomical_profile_allows(male, "masculino")
    assert not anatomical_profile_allows(male, "feminino")
    assert anatomical_profile_allows(female, "feminino")
    assert anatomical_profile_allows(male, "ambos")
    assert anatomical_profile_allows(female, "ambos")
