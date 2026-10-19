import hashlib
import json
import zipfile

import pytest

from anatomia_app.bodyparts3d import LEGACY_FMA_IDS, cache_filename, installed_user_content_dir
from anatomia_app.content_updates import (
    ContentManifest,
    ContentUpdateError,
    content_version,
    install_content_archive,
    update_available,
)


def make_manifest(archive, version="0.4.0") -> ContentManifest:
    payload = archive.read_bytes()
    return ContentManifest(
        version=version,
        structure_count=len(LEGACY_FMA_IDS),
        archive_url="https://example.test/content.zip",
        archive_sha256=hashlib.sha256(payload).hexdigest(),
        archive_size=len(payload),
    )


def test_version_comparison() -> None:
    assert update_available("0.4.0", "0.3.0")
    assert update_available("1.0.0", None)
    assert not update_available("0.3.0", "0.3.0")
    assert not update_available("0.2.9", "0.3.0")


def test_installs_and_activates_complete_content_package(tmp_path) -> None:
    archive = tmp_path / "content.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        for structure_id in LEGACY_FMA_IDS:
            bundle.writestr(f"cache/{cache_filename(structure_id)}", b"mesh")

    root = tmp_path / "user-content"
    installed = install_content_archive(archive, make_manifest(archive), root)

    assert installed_user_content_dir(root) == installed
    assert content_version(installed) == "0.4.0"
    assert json.loads((root / "current.json").read_text())["version"] == "0.4.0"


@pytest.mark.parametrize("unsafe_name", ["../outside.txt", "..\\outside.txt", "C:\\outside.txt"])
def test_rejects_unsafe_archive_path(tmp_path, unsafe_name) -> None:
    archive = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr(unsafe_name, "unsafe")

    with pytest.raises(ContentUpdateError, match="inseguro"):
        install_content_archive(archive, make_manifest(archive), tmp_path / "content")
