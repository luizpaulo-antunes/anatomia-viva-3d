from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

from anatomia_app.zanatomy import SOURCE_FILES, STRUCTURE_COUNT, verify_files


REPOSITORY = "luizpaulo-antunes/anatomia-viva-3d"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while block := source.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def build(version: str, output_dir: Path, release_tag: str) -> tuple[Path, Path]:
    project_root = Path(__file__).resolve().parents[1]
    atlas_dir = project_root / "data" / "zanatomy"
    verify_files(atlas_dir)
    expected = [atlas_dir / item.name for item in SOURCE_FILES]
    metadata_file = atlas_dir / "atlas.json"
    if metadata_file.is_file():
        expected.append(metadata_file)

    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir / f"AnatomiaViva3D-Content-{version}.zip"
    metadata = {
        "schema_version": 2,
        "content_version": version,
        "atlas_version": "2026.09",
        "structure_count": STRUCTURE_COUNT,
    }
    with zipfile.ZipFile(
        archive,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=6,
    ) as bundle:
        bundle.writestr("content.json", json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
        for path in expected:
            bundle.write(path, f"zanatomy/{path.name}")

    manifest = {
        **metadata,
        "archive_url": (
            f"https://github.com/{REPOSITORY}/releases/download/{release_tag}/"
            f"{archive.name}"
        ),
        "archive_sha256": sha256(archive),
        "archive_size": archive.stat().st_size,
    }
    manifest_path = output_dir / "anatomia-content.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return archive, manifest_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera o pacote atualizável de anatomia.")
    parser.add_argument("--version", required=True)
    parser.add_argument("--release-tag")
    parser.add_argument("--output", type=Path, default=Path("release"))
    args = parser.parse_args()
    release_tag = args.release_tag or f"v{args.version}"
    archive, manifest = build(args.version, args.output, release_tag)
    print(f"Pacote de conteúdo: {archive}")
    print(f"Manifesto: {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
