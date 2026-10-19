from __future__ import annotations

from dataclasses import dataclass, field

import pyvista as pv

from .catalog import Structure


@dataclass(slots=True)
class AtlasModel:
    """A versioned anatomical dataset ready to be displayed by the app."""

    meshes: dict[str, pv.PolyData]
    structures: tuple[Structure, ...]
    label: str
    version: str
    source: str
    license_name: str
    attribution: str
    revision: str
    coverage_note: str
    colors: dict[str, str] = field(default_factory=dict)

    @property
    def catalog(self) -> dict[str, Structure]:
        return {structure.id: structure for structure in self.structures}

    @property
    def structure_count(self) -> int:
        return len(self.meshes)
