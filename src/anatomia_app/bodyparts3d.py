from __future__ import annotations

import argparse
import http.client
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zipfile
from collections.abc import Callable
from pathlib import Path

import pyvista as pv

from .geometry import merge
from .muscle_data import MUSCLE_MESHES


ARCHIVE_URL = (
    "https://dbarchive.biosciencedbc.jp/data/bodyparts3d/LATEST/"
    "isa_BP3D_4.0_obj_99.zip"
)
ARCHIVE_NAME = "isa_BP3D_4.0_obj_99.zip"
OFFICIAL_ATTRIBUTION = (
    "BodyParts3D, © The Database Center for Life Science licensed under "
    "CC Attribution 4.0 International"
)
LEGACY_ATTRIBUTION = (
    "BodyParts3D, © The Database Center for Life Science licensed under "
    "CC Attribution-ShareAlike 2.1 Japan; STL mirror by Kevin Mattheus Moerman"
)
ATTRIBUTION = OFFICIAL_ATTRIBUTION
LEGACY_BASE_URL = (
    "https://raw.githubusercontent.com/Kevin-Mattheus-Moerman/BodyParts3D/"
    "main/assets/BodyParts3D_data/stl"
)

PROJECT_ROOT = (
    Path(sys._MEIPASS)  # type: ignore[attr-defined]  # Provided by PyInstaller.
    if getattr(sys, "frozen", False)
    else Path(__file__).resolve().parents[2]
)
BUNDLED_DATA_DIR = PROJECT_ROOT / "data" / "bodyparts3d"


def user_content_root() -> Path:
    """Return a writable, per-user home for downloaded anatomy packages."""
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "AnatomiaViva3D" / "content"


USER_CONTENT_ROOT = user_content_root()


# Each application structure may be assembled from several original meshes.
# IDs come from the official isa_parts_list_e.txt table.
BODY_PARTS_IDS: dict[str, tuple[str, ...]] = {
    "cranio": (
        "BP8209", "BP9177", "BP8875", "BP7991", "BP9057", "BP9209",
        "BP8498", "BP8991", "BP8776", "BP8107", "BP8777", "BP8495",
        "BP8309", "BP9046", "BP9060", "BP8558", "BP8406", "BP7930",
        "BP8741", "BP8103", "BP8413", "BP9034",
    ),
    "coluna": (
        "BP8831", "BP8459", "BP9108", "BP8003", "BP8835", "BP7845", "BP7979",
        "BP8981", "BP8475", "BP8726", "BP9156", "BP8643", "BP8303", "BP8840",
        "BP9221", "BP8178", "BP8412", "BP8043", "BP9250", "BP8948", "BP8995",
        "BP8227", "BP8133", "BP8280", "BP9174",
    ),
    "costelas": (
        "BP8341", "BP8800", "BP9279", "BP8996", "BP8969", "BP8357",
        "BP9092", "BP8081", "BP8792", "BP8479", "BP8881", "BP9041",
        "BP8211", "BP9230", "BP9073", "BP8708", "BP9181", "BP8438",
        "BP8407", "BP9155", "BP8951", "BP9097", "BP9236", "BP9061",
    ),
    "esterno": ("BP8562", "BP8989", "BP7865"),
    "pelve": ("BP8768", "BP8950", "BP9174"),
    "umero_d": ("BP9206",),
    "umero_e": ("BP9191",),
    "antebraco_d": ("BP8464", "BP8233"),
    "antebraco_e": ("BP9059", "BP9070"),
    "femur_d": ("BP8920",),
    "femur_e": ("BP9042",),
    "perna_d": ("BP8031", "BP8009"),
    "perna_e": ("BP9202", "BP8251"),
    "deltoide_d": ("BP7573", "BP7571", "BP5607"),
    "deltoide_e": ("BP8259", "BP9075", "BP8151"),
    "biceps_d": ("BP5558", "BP5566"),
    "biceps_e": ("BP9153", "BP8816"),
    "peitoral": ("BP5582", "BP9095", "BP5613", "BP8323", "BP5615", "BP7862"),
    "quadriceps_d": ("BP5598", "BP5602", "BP5600", "BP5604"),
    "quadriceps_e": ("BP8094", "BP8754", "BP9128", "BP9207"),
}

LEGACY_FMA_IDS: dict[str, tuple[str, ...]] = {
    "cranio": ("FMA52734", "FMA52735", "FMA52738", "FMA52739", "FMA52788", "FMA52789", "FMA52736", "FMA52740", "FMA9710", "FMA52748", "FMA52892", "FMA52893", "FMA53649", "FMA53650", "FMA53647", "FMA53648", "FMA53655", "FMA53656", "FMA53645", "FMA53646", "FMA54737", "FMA54738"),
    "coluna": ("FMA12519", "FMA12520", "FMA12521", "FMA12522", "FMA12523", "FMA12524", "FMA12525", "FMA9165", "FMA9187", "FMA9209", "FMA9248", "FMA9922", "FMA9945", "FMA9968", "FMA9991", "FMA10014", "FMA10037", "FMA10059", "FMA10081", "FMA13072", "FMA13073", "FMA13074", "FMA13075", "FMA13076", "FMA16202"),
    "costelas": ("FMA7857", "FMA7987", "FMA7882", "FMA8012", "FMA7909", "FMA8039", "FMA7957", "FMA8148", "FMA8066", "FMA8093", "FMA8175", "FMA8202", "FMA8229", "FMA8256", "FMA8283", "FMA8310", "FMA8364", "FMA8391", "FMA8445", "FMA8472", "FMA8531", "FMA8532", "FMA8533", "FMA8534"),
    "esterno": ("FMA7486", "FMA7487", "FMA7488"),
    "pelve": ("FMA16586", "FMA16587", "FMA16202"),
    "umero_d": ("FMA23130",),
    "umero_e": ("FMA23131",),
    "antebraco_d": ("FMA23464", "FMA23467"),
    "antebraco_e": ("FMA23465", "FMA23468"),
    "femur_d": ("FMA24474",),
    "femur_e": ("FMA24475",),
    "perna_d": ("FMA24477", "FMA24480"),
    "perna_e": ("FMA24478", "FMA24481"),
    "deltoide_d": ("FMA34680", "FMA34682", "FMA34684"),
    "deltoide_e": ("FMA34681", "FMA34683", "FMA34685"),
    "biceps_d": ("FMA37684", "FMA37686"),
    "biceps_e": ("FMA37685", "FMA37687"),
    "peitoral": ("FMA34690", "FMA34691", "FMA79979", "FMA79980", "FMA45874", "FMA45875"),
    "quadriceps_d": ("FMA38928", "FMA38930", "FMA38932", "FMA38934"),
    "quadriceps_e": ("FMA38929", "FMA38931", "FMA38933", "FMA38935"),
    "masseter_d": ("FMA49001", "FMA49004"),
    "masseter_e": ("FMA49002", "FMA49005"),
    "temporal_d": ("FMA49007",),
    "temporal_e": ("FMA49008",),
    "esternocleidomastoideo_d": ("FMA13408",),
    "esternocleidomastoideo_e": ("FMA13409",),
    "trapezio_d": ("FMA33581", "FMA33584", "FMA33586"),
    "trapezio_e": ("FMA33583", "FMA33585", "FMA33587"),
    "latissimo_dorso_d": ("FMA13358",),
    "latissimo_dorso_e": ("FMA13359",),
    "reto_abdominal_d": ("FMA13377",),
    "reto_abdominal_e": ("FMA13378",),
    "obliquo_externo_d": ("FMA13336",),
    "obliquo_externo_e": ("FMA13337",),
    "triceps_d": ("FMA37695", "FMA37697", "FMA37699"),
    "triceps_e": ("FMA37696", "FMA37698", "FMA37700"),
    "braquial_d": ("FMA37668",),
    "braquial_e": ("FMA37669",),
    "braquiorradial_d": ("FMA38486",),
    "braquiorradial_e": ("FMA38487",),
    "flexor_carpo_radial_d": ("FMA38460",),
    "flexor_carpo_radial_e": ("FMA38461",),
    "extensor_carpo_radial_longo_d": ("FMA38495",),
    "extensor_carpo_radial_longo_e": ("FMA38496",),
    "gluteo_maximo_d": ("FMA22328",),
    "gluteo_maximo_e": ("FMA22329",),
    "gluteo_medio_d": ("FMA22330",),
    "gluteo_medio_e": ("FMA22331",),
    "sartorio_d": ("FMA22354",),
    "sartorio_e": ("FMA22355",),
    "adutores_d": ("FMA22452", "FMA22456", "FMA22459", "FMA43886"),
    "adutores_e": ("FMA22454", "FMA22457", "FMA22460", "FMA43887"),
    "isquiotibiais_d": ("FMA45888", "FMA45891", "FMA22358", "FMA22448"),
    "isquiotibiais_e": ("FMA45889", "FMA45892", "FMA22359", "FMA22449"),
    "gastrocnemio_d": ("FMA45957", "FMA45960"),
    "gastrocnemio_e": ("FMA45958", "FMA45961"),
    "soleo_d": ("FMA22558",),
    "soleo_e": ("FMA22559",),
    "tibial_anterior_d": ("FMA22544",),
    "tibial_anterior_e": ("FMA22545",),
}

# The legacy dictionary above documents the previous curated milestone.  The
# complete model renders the skeleton plus every primitive muscle mesh from the
# generated FMA manifest.  Aggregate muscle entries are intentionally omitted
# here because they would overlap their independently selectable components.
_SKELETAL_STRUCTURE_IDS = (
    "cranio", "coluna", "costelas", "esterno", "pelve", "umero_d", "umero_e",
    "antebraco_d", "antebraco_e", "femur_d", "femur_e", "perna_d", "perna_e",
)
_ADDITIONAL_SKELETAL_FMA_IDS: dict[str, tuple[str, ...]] = {
    "cintura_escapular_d": ("FMA13322", "FMA13395"),
    "cintura_escapular_e": ("FMA13323", "FMA13396"),
    "patela_d": ("FMA24486",),
    "patela_e": ("FMA24487",),
    "mao_d": (
        "FMA24435", "FMA24437", "FMA24439", "FMA24441", "FMA24443", "FMA23725",
        "FMA24446", "FMA24448", "FMA24464", "FMA24466", "FMA24468", "FMA24470",
        "FMA24472", "FMA24450", "FMA24451", "FMA24452", "FMA24453", "FMA24454",
        "FMA24455", "FMA24456", "FMA24457", "FMA24458", "FMA24459", "FMA24460",
        "FMA24461", "FMA24462", "FMA24463",
    ),
    "mao_e": (
        "FMA24436", "FMA24438", "FMA24440", "FMA24442", "FMA24444", "FMA24445",
        "FMA24447", "FMA24449", "FMA24465", "FMA24467", "FMA24469", "FMA24471",
        "FMA24473", "FMA65470", "FMA71915", "FMA71908", "FMA71916", "FMA66791",
        "FMA23938", "FMA23940", "FMA23942", "FMA23944", "FMA23951", "FMA23953",
        "FMA23955", "FMA23957", "FMA23959",
    ),
    "pe_d": (
        "FMA24482", "FMA24497", "FMA24500", "FMA24521", "FMA24523", "FMA24525",
        "FMA24528", "FMA24507", "FMA24509", "FMA24511", "FMA24513", "FMA24515",
        "FMA43253", "FMA32634", "FMA32636", "FMA32638", "FMA32640", "FMA32642",
        "FMA32644", "FMA32646", "FMA230986", "FMA32650", "FMA32652", "FMA32654",
        "FMA32656", "FMA32658", "FMA45097",
    ),
    "pe_e": (
        "FMA24483", "FMA24498", "FMA24501", "FMA24522", "FMA24524", "FMA24526",
        "FMA24529", "FMA24508", "FMA24510", "FMA24512", "FMA24514", "FMA24516",
        "FMA43254", "FMA32635", "FMA32637", "FMA32639", "FMA32641", "FMA32643",
        "FMA32645", "FMA32647", "FMA230988", "FMA32651", "FMA32653", "FMA32655",
        "FMA32657", "FMA32659", "FMA45098",
    ),
}
LEGACY_FMA_IDS = {
    **{identifier: LEGACY_FMA_IDS[identifier] for identifier in _SKELETAL_STRUCTURE_IDS},
    **_ADDITIONAL_SKELETAL_FMA_IDS,
    **{
        identifier: (mesh_id,)
        for identifier, _name_pt, _international, _region, mesh_id in MUSCLE_MESHES
    },
}

MUSCLE_RENDER_CELL_LIMIT = 25_000

ProgressCallback = Callable[[int, int | None], None]


def installed_user_content_dir(root: Path = USER_CONTENT_ROOT) -> Path | None:
    """Resolve the atomically activated user content package, if one exists."""
    pointer = root / "current.json"
    try:
        payload = json.loads(pointer.read_text(encoding="utf-8"))
        version = payload["version"]
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None
    if not isinstance(version, str) or not version or Path(version).name != version:
        return None
    candidate = root / "versions" / version
    if (candidate / "content.json").is_file() and (candidate / "cache").is_dir():
        return candidate
    return None


def active_data_dir() -> Path:
    """Prefer updated per-user content and fall back to the bundled offline set."""
    candidate = installed_user_content_dir()
    if candidate is None:
        return BUNDLED_DATA_DIR
    cache = candidate / "cache"
    complete = all(
        (
            cache
            / (
                f"v3.0-lod{MUSCLE_RENDER_CELL_LIMIT}-{structure_id}.vtp"
                if structure_id.startswith("muscle_")
                else f"v3.0-{structure_id}.vtp"
            )
        ).is_file()
        for structure_id in LEGACY_FMA_IDS
    )
    return candidate if complete else BUNDLED_DATA_DIR


DEFAULT_DATA_DIR = active_data_dir()


def archive_path(data_dir: Path = DEFAULT_DATA_DIR) -> Path:
    return data_dir / ARCHIVE_NAME


def extracted_dir(data_dir: Path = DEFAULT_DATA_DIR) -> Path:
    return data_dir / "selected"


def legacy_dir(data_dir: Path = DEFAULT_DATA_DIR) -> Path:
    return data_dir / "selected_v3"


def cache_dir(data_dir: Path = DEFAULT_DATA_DIR) -> Path:
    return data_dir / "cache"


def cache_filename(structure_id: str, version: str = "3.0") -> str:
    prefix = (
        f"v{version}-lod{MUSCLE_RENDER_CELL_LIMIT}"
        if structure_id.startswith("muscle_")
        else f"v{version}"
    )
    return f"{prefix}-{structure_id}.vtp"


def optimized_cache_is_complete(data_dir: Path = DEFAULT_DATA_DIR) -> bool:
    folder = cache_dir(data_dir)
    return all(
        (folder / cache_filename(structure_id)).is_file()
        for structure_id in LEGACY_FMA_IDS
    )


def required_ids() -> frozenset[str]:
    return frozenset(identifier for ids in BODY_PARTS_IDS.values() for identifier in ids)


def required_legacy_ids() -> frozenset[str]:
    return frozenset(identifier for ids in LEGACY_FMA_IDS.values() for identifier in ids)


def is_installed(data_dir: Path = DEFAULT_DATA_DIR) -> bool:
    folder = extracted_dir(data_dir)
    official = all((folder / f"{identifier}.obj").is_file() for identifier in required_ids())
    legacy = all(
        (legacy_dir(data_dir) / f"{identifier}.stl").is_file()
        for identifier in required_legacy_ids()
    )
    return official or legacy or optimized_cache_is_complete(data_dir)


def installed_version(data_dir: Path = DEFAULT_DATA_DIR) -> str | None:
    folder = extracted_dir(data_dir)
    if all((folder / f"{identifier}.obj").is_file() for identifier in required_ids()):
        return "4.0"
    if all(
        (legacy_dir(data_dir) / f"{identifier}.stl").is_file()
        for identifier in required_legacy_ids()
    ):
        return "3.0"
    if optimized_cache_is_complete(data_dir):
        return "3.0-cache"
    return None


def model_label(data_dir: Path = DEFAULT_DATA_DIR) -> str:
    version = installed_version(data_dir)
    if version in {"3.0", "3.0-cache"}:
        return f"BodyParts3D 3.0 · {len(MUSCLE_MESHES)} malhas musculares"
    return f"BodyParts3D {version}" if version else "BodyParts3D"


def current_attribution(data_dir: Path = DEFAULT_DATA_DIR) -> str:
    return OFFICIAL_ATTRIBUTION if installed_version(data_dir) == "4.0" else LEGACY_ATTRIBUTION


def _valid_archive(path: Path) -> bool:
    if not path.is_file() or not zipfile.is_zipfile(path):
        return False
    with zipfile.ZipFile(path) as archive:
        return archive.testzip() is None


def download_archive(
    data_dir: Path = DEFAULT_DATA_DIR,
    progress: ProgressCallback | None = None,
    retries: int = 30,
) -> Path:
    """Download with HTTP range resume; the official server may close long transfers."""
    data_dir.mkdir(parents=True, exist_ok=True)
    destination = archive_path(data_dir)
    partial = destination.with_suffix(destination.suffix + ".part")

    if _valid_archive(destination):
        return destination
    if destination.exists():
        if partial.exists():
            destination.unlink()
        else:
            destination.replace(partial)

    last_error: Exception | None = None
    for attempt in range(retries):
        current = partial.stat().st_size if partial.exists() else 0
        request = urllib.request.Request(ARCHIVE_URL)
        if current:
            request.add_header("Range", f"bytes={current}-")
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                status = getattr(response, "status", 200)
                append = current > 0 and status == 206
                if current > 0 and not append:
                    current = 0
                total: int | None = None
                content_range = response.headers.get("Content-Range")
                if content_range and "/" in content_range:
                    total_text = content_range.rsplit("/", 1)[1]
                    if total_text.isdigit():
                        total = int(total_text)
                if total is None:
                    length = response.headers.get("Content-Length")
                    if length and length.isdigit():
                        total = current + int(length)

                mode = "ab" if append else "wb"
                downloaded = current
                with partial.open(mode) as output:
                    while block := response.read(1024 * 1024):
                        output.write(block)
                        downloaded += len(block)
                        if progress:
                            progress(downloaded, total)
        except (OSError, urllib.error.URLError, http.client.HTTPException) as error:
            last_error = error
            if attempt + 1 < retries:
                time.sleep(1)
                continue

        if _valid_archive(partial):
            partial.replace(destination)
            return destination
        last_error = RuntimeError("o arquivo recebido ainda está incompleto")
        if attempt + 1 < retries:
            time.sleep(1)

    raise RuntimeError(f"Não foi possível baixar o BodyParts3D: {last_error}")


def extract_required_meshes(
    archive_file: Path,
    data_dir: Path = DEFAULT_DATA_DIR,
) -> int:
    target = extracted_dir(data_dir)
    target.mkdir(parents=True, exist_ok=True)
    needed = required_ids()
    extracted = 0
    with zipfile.ZipFile(archive_file) as archive:
        names = {
            Path(name).stem.upper(): name
            for name in archive.namelist()
            if name.lower().endswith(".obj")
        }
        missing = sorted(needed - names.keys())
        if missing:
            raise RuntimeError(
                "O arquivo oficial não contém as malhas esperadas: " + ", ".join(missing)
            )
        for identifier in sorted(needed):
            output = target / f"{identifier}.obj"
            if output.is_file():
                continue
            with archive.open(names[identifier]) as source, output.open("wb") as destination:
                shutil.copyfileobj(source, destination)
            extracted += 1
    return extracted


def install(
    data_dir: Path = DEFAULT_DATA_DIR,
    progress: ProgressCallback | None = None,
) -> int:
    existing_archive = archive_path(data_dir)
    if _valid_archive(existing_archive):
        return extract_required_meshes(existing_archive, data_dir)
    return download_legacy_meshes(data_dir, progress)


def download_legacy_meshes(
    data_dir: Path = DEFAULT_DATA_DIR,
    progress: ProgressCallback | None = None,
) -> int:
    """Download the selected binary STL meshes from the public v3 mirror."""
    target = legacy_dir(data_dir)
    target.mkdir(parents=True, exist_ok=True)
    identifiers = sorted(required_legacy_ids())
    downloaded = 0
    for index, identifier in enumerate(identifiers, start=1):
        output = target / f"{identifier}.stl"
        if output.is_file() and output.stat().st_size > 84:
            if progress:
                progress(index, len(identifiers))
            continue
        partial = output.with_suffix(".stl.part")
        url = f"{LEGACY_BASE_URL}/{identifier}.stl"
        try:
            with urllib.request.urlopen(url, timeout=60) as response, partial.open("wb") as file:
                shutil.copyfileobj(response, file)
        except (OSError, urllib.error.URLError, http.client.HTTPException) as error:
            curl = shutil.which("curl")
            if not curl:
                raise RuntimeError(f"Falha ao baixar {identifier}: {error}") from error
            try:
                subprocess.run(
                    [curl, "-L", "--fail", "--silent", "--show-error", "--output", partial, url],
                    check=True,
                )
            except subprocess.CalledProcessError as curl_error:
                raise RuntimeError(f"Falha ao baixar {identifier}: {error}") from curl_error
        if partial.stat().st_size <= 84:
            raise RuntimeError(f"A malha {identifier} está vazia ou inválida")
        partial.replace(output)
        downloaded += 1
        if progress:
            progress(index, len(identifiers))
    return downloaded


def load_meshes(
    data_dir: Path = DEFAULT_DATA_DIR,
    progress: ProgressCallback | None = None,
) -> dict[str, pv.PolyData]:
    if not is_installed(data_dir):
        raise FileNotFoundError("O modelo BodyParts3D ainda não foi instalado")
    version = installed_version(data_dir)
    result: dict[str, pv.PolyData] = {}
    if version == "3.0-cache":
        mapping = LEGACY_FMA_IDS
        folder = cache_dir(data_dir)
        total = len(mapping)
        for index, structure_id in enumerate(mapping, start=1):
            result[structure_id] = pv.read(folder / cache_filename(structure_id))
            if progress:
                progress(index, total)
        return result
    mapping = BODY_PARTS_IDS if version == "4.0" else LEGACY_FMA_IDS
    folder = extracted_dir(data_dir) if version == "4.0" else legacy_dir(data_dir)
    extension = ".obj" if version == "4.0" else ".stl"
    cache = cache_dir(data_dir)
    cache.mkdir(parents=True, exist_ok=True)
    total = len(mapping)
    for index, (structure_id, identifiers) in enumerate(mapping.items(), start=1):
        sources = [folder / f"{identifier}{extension}" for identifier in identifiers]
        cached = cache / cache_filename(structure_id, version)
        newest_source = max(path.stat().st_mtime for path in sources)
        if cached.is_file() and cached.stat().st_mtime >= newest_source:
            try:
                result[structure_id] = pv.read(cached)
                if progress:
                    progress(index, total)
                continue
            except (OSError, ValueError):
                pass
        parts = [pv.read(path) for path in sources]
        combined = merge(parts).clean()
        if structure_id.startswith("muscle_") and combined.n_cells > MUSCLE_RENDER_CELL_LIMIT:
            reduction = 1.0 - (MUSCLE_RENDER_CELL_LIMIT / combined.n_cells)
            combined = combined.decimate_pro(reduction, preserve_topology=True)
        combined.save(cached, binary=True)
        result[structure_id] = combined
        if progress:
            progress(index, total)
    return result


def prune_obsolete_cache(data_dir: Path = DEFAULT_DATA_DIR) -> int:
    """Remove only generated v3 cache files no longer referenced by this catalog."""
    folder = cache_dir(data_dir)
    if not folder.is_dir():
        return 0
    expected = {
        cache_filename(structure_id)
        for structure_id in LEGACY_FMA_IDS
    }
    removed = 0
    for path in folder.glob("v3.0-*.vtp"):
        if path.name not in expected:
            path.unlink()
            removed += 1
    return removed


def _console_progress(downloaded: int, total: int | None) -> None:
    if total:
        percentage = min(100, downloaded * 100 // total)
        message = f"\rBaixando malhas BodyParts3D: {percentage:3d}% ({downloaded}/{total})"
    else:
        message = f"\rBaixando BodyParts3D: {downloaded / 1_048_576:.1f} MB"
    print(message, end="", flush=True)


def _console_cache_progress(completed: int, total: int | None) -> None:
    assert total is not None
    percentage = min(100, completed * 100 // total)
    print(
        f"\rOtimizando malhas: {percentage:3d}% ({completed}/{total})",
        end="",
        flush=True,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gerencia as malhas do Atlas de Anatomia 3D")
    parser.add_argument("ação", choices=("instalar", "otimizar", "status"))
    args = parser.parse_args(argv)

    if args.ação == "status":
        present = sum(
            (legacy_dir() / f"{identifier}.stl").is_file()
            for identifier in required_legacy_ids()
        )
        if present == len(required_legacy_ids()):
            print(f"BodyParts3D instalado: {present}/{len(required_legacy_ids())} malhas locais.")
        elif optimized_cache_is_complete():
            print(f"BodyParts3D instalado: {len(LEGACY_FMA_IDS)} estruturas no pacote otimizado.")
        else:
            print(f"BodyParts3D incompleto: {present}/{len(required_legacy_ids())} malhas locais.")
        return 0

    if args.ação == "otimizar":
        if not is_installed():
            print("Erro: instale todas as malhas antes de otimizar.", file=sys.stderr)
            return 1
        print("Gerando o cache de renderização; a primeira execução pode demorar…")
        load_meshes(progress=_console_cache_progress)
        removed = prune_obsolete_cache()
        print(f"\nCache de renderização concluído; {removed} arquivos obsoletos removidos.")
        return 0

    try:
        count = install(progress=_console_progress)
    except (OSError, RuntimeError, zipfile.BadZipFile) as error:
        print(f"\nErro: {error}", file=sys.stderr)
        return 1
    print(f"\nAtlas instalado. {count} novas malhas extraídas.")
    print("Na primeira abertura, o atlas criará automaticamente o cache de renderização.")
    print(current_attribution())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
