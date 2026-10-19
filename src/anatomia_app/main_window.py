from __future__ import annotations

from html import escape

import pyvista as pv
from pyvistaqt import QtInteractor
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor, QPalette
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
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

from .atlas import AtlasModel
from .catalog import STRUCTURES, Structure
from .bodyparts3d import current_attribution, is_installed, load_meshes, model_label
from .geometry import BONE_COLOR, MUSCLE_COLOR, build_demo_meshes
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


FOCUS_CONTEXT_OPACITY = 0.14
# Frame an area 30% larger than the previous selection view.  This preserves
# automatic focus without placing the camera uncomfortably close to small parts.
FOCUS_PADDING_RATIO = 0.384
SYSTEM_COLORS = {
    "Sistema esquelético": BONE_COLOR,
    "Articulações, ligamentos e fáscias": "#6ec5bd",
    "Sistema muscular": MUSCLE_COLOR,
    "Sistema cardiovascular": "#c74646",
    "Sistema linfático": "#6cad72",
    "Sistema nervoso": "#e6c85c",
    "Órgãos e vísceras": "#b57aa6",
}


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


def camera_focus_bounds(mesh: pv.PolyData) -> tuple[float, float, float, float, float, float]:
    """Add breathing room around a selected structure for camera framing."""
    bounds = tuple(float(value) for value in mesh.bounds)
    spans = (
        bounds[1] - bounds[0],
        bounds[3] - bounds[2],
        bounds[5] - bounds[4],
    )
    padding = max(max(spans) * FOCUS_PADDING_RATIO, 0.02)
    return (
        bounds[0] - padding,
        bounds[1] + padding,
        bounds[2] - padding,
        bounds[3] + padding,
        bounds[4] - padding,
        bounds[5] + padding,
    )


class AnatomyWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Anatomia Viva 3D — Atlas de Anatomia")
        self.resize(1400, 850)

        self.render_cell_limit = recommended_cell_limit()
        self.atlas = self._load_initial_model(self.render_cell_limit)
        self.meshes = self.atlas.meshes
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
        self.selection_focus_active = False
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
                return load_zanatomy(
                    modern,
                    max_cells_per_structure=max_cells_per_structure,
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
        layout.addWidget(self.plotter.interactor)
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
            ("Centralizar", self._reset_camera),
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
            item.setCheckState(0, Qt.CheckState.Checked)
            self.items[structure.id] = item
        self._tree_updating = False
        self.tree.expandToDepth(0)

    def _filter_tree(self, text: str) -> None:
        query = text.strip().casefold()

        def filter_item(item: QTreeWidgetItem) -> bool:
            structure_id = item.data(0, Qt.ItemDataRole.UserRole)
            if structure_id:
                visible = not query or query in self.catalog[structure_id].search_text
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
            self.actors[structure_id].visibility = item.checkState(0) == Qt.CheckState.Checked
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
        if self.selected_id and self.selected_id in self.actors:
            previous_item = self.items[self.selected_id]
            self.actors[self.selected_id].visibility = (
                previous_item.checkState(0) == Qt.CheckState.Checked
            )
        self.selected_id = structure_id
        actor = self.actors[structure_id]
        # The highlighted copy replaces this one block while focus is active.
        # This avoids drawing the selected surface twice and keeps the opacity
        # slider exact.
        actor.visibility = False
        self._remove_selection_overlay()
        if self.atlas_actor is not None:
            self.atlas_actor.prop.opacity = FOCUS_CONTEXT_OPACITY
        self.selection_actor = self.plotter.add_mesh(
            self.meshes[structure_id],
            name="estrutura-selecionada",
            color="#ffd166",
            opacity=self.structure_opacities.get(structure_id, 1.0),
            smooth_shading=False,
            pickable=False,
            render=False,
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
        self.statusBar().showMessage(f"Selecionado: {self.catalog[structure_id].name}")
        self.plotter.reset_camera(bounds=camera_focus_bounds(self.meshes[structure_id]), render=False)
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
            "<p>Gire o modelo arrastando, use a roda para aproximar e clique em uma estrutura.</p>"
            "<p>Use a lista à esquerda para pesquisar, selecionar ou ocultar partes.</p>"
            f"<p><b>Atlas:</b> {escape(self.atlas.label)} — {len(self.actors)} estruturas.</p>"
            f"<p>{coverage}</p>"
            f"<p><b>Cobertura:</b> {escape(self.atlas.coverage_note)}</p>"
            "<hr><small>Atlas educacional. Não deve ser usado para diagnóstico ou planejamento clínico.</small>"
        )

    def _replace_model(self, atlas: AtlasModel) -> None:
        if self.plotter.iren is not None:
            self.plotter.disable_picking()
        self.plotter.clear()
        self.atlas_actor = None
        self.selection_actor = None
        self.atlas = atlas
        self.meshes = atlas.meshes
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

    def _restore_structure_opacities(self) -> None:
        if self.atlas_actor is not None:
            self.atlas_actor.prop.opacity = 1.0
        self._remove_selection_overlay()
        if self.selected_id in self.actors and self.selected_id in self.items:
            self.actors[self.selected_id].visibility = (
                self.items[self.selected_id].checkState(0) == Qt.CheckState.Checked
            )
        self.selection_focus_active = False

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
            self.plotter.reset_camera(render=False)
            self.plotter.render()

    def _show_all(self) -> None:
        self._restore_structure_opacities()
        self._tree_updating = True
        for structure_id, actor in self.actors.items():
            actor.visibility = True
            self.structure_opacities[structure_id] = 1.0
            self.items[structure_id].setCheckState(0, Qt.CheckState.Checked)
        self._tree_updating = False
        self.selection_focus_active = False
        if self.selected_id:
            self.opacity.blockSignals(True)
            self.opacity.setValue(100)
            self.opacity.blockSignals(False)
        self.plotter.reset_camera(render=False)
        self.plotter.render()

    def _show_system(self, system: str | None) -> None:
        self._restore_structure_opacities()
        self._tree_updating = True
        for structure_id, actor in self.actors.items():
            structure = self.catalog[structure_id]
            visible = system is None or structure.system == system
            actor.visibility = visible
            self.items[structure_id].setCheckState(
                0, Qt.CheckState.Checked if visible else Qt.CheckState.Unchecked
            )
        self._tree_updating = False
        self.plotter.reset_camera(render=False)
        self.plotter.render()
        label = "todas as estruturas" if system is None else system.lower()
        self.statusBar().showMessage(f"Exibindo {label}")

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

    def _reset_camera(self) -> None:
        bounds = (
            camera_focus_bounds(self.meshes[self.selected_id])
            if self.selection_focus_active and self.selected_id
            else None
        )
        self.plotter.reset_camera(bounds=bounds)

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
        "QLineEdit, QTreeWidget, QTextBrowser { border: 1px solid #3b4654; border-radius: 4px; }"
        "QPushButton { min-height: 28px; padding: 2px 10px; }"
    )
