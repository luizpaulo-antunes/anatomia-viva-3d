from __future__ import annotations

import hashlib
import json
import re
import stat
import tempfile
import urllib.error
import urllib.request
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .bodyparts3d import (
    DEFAULT_DATA_DIR,
    LEGACY_FMA_IDS,
    USER_CONTENT_ROOT,
    optimized_cache_is_complete,
)


CONTENT_MANIFEST_URL = (
    "https://github.com/luizpaulo-antunes/anatomia-viva-3d/"
    "releases/latest/download/anatomia-content.json"
)
CONTENT_METADATA_NAME = "content.json"
CONTENT_SCHEMA_VERSION = 1

DownloadProgress = Callable[[int, int | None], None]


class ContentUpdateError(RuntimeError):
    pass


class UpdateCancelled(ContentUpdateError):
    pass


@dataclass(frozen=True)
class ContentManifest:
    version: str
    structure_count: int
    archive_url: str
    archive_sha256: str
    archive_size: int

    @classmethod
    def from_dict(cls, payload: object) -> ContentManifest:
        if not isinstance(payload, dict):
            raise ContentUpdateError("O manifesto de conteúdo não é um objeto JSON.")
        try:
            schema = int(payload["schema_version"])
            version = str(payload["content_version"])
            count = int(payload["structure_count"])
            url = str(payload["archive_url"])
            digest = str(payload["archive_sha256"]).lower()
            size = int(payload["archive_size"])
        except (KeyError, TypeError, ValueError) as error:
            raise ContentUpdateError("O manifesto de conteúdo está incompleto.") from error
        if schema != CONTENT_SCHEMA_VERSION:
            raise ContentUpdateError(f"Versão de manifesto não suportada: {schema}.")
        if not re.fullmatch(r"[0-9A-Za-z][0-9A-Za-z._-]{0,63}", version):
            raise ContentUpdateError("A versão do pacote de conteúdo é inválida.")
        if count != len(LEGACY_FMA_IDS):
            raise ContentUpdateError(
                f"O pacote anuncia {count} estruturas, mas esta versão do aplicativo "
                f"suporta {len(LEGACY_FMA_IDS)}. Atualize o aplicativo primeiro."
            )
        if not url.startswith("https://"):
            raise ContentUpdateError("O pacote de conteúdo deve usar uma URL HTTPS.")
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ContentUpdateError("O SHA-256 do pacote é inválido.")
        if size <= 0:
            raise ContentUpdateError("O tamanho do pacote é inválido.")
        return cls(version, count, url, digest, size)


def fetch_manifest(url: str = CONTENT_MANIFEST_URL) -> ContentManifest:
    try:
        with urllib.request.urlopen(url, timeout=20) as response:
            payload = json.load(response)
    except (OSError, ValueError, urllib.error.URLError) as error:
        raise ContentUpdateError(f"Não foi possível consultar as atualizações: {error}") from error
    return ContentManifest.from_dict(payload)


def content_version(data_dir: Path = DEFAULT_DATA_DIR) -> str | None:
    metadata = data_dir / CONTENT_METADATA_NAME
    try:
        payload = json.loads(metadata.read_text(encoding="utf-8"))
        version = payload["content_version"]
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None
    return version if isinstance(version, str) and version else None


def _version_key(version: str) -> tuple[tuple[int, int | str], ...]:
    return tuple(
        (0, int(part)) if part.isdigit() else (1, part.casefold())
        for part in re.findall(r"\d+|[A-Za-z]+", version)
    )


def update_available(remote_version: str, local_version: str | None = None) -> bool:
    local = local_version if local_version is not None else content_version()
    return local is None or _version_key(remote_version) > _version_key(local)


def download_content(
    manifest: ContentManifest,
    root: Path = USER_CONTENT_ROOT,
    progress: DownloadProgress | None = None,
) -> Path:
    downloads = root / "downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    destination = downloads / f"AnatomiaViva3D-Content-{manifest.version}.zip"
    partial = destination.with_suffix(".zip.part")
    digest = hashlib.sha256()
    downloaded = 0
    try:
        request = urllib.request.Request(
            manifest.archive_url,
            headers={"User-Agent": "AnatomiaViva3D-content-updater"},
        )
        with urllib.request.urlopen(request, timeout=60) as response, partial.open("wb") as output:
            while block := response.read(1024 * 1024):
                output.write(block)
                digest.update(block)
                downloaded += len(block)
                if progress:
                    progress(downloaded, manifest.archive_size)
    except UpdateCancelled:
        partial.unlink(missing_ok=True)
        raise
    except (OSError, urllib.error.URLError) as error:
        partial.unlink(missing_ok=True)
        raise ContentUpdateError(f"Falha ao baixar o pacote anatômico: {error}") from error

    if downloaded != manifest.archive_size:
        partial.unlink(missing_ok=True)
        raise ContentUpdateError(
            f"Download incompleto: {downloaded} de {manifest.archive_size} bytes."
        )
    if digest.hexdigest() != manifest.archive_sha256:
        partial.unlink(missing_ok=True)
        raise ContentUpdateError("O pacote falhou na validação SHA-256 e foi descartado.")
    partial.replace(destination)
    return destination


def _validate_archive_members(archive: zipfile.ZipFile) -> None:
    for member in archive.infolist():
        normalized = member.filename.replace("\\", "/")
        path = PurePosixPath(normalized)
        unix_mode = member.external_attr >> 16
        if (
            path.is_absolute()
            or ".." in path.parts
            or re.match(r"^[A-Za-z]:", normalized)
            or stat.S_ISLNK(unix_mode)
        ):
            raise ContentUpdateError("O pacote contém um caminho de arquivo inseguro.")


def install_content_archive(
    archive_path: Path,
    manifest: ContentManifest,
    root: Path = USER_CONTENT_ROOT,
) -> Path:
    versions = root / "versions"
    versions.mkdir(parents=True, exist_ok=True)
    target = versions / manifest.version
    if target.exists():
        cached_count = len(list((target / "cache").glob("*.vtp")))
        if optimized_cache_is_complete(target) and cached_count == manifest.structure_count:
            pointer = root / "current.json"
            pointer_temp = root / "current.json.tmp"
            pointer_temp.write_text(
                json.dumps({"version": manifest.version}, indent=2) + "\n",
                encoding="utf-8",
            )
            pointer_temp.replace(pointer)
            return target
        raise ContentUpdateError(
            f"Já existe um pacote incompleto para a versão {manifest.version}."
        )

    with tempfile.TemporaryDirectory(prefix=".install-", dir=versions) as temporary:
        staging = Path(temporary) / "content"
        staging.mkdir()
        try:
            with zipfile.ZipFile(archive_path) as archive:
                _validate_archive_members(archive)
                archive.extractall(staging)
        except (OSError, zipfile.BadZipFile) as error:
            raise ContentUpdateError(f"O pacote anatômico não pôde ser extraído: {error}") from error

        if not optimized_cache_is_complete(staging):
            raise ContentUpdateError("O pacote não contém todas as malhas esperadas pelo aplicativo.")
        actual_count = len(list((staging / "cache").glob("*.vtp")))
        if actual_count != manifest.structure_count:
            raise ContentUpdateError(
                f"O pacote contém {actual_count} estruturas, mas anuncia "
                f"{manifest.structure_count}."
            )
        metadata = {
            "schema_version": CONTENT_SCHEMA_VERSION,
            "content_version": manifest.version,
            "structure_count": actual_count,
        }
        (staging / CONTENT_METADATA_NAME).write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        staging.replace(target)

    pointer = root / "current.json"
    pointer_temp = root / "current.json.tmp"
    pointer_temp.write_text(
        json.dumps({"version": manifest.version}, indent=2) + "\n",
        encoding="utf-8",
    )
    pointer_temp.replace(pointer)
    return target
