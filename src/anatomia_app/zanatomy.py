from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import DracoPy
import numpy as np
import pyvista as pv

from .atlas import AtlasModel
from .catalog import Structure


EXPORT_COMMIT = "8ca3b7421bcfbe88b85859eb1983d5cf79f21749"
TERMINOLOGY_COMMIT = "767f14e0a4dfc55aa7c3455685b62339a4faec99"
ATLAS_VERSION = "2026.09"
TERMINOLOGY_VERSION = "TA2 / Z-Anatomy 2026.10"
STRUCTURE_COUNT = 2827
BASE_EXPORT_URL = (
    "https://raw.githubusercontent.com/nqwrc/3d-anatomy/"
    f"{EXPORT_COMMIT}/public"
)
TA2_URL = (
    "https://raw.githubusercontent.com/Z-Anatomy/Models-of-human-anatomy/"
    f"{TERMINOLOGY_COMMIT}/TA2.csv"
)
ATTRIBUTION = (
    "Z-Anatomy — The open source atlas of anatomy (CC BY-SA 4.0); "
    "BodyParts3D — The Database Center for Life Science (CC BY-SA 2.1 Japan)."
)
LICENSE_SUMMARY = (
    "CC BY-SA 4.0 (atlas principal); componentes do ouvido interno em "
    "CC BY-NC-SA 4.0 e rins em CC BY-NC 4.0"
)


@dataclass(frozen=True, slots=True)
class SourceFile:
    name: str
    url: str
    sha256: str
    size: int
    system: str | None = None


def _export_file(name: str, digest: str, size: int, system: str | None = None) -> SourceFile:
    folder = "models" if name.endswith((".glb", ".txt")) else "data"
    return SourceFile(name, f"{BASE_EXPORT_URL}/{folder}/{name}", digest, size, system)


SOURCE_FILES: tuple[SourceFile, ...] = (
    _export_file(
        "skeletal.glb",
        "c2b70b31ddec4062cbc5ba969fc24ecfed61d00397a0bca795e2701d997200f8",
        1_863_828,
        "Sistema esquelético",
    ),
    _export_file(
        "joints.glb",
        "9fdab1a257652597cf8f0b2ac93d12abc817e8f9a9099b9628e764018490afa2",
        921_960,
        "Articulações, ligamentos e fáscias",
    ),
    _export_file(
        "muscular.glb",
        "f69ed1287f802a2d603d23293e01512bb57ae77ee7cca1d5527ba00496e51de2",
        4_503_232,
        "Sistema muscular",
    ),
    _export_file(
        "cardiovascular.glb",
        "bc94c7b8eb1712f18ee461e064140e54aa817f3614e0f56a45b00e2a829cfb59",
        5_614_112,
        "Sistema cardiovascular",
    ),
    _export_file(
        "lymphatic.glb",
        "718cac2b26ad752224cc8a11b2d5bf733fb523b75d9614822a24af7d19202756",
        419_488,
        "Sistema linfático",
    ),
    _export_file(
        "nervous.glb",
        "c7cde35497f887b319c0a84f1b5b605fa3ce66e23084b5e09d6e3825fa5030d9",
        3_802_588,
        "Sistema nervoso",
    ),
    _export_file(
        "visceral.glb",
        "b21a0f34b3da1bb0b6a9a6ae71d16ffbc036beb504944af2422d4b91a9317fe5",
        1_844_996,
        "Órgãos e vísceras",
    ),
    _export_file(
        "definitions.json",
        "ff91719a0c839f3c09f151b5f99743085907d8b46bc7ad300ae72c6a70acb970",
        616_577,
    ),
    _export_file(
        "lexicon.json",
        "bedec30d82f6e02197076c61311e8d1fb2e51e1d6b273d36c1a064c7308e2002",
        99_721,
    ),
    SourceFile(
        "TA2.csv",
        TA2_URL,
        "0f9092a328b27dcd15d696d9f9a4087deb229a1aad21b75876657622de835974",
        1_510_396,
    ),
    _export_file(
        "License.txt",
        "47c73bd1a7557f49fa5a2c02561ce6ca4ac0169066ab76fc6a6351835f5d185f",
        1_746,
    ),
)

SYSTEM_FILES = tuple(item for item in SOURCE_FILES if item.system)
TOTAL_DOWNLOAD_SIZE = sum(item.size for item in SOURCE_FILES)
ProgressCallback = Callable[[int, int, str], None]

PROJECT_ROOT = (
    Path(sys._MEIPASS)  # type: ignore[attr-defined]
    if getattr(sys, "frozen", False)
    else Path(__file__).resolve().parents[2]
)
BUNDLED_DATA_DIR = PROJECT_ROOT / "data" / "zanatomy"


def user_data_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "AnatomiaViva3D" / "zanatomy"


USER_DATA_DIR = user_data_dir()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while block := source.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def is_installed(data_dir: Path) -> bool:
    return all(
        (data_dir / item.name).is_file()
        and (data_dir / item.name).stat().st_size == item.size
        for item in SOURCE_FILES
    )


def installed_data_dir() -> Path | None:
    for candidate in (USER_DATA_DIR, BUNDLED_DATA_DIR):
        if is_installed(candidate):
            try:
                verify_files(candidate)
            except (OSError, ValueError):
                continue
            return candidate
    return None


def verify_files(data_dir: Path) -> None:
    for item in SOURCE_FILES:
        path = data_dir / item.name
        if not path.is_file():
            raise FileNotFoundError(f"Arquivo anatômico ausente: {item.name}")
        if path.stat().st_size != item.size or sha256(path) != item.sha256:
            raise ValueError(f"Falha de integridade no arquivo anatômico: {item.name}")


def install(data_dir: Path = BUNDLED_DATA_DIR, progress: ProgressCallback | None = None) -> Path:
    """Download the pinned, reproducible modern atlas and verify every file."""
    data_dir.mkdir(parents=True, exist_ok=True)
    completed = 0
    for item in SOURCE_FILES:
        destination = data_dir / item.name
        if (
            destination.is_file()
            and destination.stat().st_size == item.size
            and sha256(destination) == item.sha256
        ):
            completed += item.size
            if progress:
                progress(completed, TOTAL_DOWNLOAD_SIZE, item.name)
            continue

        partial = destination.with_suffix(destination.suffix + ".part")
        request = urllib.request.Request(
            item.url,
            headers={"User-Agent": "AnatomiaViva3D/0.4 (+https://github.com/luizpaulo-antunes/anatomia-viva-3d)"},
        )
        try:
            with urllib.request.urlopen(request, timeout=90) as response, partial.open("wb") as output:
                while block := response.read(1024 * 1024):
                    output.write(block)
                    if progress:
                        progress(
                            min(completed + output.tell(), TOTAL_DOWNLOAD_SIZE),
                            TOTAL_DOWNLOAD_SIZE,
                            item.name,
                        )
        except (OSError, urllib.error.URLError) as error:
            curl = shutil.which("curl")
            if not curl:
                raise RuntimeError(f"Falha ao baixar {item.name}: {error}") from error
            try:
                subprocess.run(
                    [
                        curl,
                        "-L",
                        "--fail",
                        "--silent",
                        "--show-error",
                        "--output",
                        str(partial),
                        item.url,
                    ],
                    check=True,
                )
            except subprocess.CalledProcessError as curl_error:
                raise RuntimeError(f"Falha ao baixar {item.name}: {error}") from curl_error
        if partial.stat().st_size != item.size or sha256(partial) != item.sha256:
            partial.unlink(missing_ok=True)
            raise ValueError(f"O download de {item.name} não corresponde à revisão publicada")
        partial.replace(destination)
        completed += item.size

    verify_files(data_dir)
    report = coverage_report(data_dir)
    metadata = {
        "schema_version": 2,
        "atlas": "Z-Anatomy",
        "atlas_version": ATLAS_VERSION,
        "export_commit": EXPORT_COMMIT,
        "terminology": TERMINOLOGY_VERSION,
        "terminology_commit": TERMINOLOGY_COMMIT,
        "structure_count": report["structure_count"],
        "license": LICENSE_SUMMARY,
        "files": {
            item.name: {"sha256": item.sha256, "size": item.size, "source": item.url}
            for item in SOURCE_FILES
        },
        "coverage": report,
    }
    (data_dir / "atlas.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return data_dir


def _read_glb(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    if len(raw) < 20:
        raise ValueError(f"GLB inválido: {path.name}")
    magic, version, length = struct.unpack_from("<III", raw, 0)
    if magic != 0x46546C67 or version != 2 or length != len(raw):
        raise ValueError(f"Cabeçalho GLB inválido: {path.name}")
    json_chunk: bytes | None = None
    binary_chunk: bytes | None = None
    offset = 12
    while offset < length:
        chunk_length, chunk_type = struct.unpack_from("<II", raw, offset)
        offset += 8
        chunk = raw[offset : offset + chunk_length]
        offset += chunk_length
        if chunk_type == 0x4E4F534A:
            json_chunk = chunk
        elif chunk_type == 0x004E4942:
            binary_chunk = chunk
    if json_chunk is None or binary_chunk is None:
        raise ValueError(f"GLB sem blocos JSON/BIN: {path.name}")
    return json.loads(json_chunk.rstrip(b" \x00")), binary_chunk


def _local_matrix(node: dict[str, Any]) -> np.ndarray:
    if "matrix" in node:
        return np.asarray(node["matrix"], dtype=float).reshape((4, 4), order="F")
    translation = np.asarray(node.get("translation", (0.0, 0.0, 0.0)), dtype=float)
    scale = np.asarray(node.get("scale", (1.0, 1.0, 1.0)), dtype=float)
    x, y, z, w = node.get("rotation", (0.0, 0.0, 0.0, 1.0))
    rotation = np.asarray(
        (
            (1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
            (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
            (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)),
        ),
        dtype=float,
    )
    matrix = np.eye(4)
    matrix[:3, :3] = rotation @ np.diag(scale)
    matrix[:3, 3] = translation
    return matrix


def _world_matrices(document: dict[str, Any]) -> list[np.ndarray]:
    nodes = document.get("nodes", [])
    parents: dict[int, int] = {}
    for parent_index, node in enumerate(nodes):
        for child in node.get("children", []):
            parents[child] = parent_index
    cache: dict[int, np.ndarray] = {}

    def resolve(index: int) -> np.ndarray:
        if index not in cache:
            local = _local_matrix(nodes[index])
            cache[index] = resolve(parents[index]) @ local if index in parents else local
        return cache[index]

    return [resolve(index) for index in range(len(nodes))]


def _material_color(document: dict[str, Any], primitive: dict[str, Any]) -> str:
    default = "#d1a25b"
    material_index = primitive.get("material")
    if material_index is None:
        return default
    try:
        factor = document["materials"][material_index]["pbrMetallicRoughness"]["baseColorFactor"]
        red, green, blue = (max(0, min(255, round(float(value) * 255))) for value in factor[:3])
    except (IndexError, KeyError, TypeError, ValueError):
        return default
    return f"#{red:02x}{green:02x}{blue:02x}"


def _decode_mesh(
    document: dict[str, Any],
    binary: bytes,
    mesh_index: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray | None, str]:
    point_parts: list[np.ndarray] = []
    face_parts: list[np.ndarray] = []
    normal_parts: list[np.ndarray] = []
    all_have_normals = True
    point_offset = 0
    color = "#d1a25b"
    for primitive in document["meshes"][mesh_index].get("primitives", []):
        extension = primitive.get("extensions", {}).get("KHR_draco_mesh_compression")
        if extension is None:
            raise ValueError("A exportação contém uma primitiva sem compressão Draco")
        view = document["bufferViews"][extension["bufferView"]]
        start = int(view.get("byteOffset", 0))
        end = start + int(view["byteLength"])
        decoded = DracoPy.decode(binary[start:end])
        points = np.asarray(decoded.points, dtype=np.float64)
        faces = np.asarray(decoded.faces, dtype=np.int64)
        if not len(points) or not len(faces):
            continue
        point_parts.append(points)
        face_parts.append(faces + point_offset)
        normals = getattr(decoded, "normals", None)
        if normals is None or len(normals) != len(points):
            all_have_normals = False
        else:
            normal_parts.append(np.asarray(normals, dtype=np.float64))
        point_offset += len(points)
        if len(point_parts) == 1:
            color = _material_color(document, primitive)
    if not point_parts:
        raise ValueError("Malha Draco sem triângulos")
    combined_normals = np.vstack(normal_parts) if all_have_normals and normal_parts else None
    return np.vstack(point_parts), np.vstack(face_parts), combined_normals, color


def _polydata(
    points: np.ndarray,
    triangles: np.ndarray,
    normals: np.ndarray | None,
    matrix: np.ndarray,
) -> pv.PolyData:
    transformed = points @ matrix[:3, :3].T + matrix[:3, 3]
    if np.linalg.det(matrix[:3, :3]) < 0:
        triangles = triangles[:, (0, 2, 1)]
    vtk_faces = np.empty((len(triangles), 4), dtype=np.int64)
    vtk_faces[:, 0] = 3
    vtk_faces[:, 1:] = triangles
    mesh = pv.PolyData(transformed, vtk_faces.ravel())
    if normals is not None:
        transformed_normals = normals @ np.linalg.inv(matrix[:3, :3])
        lengths = np.linalg.norm(transformed_normals, axis=1)
        transformed_normals /= np.where(lengths == 0, 1, lengths)[:, None]
        mesh.point_data["Normals"] = transformed_normals.astype(np.float32)
        mesh.point_data.active_normals_name = "Normals"
    return mesh


GLTF_TO_APP = np.asarray(
    (
        (1.0, 0.0, 0.0, 0.0),
        (0.0, 0.0, -1.0, 0.0),
        (0.0, 1.0, 0.0, 0.0),
        (0.0, 0.0, 0.0, 1.0),
    )
)


def _read_ta2(path: Path) -> dict[str, dict[str, str]]:
    lines: list[str] = []
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        if not raw:
            continue
        if raw.startswith('"') and raw.endswith('"'):
            raw = raw[1:-1].replace('""', '"')
        lines.append(raw)
    return {
        row["English"].strip().casefold(): row
        for row in csv.DictReader(lines, delimiter=";")
        if row.get("English")
    }


def _base_name(raw_name: str) -> tuple[str, str]:
    match = re.search(r"\.([lr])$", raw_name)
    if not match:
        return raw_name.strip(), ""
    side = "esquerdo" if match.group(1) == "l" else "direito"
    return raw_name[:-2].strip(), side


def _identifier(system_file: str, raw_name: str) -> str:
    digest = hashlib.sha1(f"{system_file}:{raw_name}".encode()).hexdigest()[:16]
    return f"za_{digest}"


SYSTEM_FUNCTIONS = {
    "Sistema esquelético": "Sustentação, proteção e alavanca mecânica, conforme a estrutura.",
    "Articulações, ligamentos e fáscias": "Conecta, estabiliza, reveste ou permite movimento entre estruturas.",
    "Sistema muscular": "Produz movimento ou estabilização; consulte a descrição de referência quando disponível.",
    "Sistema cardiovascular": "Participa da circulação ou da condução do sangue.",
    "Sistema linfático": "Participa da drenagem linfática e da resposta imune.",
    "Sistema nervoso": "Participa da recepção, integração ou transmissão de sinais nervosos.",
    "Órgãos e vísceras": "Exerce função específica do órgão ou sistema ao qual pertence.",
}


def _source_license(base_name: str) -> str:
    if base_name in {"Cochlea", "Vestibule"}:
        return "CC BY-NC-SA 4.0 — University of Dundee School of Medicine"
    if base_name == "Kidney":
        return "CC BY-NC 4.0 — lissiecowley"
    return "CC BY-SA 4.0 — Z-Anatomy (com atribuições indicadas em License.txt)"


def _structure(
    source_file: SourceFile,
    raw_name: str,
    ta2: dict[str, dict[str, str]],
    lexicon: dict[str, dict[str, Any]],
    definitions: dict[str, str],
) -> Structure:
    base_name, side = _base_name(raw_name)
    term = ta2.get(base_name.casefold(), {})
    lexicon_term = lexicon.get(base_name, {})
    unidentified = not base_name.strip(" ?x")
    display_base = (
        "Estrutura sem identificação anatômica na fonte"
        if unidentified
        else base_name
    )
    portuguese = (term.get("Portugues") or display_base).strip()
    latin = (
        term.get("Latin")
        or lexicon_term.get("la")
        or ("Nomen non identificatum" if unidentified else base_name)
    ).strip()
    side_suffix = f" — lado {side}" if side else ""
    ta2_id = (term.get("TA2ID") or "não associado automaticamente").strip()
    official = lexicon_term.get("official")
    official_label = (
        "Sim (TA2)"
        if term
        else "Sim"
        if official is True
        else "Não/termo complementar"
        if official is False
        else "Não informado"
    )
    reference = definitions.get(base_name)
    if reference:
        description = f"Descrição de referência (em inglês): {reference}"
    else:
        description = (
            "Estrutura individualizada no modelo tridimensional. "
            "A fonte não fornece uma descrição textual revisada para este item."
        )
    details = (
        ("Nome original", raw_name),
        ("Identificador TA2", ta2_id),
        ("Termo oficial no léxico", official_label),
        ("Fonte geométrica", f"Z-Anatomy, exportação {ATLAS_VERSION}"),
        ("Licença desta malha", _source_license(base_name)),
    )
    return Structure(
        _identifier(source_file.name, raw_name),
        f"{portuguese}{side_suffix}",
        f"{latin}{side_suffix}",
        source_file.system or "Outro",
        description,
        SYSTEM_FUNCTIONS[source_file.system or "Outro"],
        details,
    )


def _glb_names(path: Path) -> list[str]:
    document, _binary = _read_glb(path)
    return [
        node.get("extras", {}).get("za_name") or node.get("name", "Estrutura sem nome")
        for node in document.get("nodes", [])
        if "mesh" in node
    ]


def coverage_report(data_dir: Path) -> dict[str, Any]:
    ta2 = _read_ta2(data_dir / "TA2.csv")
    definitions = json.loads((data_dir / "definitions.json").read_text(encoding="utf-8"))
    systems: dict[str, int] = {}
    unmatched: list[str] = []
    questionable: list[str] = []
    definition_count = 0
    total = 0
    for item in SYSTEM_FILES:
        names = _glb_names(data_dir / item.name)
        systems[item.system or item.name] = len(names)
        total += len(names)
        for raw_name in names:
            base, _side = _base_name(raw_name)
            if base.casefold() not in ta2:
                unmatched.append(base)
            if base in definitions:
                definition_count += 1
            if not base.strip(" ?") or "?" in base or base.startswith(" "):
                questionable.append(raw_name)
    unique_unmatched = sorted(set(unmatched), key=str.casefold)
    return {
        "structure_count": total,
        "systems": systems,
        "ta2_matched": total - len(unmatched),
        "ta2_match_percent": round((total - len(unmatched)) * 100 / total, 1),
        "definitions_available": definition_count,
        "unmatched_source_names": unique_unmatched,
        "questionable_source_names": sorted(set(questionable), key=str.casefold),
        "limitations": [
            "Cobertura representa as malhas existentes na revisão da fonte, não toda entidade da TA2.",
            "Descrições textuais da fonte são majoritariamente Wikipédia em inglês e não equivalem a revisão clínica.",
            "A própria fonte Z-Anatomy declara estruturas ausentes e validação final pendente.",
            "O modelo representa anatomia masculina; modelo feminino completo ainda não está disponível na fonte.",
        ],
    }


def load_atlas(
    data_dir: Path | None = None,
    progress: ProgressCallback | None = None,
) -> AtlasModel:
    root = data_dir or installed_data_dir()
    if root is None or not is_installed(root):
        raise FileNotFoundError("O atlas moderno Z-Anatomy ainda não foi instalado")
    ta2 = _read_ta2(root / "TA2.csv")
    lexicon = json.loads((root / "lexicon.json").read_text(encoding="utf-8"))
    definitions = json.loads((root / "definitions.json").read_text(encoding="utf-8"))
    meshes: dict[str, pv.PolyData] = {}
    colors: dict[str, str] = {}
    structures: list[Structure] = []
    completed = 0

    for source_file in SYSTEM_FILES:
        document, binary = _read_glb(root / source_file.name)
        transforms = _world_matrices(document)
        decoded: dict[int, tuple[np.ndarray, np.ndarray, np.ndarray | None, str]] = {}
        for node_index, node in enumerate(document.get("nodes", [])):
            if "mesh" not in node:
                continue
            mesh_index = int(node["mesh"])
            if mesh_index not in decoded:
                decoded[mesh_index] = _decode_mesh(document, binary, mesh_index)
            points, triangles, normals, color = decoded[mesh_index]
            raw_name = node.get("extras", {}).get("za_name") or node.get("name", "Estrutura sem nome")
            structure = _structure(source_file, raw_name, ta2, lexicon, definitions)
            meshes[structure.id] = _polydata(
                points,
                triangles,
                normals,
                GLTF_TO_APP @ transforms[node_index],
            )
            colors[structure.id] = color
            structures.append(structure)
            completed += 1
            if progress:
                progress(completed, STRUCTURE_COUNT, raw_name)

    if len(meshes) != STRUCTURE_COUNT:
        raise ValueError(
            f"A revisão esperava {STRUCTURE_COUNT} estruturas, mas carregou {len(meshes)}"
        )
    report = coverage_report(root)
    coverage = (
        f"{len(meshes)} malhas em 7 sistemas; "
        f"{report['ta2_match_percent']}% dos itens associados automaticamente à TA2. "
        "Lacunas e ressalvas da fonte permanecem visíveis no relatório de cobertura."
    )
    return AtlasModel(
        meshes=meshes,
        structures=tuple(structures),
        label=f"Z-Anatomy {ATLAS_VERSION}",
        version=ATLAS_VERSION,
        source="https://github.com/Z-Anatomy/Models-of-human-anatomy",
        license_name=LICENSE_SUMMARY,
        attribution=ATTRIBUTION,
        revision=f"export {EXPORT_COMMIT[:12]}; terminologia {TERMINOLOGY_COMMIT[:12]}",
        coverage_note=coverage,
        colors=colors,
    )


def _console_progress(completed: int, total: int, name: str) -> None:
    percentage = min(100, completed * 100 // total)
    print(f"\r{percentage:3d}% — {name[:60]:60}", end="", flush=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gerencia o atlas moderno Z-Anatomy")
    parser.add_argument("ação", choices=("instalar", "verificar", "status", "relatorio"))
    parser.add_argument("--destino", type=Path, default=BUNDLED_DATA_DIR)
    args = parser.parse_args(argv)
    if args.ação == "instalar":
        install(args.destino, _console_progress)
        print(f"\nAtlas instalado em {args.destino}")
    elif args.ação == "verificar":
        verify_files(args.destino)
        print(f"Atlas íntegro: {args.destino}")
    elif args.ação == "relatorio":
        print(json.dumps(coverage_report(args.destino), ensure_ascii=False, indent=2))
    else:
        present = sum((args.destino / item.name).is_file() for item in SOURCE_FILES)
        print(f"Arquivos: {present}/{len(SOURCE_FILES)}")
        print(f"Estruturas esperadas: {STRUCTURE_COUNT}")
        print(f"Instalado: {'sim' if is_installed(args.destino) else 'não'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
