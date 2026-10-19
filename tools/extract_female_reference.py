"""Extract the pinned HRA female reproductive subset into a compact asset."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

import numpy as np


SOURCE_SHA256 = "472567a56896b9b7890508da6501fbf858e56aaa30745365f7a71ade782b529c"
MESH_GROUPS = {
    "hra_f_vagina": range(403, 405),
    "hra_f_tuba_d": range(405, 409),
    "hra_f_tuba_e": range(409, 413),
    "hra_f_recesso_uterovesical": (413,),
    "hra_f_lig_redondo_d": (414,),
    "hra_f_lig_redondo_e": (415,),
    "hra_f_lig_uterosacrais": (416, 417),
    "hra_f_lig_cardinais": (418, 419),
    "hra_f_lig_susp_ovarios": (420, 421),
    "hra_f_lig_proprios_ovarios": (422, 423),
    "hra_f_lig_largo": (424,),
    "hra_f_mesossalpinge": (425, 426),
    "hra_f_mesovario": (427, 428),
    "hra_f_ovario_e": (429,),
    "hra_f_ovario_d": (430,),
    "hra_f_utero": range(431, 441),
    "hra_f_art_uterina_e": (603,),
    "hra_f_art_uterina_d": (604,),
    "hra_f_veia_uterina_e": (605,),
    "hra_f_veia_uterina_d": (606,),
}
COMPONENT_TYPES = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
COMPONENT_COUNTS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}
# Uniform pelvic registration derived from the HRA and Z-Anatomy bony-pelvis
# envelopes. It preserves the source proportions rather than deforming organs.
SCALE = 0.9
TRANSLATION = np.asarray((0.0077, -0.0670, 0.8520), dtype=np.float64)


def read_glb(path: Path) -> tuple[dict, bytes]:
    with path.open("rb") as source:
        magic, version, _length = struct.unpack("<III", source.read(12))
        if magic != 0x46546C67 or version != 2:
            raise ValueError("A fonte não é um GLB 2.0 válido")
        json_length, json_kind = struct.unpack("<II", source.read(8))
        if json_kind != 0x4E4F534A:
            raise ValueError("GLB sem bloco JSON inicial")
        document = json.loads(source.read(json_length))
        binary_length, binary_kind = struct.unpack("<II", source.read(8))
        if binary_kind != 0x004E4942:
            raise ValueError("GLB sem bloco binário")
        return document, source.read(binary_length)


def accessor(document: dict, binary: bytes, index: int) -> np.ndarray:
    item = document["accessors"][index]
    view = document["bufferViews"][item["bufferView"]]
    dtype = np.dtype(COMPONENT_TYPES[item["componentType"]]).newbyteorder("<")
    width = COMPONENT_COUNTS[item["type"]]
    offset = view.get("byteOffset", 0) + item.get("byteOffset", 0)
    stride = view.get("byteStride", dtype.itemsize * width)
    return np.ndarray(
        (item["count"], width), dtype=dtype, buffer=binary, offset=offset,
        strides=(stride, dtype.itemsize),
    ).copy()


def extract(source: Path, destination: Path) -> None:
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != SOURCE_SHA256:
        raise ValueError(f"SHA-256 inesperado para a fonte HRA: {digest}")
    document, binary = read_glb(source)
    mesh_nodes = {int(node["mesh"]): node for node in document["nodes"] if "mesh" in node}
    arrays: dict[str, np.ndarray] = {}
    for identifier, mesh_indices in MESH_GROUPS.items():
        point_parts: list[np.ndarray] = []
        face_parts: list[np.ndarray] = []
        point_offset = 0
        for mesh_index in mesh_indices:
            node = mesh_nodes[mesh_index]
            if node.get("matrix") or node.get("rotation") or node.get("scale") or node.get("translation"):
                raise ValueError(f"Transformação inesperada no nó da malha {mesh_index}")
            for primitive in document["meshes"][mesh_index]["primitives"]:
                points = accessor(document, binary, primitive["attributes"]["POSITION"]).astype(np.float64)
                triangles = accessor(document, binary, primitive["indices"]).reshape((-1, 3)).astype(np.int64)
                # HRA [x, y, z] -> app [x, -z, y], followed by pelvic registration.
                points = np.column_stack((points[:, 0], -points[:, 2], points[:, 1]))
                points = points * SCALE + TRANSLATION
                point_parts.append(points.astype(np.float32))
                face_parts.append((triangles + point_offset).astype(np.int32))
                point_offset += len(points)
        arrays[f"{identifier}_points"] = np.vstack(point_parts)
        arrays[f"{identifier}_faces"] = np.vstack(face_parts)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as output:
        np.savez_compressed(output, **arrays)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, default=Path("src/anatomia_app/data/female_reproductive_v1_5.npz"))
    args = parser.parse_args()
    extract(args.source, args.output)
    print(f"Referência feminina gerada: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
