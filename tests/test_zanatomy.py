import json
import struct

import DracoPy
import numpy as np
import pytest

from anatomia_app.zanatomy import (
    GLTF_TO_APP,
    SOURCE_FILES,
    STRUCTURE_COUNT,
    _base_name,
    _decode_mesh,
    _polydata,
    _read_glb,
    _read_ta2,
    _world_matrices,
)


def _glb_chunk(payload: bytes, kind: int, padding: bytes) -> bytes:
    padded = payload + padding * ((-len(payload)) % 4)
    return struct.pack("<II", len(padded), kind) + padded


def _write_test_glb(path) -> None:
    compressed = DracoPy.encode(
        np.asarray(((0, 0, 0), (1, 0, 0), (0, 1, 0)), dtype=np.float32),
        np.asarray(((0, 1, 2),), dtype=np.uint32),
    )
    document = {
        "asset": {"version": "2.0"},
        "extensionsRequired": ["KHR_draco_mesh_compression"],
        "buffers": [{"byteLength": len(compressed)}],
        "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": len(compressed)}],
        "materials": [
            {"pbrMetallicRoughness": {"baseColorFactor": [1.0, 0.25, 0.0, 1.0]}}
        ],
        "meshes": [
            {
                "primitives": [
                    {
                        "material": 0,
                        "extensions": {
                            "KHR_draco_mesh_compression": {
                                "bufferView": 0,
                                "attributes": {"POSITION": 0},
                            }
                        },
                    }
                ]
            }
        ],
        "nodes": [
            {"children": [1], "translation": [0, 2, 0]},
            {"mesh": 0, "translation": [1, 0, 3], "extras": {"za_name": "Test.l"}},
        ],
    }
    json_payload = json.dumps(document, separators=(",", ":")).encode()
    body = _glb_chunk(json_payload, 0x4E4F534A, b" ") + _glb_chunk(
        compressed, 0x004E4942, b"\x00"
    )
    path.write_bytes(struct.pack("<III", 0x46546C67, 2, 12 + len(body)) + body)


def test_source_manifest_is_pinned_and_complete() -> None:
    assert STRUCTURE_COUNT == 2827
    assert len([item for item in SOURCE_FILES if item.system]) == 7
    assert all(len(item.sha256) == 64 and item.size > 0 for item in SOURCE_FILES)
    assert all("/8ca3b742" in item.url for item in SOURCE_FILES if item.name != "TA2.csv")


def test_ta2_reader_supports_quoted_semicolon_export(tmp_path) -> None:
    table = tmp_path / "TA2.csv"
    table.write_text(
        '\ufeff\n"TA2ID;English;Latin;Français;Español;Portugues;Italiano;Parsi"\n'
        '"2464;Biceps brachii muscle;Musculus biceps brachii;;;Músculo bíceps braquial;;"\n',
        encoding="utf-8",
    )

    terms = _read_ta2(table)

    assert terms["biceps brachii muscle"]["Portugues"] == "Músculo bíceps braquial"


def test_decodes_draco_and_applies_hierarchy_and_app_orientation(tmp_path) -> None:
    path = tmp_path / "tiny.glb"
    _write_test_glb(path)
    document, binary = _read_glb(path)
    matrices = _world_matrices(document)
    points, faces, normals, color = _decode_mesh(document, binary, 0)

    mesh = _polydata(points, faces, normals, GLTF_TO_APP @ matrices[1])

    assert mesh.n_points == 3
    assert mesh.n_cells == 1
    assert color == "#ff4000"
    # Source translation [1, 2, 3] becomes app coordinates [1, -3, 2].
    assert mesh.points.min(axis=0) == pytest.approx((1, -3, 2))


@pytest.mark.parametrize(
    ("raw", "base", "side"),
    (("Kidney.l", "Kidney", "esquerdo"), ("Heart", "Heart", ""), ("Ulna.r", "Ulna", "direito")),
)
def test_laterality_suffix(raw, base, side) -> None:
    assert _base_name(raw) == (base, side)
