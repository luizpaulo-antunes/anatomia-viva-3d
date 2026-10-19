from __future__ import annotations

from html import escape

import pyvista as pv
from pyvistaqt import QtInteractor
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor, QPalette
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QSlider,
    QSplitter,
    QTextBrowser,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)
from vtkmodules.vtkCommonDataModel import vtkPlanes
from vtkmodules.vtkFiltersGeneral import vtkExtractSelectedFrustum

from .atlas import AtlasModel
from .catalog import STRUCTURES, Structure
from .bodyparts3d import current_attribution, is_installed, load_meshes, model_label
from .geometry import BONE_COLOR, MUSCLE_COLOR, build_demo_meshes
from .female_reference import add_female_reference
from .zanatomy import (
    ATLAS_VERSION,
    TOTAL_DOWNLOAD_SIZE,
    USER_DATA_DIR,
    build_lod_cache,
    install as install_zanatomy,
    installed_data_dir as installed_zanatomy_dir,
    load_atlas as load_zanatomy,
    recommended_cell_limit,
)


FOCUS_CONTEXT_OPACITY = 0.16
# Used by the compatibility fallback when there is no complete-body frame.
FOCUS_PADDING_RATIO = 0.384
# Minimum camera windows relative to the complete model.  They stop a tiny
# nerve, vessel, or facial bone from filling the viewport while retaining an
# anatomically useful amount of context.
FOCUS_REGION_PROFILES = {
    "Cabeça": (0.48, 0.86, 0.23, 0.90),
    "Pescoço": (0.46, 0.84, 0.20, 0.80),
    "Tórax": (0.62, 0.92, 0.34, 0.67),
    "Abdome": (0.56, 0.92, 0.30, 0.49),
    "Pelve e períneo": (0.54, 0.90, 0.28, 0.35),
    "Ombro": (0.48, 0.86, 0.30, 0.76),
    "Membro superior": (0.40, 0.84, 0.30, None),
    "Membro inferior": (0.36, 0.84, 0.32, None),
    "Dorso e coluna": (0.56, 0.92, 0.36, None),
    "Não especificada": (0.42, 0.86, 0.30, None),
}
SYSTEM_COLORS = {
    "Sistema esquelético": BONE_COLOR,
    "Articulações, ligamentos e fáscias": "#6ec5bd",
    "Sistema muscular": MUSCLE_COLOR,
    "Sistema cardiovascular": "#c74646",
    "Sistema linfático": "#6cad72",
    "Sistema nervoso": "#e6c85c",
    "Órgãos e vísceras": "#b57aa6",
}


def anatomical_profile_allows(structure: Structure, profile: str) -> bool:
    structure_profile = getattr(structure, "anatomical_profile", "comum")
    return (
        structure_profile == "comum"
        or profile == "ambos"
        or structure_profile == profile
    )


class StructureActor:
    """Small compatibility facade over one VTK composite block."""

    def __init__(self, attributes) -> None:
        self.attributes = attributes

    @property
    def prop(self) -> StructureActor:
        return self

    @property
    def visibility(self) -> bool:
        value = self.attributes.visible
        return True if value is None else bool(value)

    @visibility.setter
    def visibility(self, value: bool) -> None:
        self.attributes.visible = value

    @property
    def color(self):
        return self.attributes.color

    @color.setter
    def color(self, value) -> None:
        self.attributes.color = value

    @property
    def opacity(self) -> float:
        value = self.attributes.opacity
        return 1.0 if value is None else float(value)

    @opacity.setter
    def opacity(self, value: float) -> None:
        self.attributes.opacity = value


def combined_bounds(meshes) -> tuple[float, float, float, float, float, float]:
    """Return bounds containing every supplied mesh."""
    bounds = [tuple(float(value) for value in mesh.bounds) for mesh in meshes]
    if not bounds:
        raise ValueError("Não há malhas para calcular o enquadramento.")
    return (
        min(item[0] for item in bounds),
        max(item[1] for item in bounds),
        min(item[2] for item in bounds),
        max(item[3] for item in bounds),
        min(item[4] for item in bounds),
        max(item[5] for item in bounds),
    )


def bounds_intersect(
    first: tuple[float, float, float, float, float, float],
    second: tuple[float, float, float, float, float, float],
) -> bool:
    """Return whether two 3D bounds overlap or touch."""
    return not (
        first[1] < second[0]
        or first[0] > second[1]
        or first[3] < second[2]
        or first[2] > second[3]
        or first[5] < second[4]
        or first[4] > second[5]
    )


def local_focus_bounds(
    mesh: pv.PolyData,
    scene_bounds: tuple[float, float, float, float, float, float],
) -> tuple[float, float, float, float, float, float]:
    """Return a local 3D neighborhood around the selected anatomy."""
    bounds = tuple(float(value) for value in mesh.bounds)
    scene_spans = (
        scene_bounds[1] - scene_bounds[0],
        scene_bounds[3] - scene_bounds[2],
        scene_bounds[5] - scene_bounds[4],
    )
    selected_spans = (
        bounds[1] - bounds[0],
        bounds[3] - bounds[2],
        bounds[5] - bounds[4],
    )
    padding = (
        max(selected_spans[0] * 0.35, scene_spans[0] * 0.04),
        max(selected_spans[1] * 0.35, scene_spans[1] * 0.10),
        max(selected_spans[2] * 0.35, scene_spans[2] * 0.03),
    )
    return (
        bounds[0] - padding[0],
        bounds[1] + padding[0],
        bounds[2] - padding[1],
        bounds[3] + padding[1],
        bounds[4] - padding[2],
        bounds[5] + padding[2],
    )


def is_focus_context_structure(
    structure_id: str,
    structure: Structure,
    mesh: pv.PolyData,
    selected_id: str,
    focus_bounds: tuple[float, float, float, float, float, float],
) -> bool:
    """Keep only nearby bones as a clean landmark for a selection."""
    return (
        structure_id != selected_id
        and structure.system == "Sistema esquelético"
        and bounds_intersect(tuple(float(value) for value in mesh.bounds), focus_bounds)
    )


def _normalized_region(region: str) -> str:
    value = region.casefold()
    if "cabeça" in value or "face" in value or "crân" in value:
        return "Cabeça"
    if "pescoço" in value or "cervical" in value:
        return "Pescoço"
    if "tórax" in value or "torác" in value:
        return "Tórax"
    if "abd" in value:
        return "Abdome"
    if "pelv" in value or "períneo" in value:
        return "Pelve e períneo"
    if "ombro" in value or "escapular" in value:
        return "Ombro"
    if any(term in value for term in ("superior", "braço", "antebraço", "mão")):
        return "Membro superior"
    if any(term in value for term in ("inferior", "coxa", "perna", "pé")):
        return "Membro inferior"
    if "dorso" in value or "coluna" in value or "lombar" in value:
        return "Dorso e coluna"
    return "Não especificada"


def camera_focus_bounds(
    mesh: pv.PolyData,
    scene_bounds: tuple[float, float, float, float, float, float] | None = None,
    region: str = "",
) -> tuple[float, float, float, float, float, float]:
    """Frame a selected structure without losing its anatomical context.

    With complete-scene bounds, the smallest possible frame is a stable body
    region rather than the selected mesh itself.  The one-argument behavior is
    kept as a fallback for old/demo data with no scene context.
    """
    bounds = tuple(float(value) for value in mesh.bounds)
    spans = (
        bounds[1] - bounds[0],
        bounds[3] - bounds[2],
        bounds[5] - bounds[4],
    )
    padding = max(max(spans) * FOCUS_PADDING_RATIO, 0.02)
    padded = (
        bounds[0] - padding,
        bounds[1] + padding,
        bounds[2] - padding,
        bounds[3] + padding,
        bounds[4] - padding,
        bounds[5] + padding,
    )
    if scene_bounds is None:
        return padded

    scene = tuple(float(value) for value in scene_bounds)
    scene_spans = (
        max(scene[1] - scene[0], 0.001),
        max(scene[3] - scene[2], 0.001),
        max(scene[5] - scene[4], 0.001),
    )
    scene_centers = (
        (scene[0] + scene[1]) / 2,
        (scene[2] + scene[3]) / 2,
        (scene[4] + scene[5]) / 2,
    )
    selected_centers = (
        (bounds[0] + bounds[1]) / 2,
        (bounds[2] + bounds[3]) / 2,
        (bounds[4] + bounds[5]) / 2,
    )
    normalized_region = _normalized_region(region)
    x_ratio, y_ratio, z_ratio, z_anchor = FOCUS_REGION_PROFILES[normalized_region]

    # Central regions use a stable anatomical anchor when the classification
    # agrees with the mesh position. Misclassified source objects receive a
    # local frame, avoiding a jump across half the body.
    center_x = selected_centers[0]
    if normalized_region in {
        "Cabeça",
        "Pescoço",
        "Tórax",
        "Abdome",
        "Pelve e períneo",
        "Dorso e coluna",
    } and abs(selected_centers[0] - scene_centers[0]) <= scene_spans[0] * 0.32:
        center_x = scene_centers[0]

    center_z = selected_centers[2]
    if z_anchor is not None:
        anchored_z = scene[4] + scene_spans[2] * z_anchor
        anchor_tolerance = scene_spans[2] * (z_ratio / 2 + 0.08)
        if abs(selected_centers[2] - anchored_z) <= anchor_tolerance:
            center_z = anchored_z

    desired_spans = (
        scene_spans[0] * x_ratio,
        scene_spans[1] * y_ratio,
        scene_spans[2] * z_ratio,
    )
    selected_padding = (
        max(spans[0] * 0.12, scene_spans[0] * 0.01),
        max(spans[1] * 0.12, scene_spans[1] * 0.01),
        max(spans[2] * 0.12, scene_spans[2] * 0.01),
    )
    selected_padded = (
        bounds[0] - selected_padding[0],
        bounds[1] + selected_padding[0],
        bounds[2] - selected_padding[1],
        bounds[3] + selected_padding[1],
        bounds[4] - selected_padding[2],
        bounds[5] + selected_padding[2],
    )
    contextual = (
        center_x - desired_spans[0] / 2,
        center_x + desired_spans[0] / 2,
        selected_centers[1] - desired_spans[1] / 2,
        selected_centers[1] + desired_spans[1] / 2,
        center_z - desired_spans[2] / 2,
        center_z + desired_spans[2] / 2,
    )
    return (
        min(contextual[0], selected_padded[0]),
        max(contextual[1], selected_padded[1]),
        min(contextual[2], selected_padded[2]),
        max(contextual[3], selected_padded[3]),
        min(contextual[4], selected_padded[4]),
        max(contextual[5], selected_padded[5]),
    )


class AnatomyWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Anatomia Viva 3D — Atlas de Anatomia")
        self.resize(1400, 850)

        self.render_cell_limit = recommended_cell_limit()
        self.atlas = self._load_initial_model(self.render_cell_limit)
        self.meshes = self.atlas.meshes
        self.scene_bounds = combined_bounds(self.meshes.values())
        self.structures = self.atlas.structures
        self.catalog = self.atlas.catalog
        self.model_source = self.atlas.label
        self.colors = self.atlas.colors
        self.actors: dict[str, StructureActor] = {}
        self.block_ids: dict[int, str] = {}
        self.structure_opacities: dict[str, float] = {}
        self.items: dict[str, QTreeWidgetItem] = {}
        self.selected_id: str | None = None
        self.atlas_actor = None
        self.selection_actor = None
        self.selection_outline_actor = None
        self.selection_focus_active = False
        self.active_focus_bounds = None
        self.active_filter_bounds = None
        self.focus_context_ids: set[str] | None = None
        self.anatomical_profile = "masculino"
        self._tree_updating = False

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_navigation_panel())
        splitter.addWidget(self._build_viewport())
        splitter.addWidget(self._build_information_panel())
        splitter.setSizes([270, 820, 310])
        self.setCentralWidget(splitter)

        self._create_toolbar()
        self._populate_scene()
        self._populate_tree()
        self._show_welcome()
        self.statusBar().showMessage("Clique em uma estrutura para estudá-la")

    @staticmethod
    def _legacy_atlas(meshes: dict[str, pv.PolyData], label: str) -> AtlasModel:
        structures = tuple(item for item in STRUCTURES if item.id in meshes)
        is_demo = label == "Demonstração"
        return AtlasModel(
            meshes=meshes,
            structures=structures,
            label=label,
            version="demo" if is_demo else label.removeprefix("BodyParts3D "),
            source="modelo procedural interno" if is_demo else "BodyParts3D",
            license_name="MIT (geometria procedural)" if is_demo else "Consulte THIRD_PARTY_LICENSES.md",
            attribution="Anatomia Viva 3D" if is_demo else current_attribution(),
            revision="incluída no aplicativo",
            coverage_note=(
                "Representação simplificada para demonstração; não é um atlas anatômico completo."
                if is_demo
                else "Modelo legado mantido apenas para compatibilidade."
            ),
        )

    @classmethod
    def _load_initial_model(cls, max_cells_per_structure: int | None = None) -> AtlasModel:
        modern = installed_zanatomy_dir()
        if modern is not None:
            try:
                return add_female_reference(
                    load_zanatomy(
                        modern,
                        max_cells_per_structure=max_cells_per_structure,
                    )
                )
            except (OSError, RuntimeError, ValueError):
                pass
        if is_installed():
            try:
                return cls._legacy_atlas(load_meshes(), model_label())
            except (OSError, RuntimeError, ValueError):
                pass
        return cls._legacy_atlas(build_demo_meshes(), "Demonstração")

    def _build_navigation_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        title = QLabel("Estruturas anatômicas")
        title.setObjectName("panelTitle")
        layout.addWidget(title)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Pesquisar nome ou termo latino…")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._filter_tree)
        layout.addWidget(self.search)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tree.itemSelectionChanged.connect(self._on_tree_selection)
        self.tree.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self.tree, 1)

        hint = QLabel("☑ exibe/oculta  •  clique seleciona")
        hint.setObjectName("hint")
        layout.addWidget(hint)
        panel.setMinimumWidth(235)
        return panel

    def _build_viewport(self) -> QWidget:
        frame = QFrame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        self.plotter = QtInteractor(frame)
        if self.render_cell_limit is not None:
            self.plotter.render_window.SetMultiSamples(0)
        self.plotter.set_background("#131820", top="#293341")
        if self.plotter.iren is not None:
            self.plotter.enable_trackball_style()
            self.plotter.add_key_event("+", self._zoom_in)
            self.plotter.add_key_event("=", self._zoom_in)
            self.plotter.add_key_event("-", self._zoom_out)
            self.plotter.add_key_event("f", self._reset_camera)
        layout.addWidget(self.plotter.interactor)
        controls = QLabel(
            "Arraste: girar  •  botão direito: mover  •  roda ou +/−: zoom  •  F: reenquadrar"
        )
        controls.setObjectName("viewportHint")
        controls.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(controls)
        return frame

    def _build_information_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        title = QLabel("Informações")
        title.setObjectName("panelTitle")
        layout.addWidget(title)

        self.details = QTextBrowser()
        self.details.setOpenExternalLinks(True)
        layout.addWidget(self.details, 1)

        layout.addWidget(QLabel("Opacidade da estrutura selecionada"))
        self.opacity = QSlider(Qt.Orientation.Horizontal)
        self.opacity.setRange(10, 100)
        self.opacity.setValue(100)
        self.opacity.setEnabled(False)
        self.opacity.valueChanged.connect(self._set_selected_opacity)
        layout.addWidget(self.opacity)

        row = QHBoxLayout()
        isolate = QPushButton("Isolar")
        isolate.clicked.connect(self._isolate_selected)
        hide = QPushButton("Ocultar")
        hide.clicked.connect(self._hide_selected)
        row.addWidget(isolate)
        row.addWidget(hide)
        layout.addLayout(row)

        show_all = QPushButton("Exibir todas as estruturas")
        show_all.clicked.connect(self._show_all)
        layout.addWidget(show_all)
        panel.setMinimumWidth(280)
        return panel

    def _create_toolbar(self) -> None:
        toolbar = self.addToolBar("Vistas")
        toolbar.setMovable(False)
        actions = (
            ("Anterior", self._view_front),
            ("Posterior", self._view_back),
            ("Lateral", self._view_side),
            ("Superior", self._view_top),
            ("Aproximar +", self._zoom_in),
            ("Afastar −", self._zoom_out),
            ("Reenquadrar", self._reset_camera),
        )
        for label, callback in actions:
            action = QAction(label, self)
            action.triggered.connect(callback)
            toolbar.addAction(action)
        toolbar.addSeparator()
        layers = (
            ("Tudo", None),
            ("Ossos", "Sistema esquelético"),
            ("Músculos", "Sistema muscular"),
            ("Vasos", "Sistema cardiovascular"),
            ("Nervos", "Sistema nervoso"),
            ("Órgãos", "Órgãos e vísceras"),
        )
        for label, system in layers:
            action = QAction(label, self)
            action.triggered.connect(lambda _checked=False, value=system: self._show_system(value))
            toolbar.addAction(action)
        toolbar.addSeparator()
        toolbar.addWidget(QLabel(" Perfil reprodutivo: "))
        self.profile_selector = QComboBox()
        self.profile_selector.addItem("Masculino", "masculino")
        self.profile_selector.addItem("Feminino", "feminino")
        self.profile_selector.addItem("Ambos (comparar)", "ambos")
        self.profile_selector.setToolTip(
            "Alterna somente as estruturas específicas dos sistemas reprodutivos; "
            "as estruturas comuns permanecem visíveis."
        )
        self.profile_selector.currentIndexChanged.connect(self._change_anatomical_profile)
        toolbar.addWidget(self.profile_selector)
        toolbar.addSeparator()
        profile = " • modo leve" if self.render_cell_limit is not None else ""
        self.model_badge = QLabel(f"  Modelo: {self.model_source}{profile}  ")
        toolbar.addWidget(self.model_badge)

        data_menu = self.menuBar().addMenu("Dados")
        update_content = QAction("Instalar/atualizar atlas moderno…", self)
        update_content.triggered.connect(self._update_anatomy_content)
        data_menu.addAction(update_content)
        data_menu.addSeparator()
        detailed = QAction("Usar modelo legado BodyParts3D", self)
        detailed.triggered.connect(self._use_detailed_model)
        data_menu.addAction(detailed)
        demo = QAction("Usar modelo de demonstração", self)
        demo.triggered.connect(self._use_demo_model)
        data_menu.addAction(demo)
        data_menu.addSeparator()
        credits = QAction("Fonte, cobertura e licenças", self)
        credits.triggered.connect(self._show_model_credits)
        data_menu.addAction(credits)

    def _populate_scene(self) -> None:
        blocks = pv.MultiBlock()
        identifiers: list[str] = []
        for structure in self.structures:
            if structure.id not in self.meshes:
                continue
            blocks.append(self.meshes[structure.id], structure.id)
            identifiers.append(structure.id)
            self.structure_opacities[structure.id] = 1.0

        self.atlas_actor, mapper = self.plotter.add_composite(
            blocks,
            name="atlas-anatomico",
            color=BONE_COLOR,
            smooth_shading=False,
            pickable=True,
            specular=0.15,
            specular_power=12,
            render=False,
        )
        for block_index, structure_id in enumerate(identifiers, start=1):
            attributes = mapper.block_attr[block_index]
            structure = self.catalog[structure_id]
            attributes.color = self.colors.get(
                structure_id,
                SYSTEM_COLORS.get(structure.system, MUSCLE_COLOR),
            )
            self.actors[structure_id] = StructureActor(attributes)
            attributes.visible = anatomical_profile_allows(
                structure, self.anatomical_profile
            )
            self.block_ids[block_index] = structure_id

        self.plotter.add_axes(line_width=2, labels_off=True)
        # Some CI/headless platforms can construct the scene but provide no
        # OpenGL interactor. The desktop application always has one.
        if self.plotter.iren is not None:
            self.plotter.enable_block_picking(callback=self._on_block_picked, side="left")
        self.plotter.render()
        self._view_front()

    def _populate_tree(self) -> None:
        groups: dict[str, QTreeWidgetItem] = {}
        regions: dict[tuple[str, str], QTreeWidgetItem] = {}
        self._tree_updating = True
        for structure in self.structures:
            if structure.id not in self.meshes:
                continue
            parent = groups.get(structure.system)
            if parent is None:
                parent = QTreeWidgetItem(self.tree, [structure.system])
                parent.setFlags(parent.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)
                groups[structure.system] = parent
            item_parent = parent
            if structure.region:
                region_key = (structure.system, structure.region)
                item_parent = regions.get(region_key)
                if item_parent is None:
                    item_parent = QTreeWidgetItem(parent, [structure.region])
                    item_parent.setFlags(item_parent.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)
                    regions[region_key] = item_parent
            item = QTreeWidgetItem(item_parent, [structure.name])
            item.setData(0, Qt.ItemDataRole.UserRole, structure.id)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                0,
                Qt.CheckState.Checked
                if anatomical_profile_allows(structure, self.anatomical_profile)
                else Qt.CheckState.Unchecked,
            )
            self.items[structure.id] = item
        self._tree_updating = False
        self.tree.expandToDepth(0)

    def _filter_tree(self, text: str) -> None:
        query = text.strip().casefold()

        def filter_item(item: QTreeWidgetItem) -> bool:
            structure_id = item.data(0, Qt.ItemDataRole.UserRole)
            if structure_id:
                structure = self.catalog[structure_id]
                visible = anatomical_profile_allows(
                    structure, self.anatomical_profile
                ) and (not query or query in structure.search_text)
            else:
                child_visibility = [
                    filter_item(item.child(index)) for index in range(item.childCount())
                ]
                visible = any(child_visibility)
            item.setHidden(not visible)
            return visible

        root = self.tree.invisibleRootItem()
        for index in range(root.childCount()):
            filter_item(root.child(index))
        if query:
            self.tree.expandAll()
        else:
            self.tree.collapseAll()
            self.tree.expandToDepth(0)

    def _on_tree_selection(self) -> None:
        selected = self.tree.selectedItems()
        if not selected:
            return
        structure_id = selected[0].data(0, Qt.ItemDataRole.UserRole)
        if structure_id:
            self._select_structure(structure_id)

    def _on_item_changed(self, item: QTreeWidgetItem, _column: int) -> None:
        if self._tree_updating:
            return
        structure_id = item.data(0, Qt.ItemDataRole.UserRole)
        if not structure_id:
            return
        if structure_id in self.actors:
            visible = (
                item.checkState(0) == Qt.CheckState.Checked
                and anatomical_profile_allows(
                    self.catalog[structure_id], self.anatomical_profile
                )
            )
            if self.focus_context_ids is not None:
                visible = visible and structure_id in self.focus_context_ids
            self.actors[structure_id].visibility = visible
        if (
            structure_id == self.selected_id
            and item.checkState(0) == Qt.CheckState.Unchecked
        ):
            self._restore_structure_opacities()
        self.plotter.render()

    def _on_block_picked(self, block_index: int, _dataset) -> None:
        structure_id = self.block_ids.get(block_index)
        if structure_id:
            item = self.items[structure_id]
            parent = item.parent()
            while parent is not None:
                parent.setExpanded(True)
                parent = parent.parent()
            self.tree.blockSignals(True)
            self.tree.setCurrentItem(item)
            self.tree.scrollToItem(item)
            self.tree.blockSignals(False)
            self._select_structure(structure_id)

    def _select_structure(self, structure_id: str) -> None:
        if self.selection_focus_active or self.focus_context_ids is not None:
            self._restore_structure_opacities()
        self.selected_id = structure_id
        actor = self.actors[structure_id]
        # The highlighted copy replaces this one block while focus is active.
        # This avoids drawing the selected surface twice and keeps the opacity
        # slider exact.
        self.active_focus_bounds = self._selected_focus_bounds()
        self.active_filter_bounds = local_focus_bounds(
            self.meshes[structure_id], self.scene_bounds
        )
        self.focus_context_ids = {
            identifier
            for identifier, structure in self.catalog.items()
            if identifier in self.meshes
            and anatomical_profile_allows(structure, self.anatomical_profile)
            and is_focus_context_structure(
                identifier,
                structure,
                self.meshes[identifier],
                structure_id,
                self.active_filter_bounds,
            )
        }
        for identifier, context_actor in self.actors.items():
            context_actor.visibility = (
                identifier in self.focus_context_ids
                and self.items[identifier].checkState(0) == Qt.CheckState.Checked
            )
        actor.visibility = False
        if self.atlas_actor is not None:
            self.atlas_actor.prop.opacity = FOCUS_CONTEXT_OPACITY
        self.selection_actor = self.plotter.add_mesh(
            self.meshes[structure_id],
            name="estrutura-selecionada",
            color="#ffd166",
            opacity=self.structure_opacities.get(structure_id, 1.0),
            smooth_shading=True,
            ambient=0.32,
            diffuse=0.78,
            specular=0.25,
            specular_power=18,
            pickable=False,
            render=False,
        )
        self.selection_outline_actor = self.plotter.add_silhouette(
            self.meshes[structure_id],
            color="#fff4c2",
            line_width=4,
            opacity=0.95,
            decimate=0.5,
        )
        self.selection_focus_active = True
        self._tree_updating = True
        self.items[structure_id].setCheckState(0, Qt.CheckState.Checked)
        self._tree_updating = False
        self.opacity.setEnabled(True)
        self.opacity.blockSignals(True)
        self.opacity.setValue(round(self.structure_opacities.get(structure_id, 1.0) * 100))
        self.opacity.blockSignals(False)
        self._show_details(self.catalog[structure_id])
        structure = self.catalog[structure_id]
        region = structure.region or "região local"
        self.statusBar().showMessage(
            f"Selecionado: {structure.name} • enquadramento: {region}"
        )
        self.plotter.reset_camera(bounds=self.active_focus_bounds, render=False)
        self.plotter.render()

    def _show_details(self, structure: Structure) -> None:
        extra = "".join(
            f"<p><b>{escape(label)}:</b> {escape(value)}</p>" for label, value in structure.details
        )
        self.details.setHtml(
            f"<h2>{escape(structure.name)}</h2>"
            f"<p><i>{escape(structure.latin_name)}</i></p>"
            f"<p><b>{escape(structure.system)}</b></p><hr>"
            f"<h3>Descrição</h3><p>{escape(structure.description)}</p>"
            f"<h3>Função</h3><p>{escape(structure.function)}</p>{extra}"
            "<hr><small>Conteúdo didático em português. Confirme detalhes clínicos em bibliografia médica revisada.</small>"
        )

    def _show_welcome(self) -> None:
        counts: dict[str, int] = {}
        for identifier in self.actors:
            system = self.catalog[identifier].system
            counts[system] = counts.get(system, 0) + 1
        coverage = " • ".join(f"{escape(name)}: {count}" for name, count in counts.items())
        self.details.setHtml(
            "<h2>Anatomia Viva 3D</h2>"
            "<p>Gire o modelo arrastando. Use a roda ou os botões +/− para controlar o zoom e clique em uma estrutura.</p>"
            "<p>Use a lista à esquerda para pesquisar, selecionar ou ocultar partes.</p>"
            f"<p><b>Atlas:</b> {escape(self.atlas.label)} — {len(self.actors)} estruturas.</p>"
            f"<p>{coverage}</p>"
            f"<p><b>Cobertura:</b> {escape(self.atlas.coverage_note)}</p>"
            "<hr><small>Atlas educacional. Não deve ser usado para diagnóstico ou planejamento clínico.</small>"
        )

    def _replace_model(self, atlas: AtlasModel) -> None:
        if atlas.label.startswith("Z-Anatomy") and not any(
            structure.anatomical_profile == "feminino"
            for structure in atlas.structures
        ):
            atlas = add_female_reference(atlas)
        if self.plotter.iren is not None:
            self.plotter.disable_picking()
        self.plotter.clear()
        self.atlas_actor = None
        self.selection_actor = None
        self.selection_outline_actor = None
        self.atlas = atlas
        self.meshes = atlas.meshes
        self.scene_bounds = combined_bounds(self.meshes.values())
        self.structures = atlas.structures
        self.catalog = atlas.catalog
        self.colors = atlas.colors
        self.model_source = atlas.label
        self.actors.clear()
        self.block_ids.clear()
        self.structure_opacities.clear()
        self.tree.clear()
        self.items.clear()
        self.selected_id = None
        self.selection_focus_active = False
        self.active_focus_bounds = None
        self.active_filter_bounds = None
        self.focus_context_ids = None
        self.opacity.setEnabled(False)
        self._populate_scene()
        self._populate_tree()
        self._show_all()
        self._show_welcome()
        profile = " • modo leve" if self.render_cell_limit is not None else ""
        self.model_badge.setText(f"  Modelo: {atlas.label}{profile}  ")
        self.statusBar().showMessage(f"Modelo ativo: {atlas.label}")

    def _use_detailed_model(self) -> None:
        if not is_installed():
            QMessageBox.information(
                self,
                "Modelo legado ainda não instalado",
                "Feche o aplicativo e execute no terminal:\n\n"
                "python -m anatomia_app.bodyparts3d instalar\n\n"
                "Esse fallback histórico ocupa cerca de 1 GB. O atlas moderno Z-Anatomy "
                "é a opção recomendada no menu Dados.",
            )
            return
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            self._replace_model(self._legacy_atlas(load_meshes(), model_label()))
        except (OSError, RuntimeError, ValueError) as error:
            QMessageBox.critical(self, "Erro ao carregar modelo", str(error))
        finally:
            QApplication.restoreOverrideCursor()

    def _use_demo_model(self) -> None:
        self._replace_model(self._legacy_atlas(build_demo_meshes(), "Demonstração"))

    def _update_anatomy_content(self) -> None:
        existing = installed_zanatomy_dir()
        if existing is not None:
            if self.atlas.label.startswith("Z-Anatomy"):
                QMessageBox.information(
                    self,
                    "Atlas moderno instalado",
                    f"A revisão Z-Anatomy {ATLAS_VERSION} já está instalada e íntegra, "
                    f"com {len(self.meshes)} estruturas carregadas. Novas revisões serão "
                    "publicadas junto às próximas versões do aplicativo.",
                )
                return
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                self._replace_model(
                    load_zanatomy(
                        existing,
                        max_cells_per_structure=self.render_cell_limit,
                    )
                )
            except (OSError, RuntimeError, ValueError) as error:
                QMessageBox.critical(self, "Falha ao carregar o atlas moderno", str(error))
            finally:
                QApplication.restoreOverrideCursor()
            return

        size_mb = TOTAL_DOWNLOAD_SIZE / (1024 * 1024)
        answer = QMessageBox.question(
            self,
            "Instalar atlas moderno",
            f"O atlas Z-Anatomy {ATLAS_VERSION} contém 2.827 estruturas em sete "
            f"sistemas e ocupa {size_mb:.0f} MB para download. Deseja instalar agora?",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        progress = QProgressDialog(
            "Baixando a biblioteca anatômica…",
            "Cancelar",
            0,
            TOTAL_DOWNLOAD_SIZE,
            self,
        )
        progress.setWindowTitle("Atualização de conteúdo")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)

        def report(downloaded: int, _total: int, name: str) -> None:
            progress.setLabelText(f"Baixando e validando {name}…")
            progress.setValue(downloaded)
            QApplication.processEvents()
            if progress.wasCanceled():
                raise InterruptedError("Atualização cancelada pelo usuário.")

        try:
            installed_dir = install_zanatomy(USER_DATA_DIR, progress=report)
            if self.render_cell_limit is not None:
                progress.setRange(0, 0)
                progress.setLabelText("Preparando o atlas para este computador…")
                QApplication.processEvents()

                def optimize_report(completed: int, total: int, name: str) -> None:
                    progress.setRange(0, total)
                    progress.setValue(completed)
                    progress.setLabelText(f"Otimizando {name} para vídeo integrado…")
                    QApplication.processEvents()
                    if progress.wasCanceled():
                        raise InterruptedError("Otimização cancelada pelo usuário.")

                build_lod_cache(
                    installed_dir,
                    self.render_cell_limit,
                    progress=optimize_report,
                )
            progress.setRange(0, 0)
            progress.setLabelText("Decodificando as 2.827 estruturas 3D…")
            QApplication.processEvents()
            atlas = load_zanatomy(
                installed_dir,
                max_cells_per_structure=self.render_cell_limit,
            )
            self._replace_model(atlas)
        except InterruptedError:
            self.statusBar().showMessage("Atualização da biblioteca cancelada")
            return
        except (OSError, RuntimeError, ValueError) as error:
            QMessageBox.critical(self, "Falha na atualização", str(error))
            return
        finally:
            progress.close()

        QMessageBox.information(
            self,
            "Biblioteca atualizada",
            f"O atlas Z-Anatomy {ATLAS_VERSION} foi instalado com 2.827 estruturas. "
            "A cobertura e as licenças podem ser consultadas no menu Dados.",
        )

    def _show_model_credits(self) -> None:
        QMessageBox.about(
            self,
            "Fonte, cobertura e licenças",
            f"Modelo: {self.atlas.label}\n"
            f"Versão: {self.atlas.version}\n"
            f"Revisão: {self.atlas.revision}\n\n"
            f"Cobertura: {self.atlas.coverage_note}\n\n"
            f"Atribuição: {self.atlas.attribution}\n"
            f"Licença: {self.atlas.license_name}\n"
            f"Fonte: {self.atlas.source}\n\n"
            "Consulte THIRD_PARTY_LICENSES.md e o relatório de cobertura. "
            "Nenhuma base aberta garante, sozinha, toda estrutura anatômica humana.",
        )

    def _set_selected_opacity(self, value: int) -> None:
        if self.selected_id:
            opacity = value / 100
            self.structure_opacities[self.selected_id] = opacity
            if self.selection_actor is not None:
                self.selection_actor.prop.opacity = opacity
            self.plotter.render()

    def _remove_selection_overlay(self) -> None:
        if self.selection_actor is not None:
            self.plotter.remove_actor(self.selection_actor, render=False)
            self.selection_actor = None
        if self.selection_outline_actor is not None:
            self.plotter.remove_actor(self.selection_outline_actor, render=False)
            self.selection_outline_actor = None

    def _restore_structure_opacities(self) -> None:
        if self.atlas_actor is not None:
            self.atlas_actor.prop.opacity = 1.0
        self._remove_selection_overlay()
        if self.focus_context_ids is not None:
            for structure_id, actor in self.actors.items():
                actor.visibility = (
                    self.items[structure_id].checkState(0) == Qt.CheckState.Checked
                    and anatomical_profile_allows(
                        self.catalog[structure_id], self.anatomical_profile
                    )
                )
            self.focus_context_ids = None
        elif self.selected_id in self.actors and self.selected_id in self.items:
            self.actors[self.selected_id].visibility = (
                self.items[self.selected_id].checkState(0) == Qt.CheckState.Checked
                and anatomical_profile_allows(
                    self.catalog[self.selected_id], self.anatomical_profile
                )
            )
        self.selection_focus_active = False
        self.opacity.setEnabled(False)

    def _isolate_selected(self) -> None:
        if not self.selected_id:
            return
        self._restore_structure_opacities()
        self._tree_updating = True
        for structure_id, actor in self.actors.items():
            visible = structure_id == self.selected_id
            actor.visibility = visible
            self.items[structure_id].setCheckState(
                0, Qt.CheckState.Checked if visible else Qt.CheckState.Unchecked
            )
        self._tree_updating = False
        self.plotter.render()

    def _hide_selected(self) -> None:
        if self.selected_id:
            self.items[self.selected_id].setCheckState(0, Qt.CheckState.Unchecked)
            self._restore_structure_opacities()
            self.plotter.render()

    def _show_all(self) -> None:
        self._restore_structure_opacities()
        self.active_focus_bounds = None
        self.active_filter_bounds = None
        self._tree_updating = True
        for structure_id, actor in self.actors.items():
            visible = anatomical_profile_allows(
                self.catalog[structure_id], self.anatomical_profile
            )
            actor.visibility = visible
            self.structure_opacities[structure_id] = 1.0
            self.items[structure_id].setCheckState(
                0, Qt.CheckState.Checked if visible else Qt.CheckState.Unchecked
            )
        self._tree_updating = False
        self.selection_focus_active = False
        if self.selected_id:
            self.opacity.blockSignals(True)
            self.opacity.setValue(100)
            self.opacity.blockSignals(False)
        self.plotter.reset_camera(render=False)
        self.plotter.render()

    def _show_system(self, system: str | None) -> None:
        # A layer change while studying a structure must not discard the
        # student's position, orientation, or zoom.  Only objects intersecting
        # the active anatomical frame are enabled; "Exibir todas" is the
        # explicit way back to the complete body.
        focus_bounds = self.active_focus_bounds
        filter_bounds = self.active_filter_bounds
        view_frustum = self._view_frustum() if focus_bounds is not None else None
        self._restore_structure_opacities()
        self._tree_updating = True
        visible_count = 0
        anatomical_profile = getattr(self, "anatomical_profile", "masculino")
        for structure_id, actor in self.actors.items():
            structure = self.catalog[structure_id]
            matches_system = (
                (system is None or structure.system == system)
                and anatomical_profile_allows(structure, anatomical_profile)
            )
            structure_bounds = tuple(
                float(value) for value in self.meshes[structure_id].bounds
            )
            if focus_bounds is None:
                matches_focus = True
            else:
                neighborhood = filter_bounds or focus_bounds
                matches_focus = bounds_intersect(structure_bounds, neighborhood)
                if matches_focus and view_frustum is not None:
                    matches_focus = bool(
                        view_frustum.OverallBoundsTest(structure_bounds)
                    )
            visible = matches_system and matches_focus
            actor.visibility = visible
            visible_count += int(visible)
            self.items[structure_id].setCheckState(
                0, Qt.CheckState.Checked if visible else Qt.CheckState.Unchecked
            )
        self._tree_updating = False
        if focus_bounds is None:
            self.plotter.reset_camera(render=False)
        self.plotter.render()
        label = "todas as estruturas" if system is None else system.lower()
        scope = " na região em foco" if focus_bounds is not None else ""
        self.statusBar().showMessage(
            f"Exibindo {label}{scope} • {visible_count} estruturas"
        )

    def _change_anatomical_profile(self, _index: int) -> None:
        profile = self.profile_selector.currentData()
        if not profile or profile == self.anatomical_profile:
            return
        camera_position = self.plotter.camera_position
        self._restore_structure_opacities()
        if self.selected_id and not anatomical_profile_allows(
            self.catalog[self.selected_id], profile
        ):
            self.selected_id = None
            self.tree.clearSelection()
            self._show_welcome()
        self.anatomical_profile = profile
        self._show_system(None)
        self.plotter.camera_position = camera_position
        self._filter_tree(self.search.text())
        self.plotter.render()
        labels = {"masculino": "masculino", "feminino": "feminino", "ambos": "comparativo"}
        self.statusBar().showMessage(
            f"Perfil reprodutivo {labels[profile]} ativo • enquadramento preservado"
        )

    def _view_frustum(self):
        """Build a bounds tester for the camera's current visible 3D volume."""
        if self.plotter.iren is None:
            return None
        try:
            coefficients = [0.0] * 24
            aspect = float(self.plotter.renderer.GetTiledAspectRatio())
            self.plotter.camera.GetFrustumPlanes(aspect, coefficients)
            planes = vtkPlanes()
            planes.SetFrustumPlanes(coefficients)
            frustum = vtkExtractSelectedFrustum()
            frustum.SetFrustum(planes)
            return frustum
        except (AttributeError, RuntimeError, TypeError, ValueError):
            return None

    def _view_front(self) -> None:
        self.plotter.camera_position = [(0, -8, 0), (0, 0, 0), (0, 0, 1)]
        self._reset_camera()

    def _view_back(self) -> None:
        self.plotter.camera_position = [(0, 8, 0), (0, 0, 0), (0, 0, 1)]
        self._reset_camera()

    def _view_side(self) -> None:
        self.plotter.camera_position = [(8, 0, 0), (0, 0, 0), (0, 0, 1)]
        self._reset_camera()

    def _view_top(self) -> None:
        self.plotter.camera_position = [(0, 0, 8), (0, 0, 0), (0, 1, 0)]
        self._reset_camera()

    def _selected_focus_bounds(self):
        if not self.selected_id:
            return None
        structure = self.catalog[self.selected_id]
        return camera_focus_bounds(
            self.meshes[self.selected_id],
            self.scene_bounds,
            structure.region,
        )

    def _zoom_in(self) -> None:
        self.plotter.camera.zoom(1.18)
        self.plotter.render()

    def _zoom_out(self) -> None:
        self.plotter.camera.zoom(1 / 1.18)
        self.plotter.render()

    def _reset_camera(self) -> None:
        self.plotter.reset_camera(bounds=self.active_focus_bounds)

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt naming convention
        self.plotter.close()
        super().closeEvent(event)


def apply_theme(app: QApplication) -> None:
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#20252d"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#eef2f5"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#171b21"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#252b34"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#eef2f5"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#303844"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#eef2f5"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#4b8ecf"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)
    app.setStyleSheet(
        "QLabel#panelTitle { font-size: 18px; font-weight: 600; padding: 6px 0; }"
        "QLabel#hint { color: #aeb8c4; padding: 4px; }"
        "QLabel#viewportHint { color: #c5ced8; background: #171c23; padding: 6px; }"
        "QLineEdit, QTreeWidget, QTextBrowser { border: 1px solid #3b4654; border-radius: 4px; }"
        "QPushButton { min-height: 28px; padding: 2px 10px; }"
    )
