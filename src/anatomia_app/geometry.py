from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pyvista as pv


BONE_COLOR = "#e8dfc8"
MUSCLE_COLOR = "#b5413e"


def capsule(start: tuple[float, float, float], end: tuple[float, float, float], radius: float) -> pv.PolyData:
    """Create a simple bone/muscle-shaped capsule between two points."""
    first = np.asarray(start, dtype=float)
    second = np.asarray(end, dtype=float)
    vector = second - first
    length = float(np.linalg.norm(vector))
    center = (first + second) / 2
    shaft = pv.Cylinder(center=center, direction=vector, radius=radius, height=length, resolution=24)
    return shaft.merge(pv.Sphere(radius=radius, center=first)).merge(
        pv.Sphere(radius=radius, center=second)
    )


def ellipsoid(center: tuple[float, float, float], radii: tuple[float, float, float]) -> pv.PolyData:
    mesh = pv.Sphere(radius=1.0, theta_resolution=32, phi_resolution=24)
    mesh.points *= np.asarray(radii)
    mesh.translate(center, inplace=True)
    return mesh


def merge(parts: Iterable[pv.PolyData]) -> pv.PolyData:
    items = list(parts)
    if not items:
        raise ValueError("É necessário fornecer ao menos uma malha")
    result = items[0]
    for part in items[1:]:
        result = result.merge(part)
    return result


def _ribs() -> pv.PolyData:
    ribs: list[pv.PolyData] = []
    for index, z in enumerate(np.linspace(0.55, 1.55, 8)):
        width = 0.53 - abs(index - 3.5) * 0.035
        depth = 0.26
        for side in (-1, 1):
            points = np.array([
                [0.05 * side, 0.11, z],
                [0.30 * side, 0.20, z + 0.02],
                [width * side, 0.02, z],
                [0.34 * side, -depth, z - 0.08],
                [0.08 * side, -0.29, z - 0.10],
            ])
            ribs.append(pv.Spline(points, 50).tube(radius=0.025))
    return merge(ribs)


def build_demo_meshes() -> dict[str, pv.PolyData]:
    """Return a simplified teaching model, with one independently selectable mesh per entry."""
    meshes: dict[str, pv.PolyData] = {
        "cranio": ellipsoid((0, 0, 2.55), (0.37, 0.32, 0.45)),
        "coluna": capsule((0, 0.13, -0.05), (0, 0.13, 2.12), 0.075),
        "costelas": _ribs(),
        "esterno": capsule((0, -0.30, 0.57), (0, -0.30, 1.52), 0.055),
        "pelve": merge((
            ellipsoid((-0.28, 0, -0.17), (0.35, 0.25, 0.32)),
            ellipsoid((0.28, 0, -0.17), (0.35, 0.25, 0.32)),
            capsule((-0.35, 0, -0.26), (0.35, 0, -0.26), 0.07),
        )),
        "umero_d": capsule((-0.62, 0, 1.67), (-0.78, 0, 0.80), 0.075),
        "umero_e": capsule((0.62, 0, 1.67), (0.78, 0, 0.80), 0.075),
        "antebraco_d": merge((
            capsule((-0.81, -0.02, 0.73), (-0.88, -0.03, -0.03), 0.045),
            capsule((-0.74, 0.05, 0.73), (-0.77, 0.05, -0.03), 0.04),
        )),
        "antebraco_e": merge((
            capsule((0.81, -0.02, 0.73), (0.88, -0.03, -0.03), 0.045),
            capsule((0.74, 0.05, 0.73), (0.77, 0.05, -0.03), 0.04),
        )),
        "femur_d": capsule((-0.29, 0, -0.36), (-0.34, 0, -1.48), 0.09),
        "femur_e": capsule((0.29, 0, -0.36), (0.34, 0, -1.48), 0.09),
        "perna_d": merge((
            capsule((-0.34, 0, -1.57), (-0.37, 0, -2.55), 0.065),
            capsule((-0.45, 0.02, -1.57), (-0.47, 0.02, -2.51), 0.035),
        )),
        "perna_e": merge((
            capsule((0.34, 0, -1.57), (0.37, 0, -2.55), 0.065),
            capsule((0.45, 0.02, -1.57), (0.47, 0.02, -2.51), 0.035),
        )),
        "deltoide_d": ellipsoid((-0.64, -0.02, 1.68), (0.20, 0.22, 0.31)),
        "deltoide_e": ellipsoid((0.64, -0.02, 1.68), (0.20, 0.22, 0.31)),
        "biceps_d": capsule((-0.69, -0.14, 1.50), (-0.78, -0.14, 0.91), 0.105),
        "biceps_e": capsule((0.69, -0.14, 1.50), (0.78, -0.14, 0.91), 0.105),
        "peitoral": merge((
            ellipsoid((-0.25, -0.28, 1.35), (0.32, 0.10, 0.38)),
            ellipsoid((0.25, -0.28, 1.35), (0.32, 0.10, 0.38)),
        )),
        "quadriceps_d": capsule((-0.30, -0.13, -0.52), (-0.34, -0.13, -1.36), 0.13),
        "quadriceps_e": capsule((0.30, -0.13, -0.52), (0.34, -0.13, -1.36), 0.13),
    }
    return meshes
