import zipfile

from anatomia_app.bodyparts3d import (
    BODY_PARTS_IDS,
    LEGACY_FMA_IDS,
    extract_required_meshes,
    is_installed,
    optimized_cache_is_complete,
    required_ids,
)
from anatomia_app.catalog import CATALOG


def test_every_catalog_structure_has_real_mesh_mapping() -> None:
    assert set(BODY_PARTS_IDS) < set(CATALOG)
    assert set(LEGACY_FMA_IDS) < set(CATALOG)
    assert len([item for item in LEGACY_FMA_IDS if item.startswith("muscle_")]) == 422
    assert {"mao_d", "mao_e", "pe_d", "pe_e"} <= set(LEGACY_FMA_IDS)
    assert all(BODY_PARTS_IDS.values())
    assert all(LEGACY_FMA_IDS.values())


def test_extracts_only_required_meshes(tmp_path) -> None:
    archive_path = tmp_path / "source.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        for identifier in required_ids():
            archive.writestr(f"nested/folder/{identifier}.obj", "v 0 0 0\n")
        archive.writestr("nested/folder/BP0000.obj", "not required")

    count = extract_required_meshes(archive_path, tmp_path)

    assert count == len(required_ids())
    assert is_installed(tmp_path)
    assert not (tmp_path / "selected" / "BP0000.obj").exists()


def test_optimized_cache_can_be_distributed_without_raw_meshes(tmp_path) -> None:
    from anatomia_app.bodyparts3d import LEGACY_FMA_IDS, cache_dir, cache_filename

    folder = cache_dir(tmp_path)
    folder.mkdir(parents=True)
    for structure_id in LEGACY_FMA_IDS:
        (folder / cache_filename(structure_id)).touch()

    assert optimized_cache_is_complete(tmp_path)
    assert is_installed(tmp_path)
