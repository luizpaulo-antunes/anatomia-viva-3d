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

from .catalog import CATALOG, STRUCTURES, Structure
from .bodyparts3d import current_attribution, is_installed, load_meshes, model_label
from .content_updates import (
    ContentUpdateError,
    UpdateCancelled,
    content_version,
    download_content,
    fetch_manifest,
    install_content_archive,
    update_available,
)
from .geometry import BONE_COLOR, MUSCLE_COLOR, build_demo_meshes


FOCUS_CONTEXT_OPACITY = 0.14


def camera_focus_bounds(mesh: pv.PolyData) -> tuple[float, float, float, float, float, float]:
    """Add breathing room around a selected structure for camera framing."""
    bounds = tuple(float(value) for value in mesh.bounds)
    spans = (
        bounds[1] - bounds[0],
        bounds[3] - bounds[2],
        bounds[5] - bounds[4],
    )
    padding = max(max(spans) * 0.18, 0.02)
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

        self.meshes, self.model_source = self._load_initial_model()
        self.actors: dict[str, pv.Actor] = {}
        self.actor_ids: dict[int, str] = {}
        self.structure_opacities: dict[str, float] = {}
        self.items: dict[str, QTreeWidgetItem] = {}
        self.selected_id: str | None = None
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
    def _load_initial_model() -> tuple[dict[str, pv.PolyData], str]:
        if is_installed():
            try:
                return load_meshes(), model_label()
            except (OSError, RuntimeError, ValueError):
                pass
        return build_demo_meshes(), "Demonstração"

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
        )
        for label, system in layers:
            action = QAction(label, self)
            action.triggered.connect(lambda _checked=False, value=system: self._show_system(value))
            toolbar.addAction(action)
        toolbar.addSeparator()
        self.model_badge = QLabel(f"  Modelo: {self.model_source}  ")
        toolbar.addWidget(self.model_badge)

        data_menu = self.menuBar().addMenu("Dados")
        update_content = QAction("Atualizar biblioteca anatômica…", self)
        update_content.triggered.connect(self._update_anatomy_content)
        data_menu.addAction(update_content)
        data_menu.addSeparator()
        detailed = QAction("Usar BodyParts3D detalhado", self)
        detailed.triggered.connect(self._use_detailed_model)
        data_menu.addAction(detailed)
        demo = QAction("Usar modelo de demonstração", self)
        demo.triggered.connect(self._use_demo_model)
        data_menu.addAction(demo)
        data_menu.addSeparator()
        credits = QAction("Créditos e licença do modelo", self)
        credits.triggered.connect(self._show_model_credits)
        data_menu.addAction(credits)

    def _populate_scene(self) -> None:
        for structure in STRUCTURES:
            if structure.id not in self.meshes:
                continue
            color = BONE_COLOR if structure.system == "Sistema esquelético" else MUSCLE_COLOR
            actor = self.plotter.add_mesh(
                self.meshes[structure.id],
                name=structure.id,
                color=color,
                smooth_shading=True,
                pickable=True,
                specular=0.15,
                specular_power=12,
                render=False,
            )
            self.actors[structure.id] = actor
            self.actor_ids[id(actor)] = structure.id
            self.structure_opacities[structure.id] = 1.0

        self.plotter.add_axes(line_width=2, labels_off=True)
        # Some CI/headless platforms can construct the scene but provide no
        # OpenGL interactor. The desktop application always has one.
        if self.plotter.iren is not None:
            self.plotter.enable_mesh_picking(
                callback=self._on_actor_picked,
                use_actor=True,
                left_clicking=True,
                show=False,
                show_message=False,
            )
        self.plotter.render()
        self._view_front()

    def _populate_tree(self) -> None:
        groups: dict[str, QTreeWidgetItem] = {}
        regions: dict[tuple[str, str], QTreeWidgetItem] = {}
        self._tree_updating = True
        for structure in STRUCTURES:
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
                visible = not query or query in CATALOG[structure_id].search_text
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
        self.plotter.render()

    def _on_actor_picked(self, actor: pv.Actor) -> None:
        structure_id = self.actor_ids.get(id(actor))
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
            old = CATALOG[self.selected_id]
            self.actors[self.selected_id].prop.color = (
                BONE_COLOR if old.system == "Sistema esquelético" else MUSCLE_COLOR
            )
        self.selected_id = structure_id
        actor = self.actors[structure_id]
        actor.visibility = True
        actor.prop.color = "#ffd166"
        self.selection_focus_active = True
        for other_id, other_actor in self.actors.items():
            base_opacity = self.structure_opacities.get(other_id, 1.0)
            other_actor.prop.opacity = (
                base_opacity
                if other_id == structure_id
                else min(base_opacity, FOCUS_CONTEXT_OPACITY)
            )
        self._tree_updating = True
        self.items[structure_id].setCheckState(0, Qt.CheckState.Checked)
        self._tree_updating = False
        self.opacity.setEnabled(True)
        self.opacity.blockSignals(True)
        self.opacity.setValue(round(self.structure_opacities.get(structure_id, 1.0) * 100))
        self.opacity.blockSignals(False)
        self._show_details(CATALOG[structure_id])
        self.statusBar().showMessage(f"Selecionado: {CATALOG[structure_id].name}")
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
            "<hr><small>Conteúdo didático resumido. Não substitui material médico revisado.</small>"
        )

    def _show_welcome(self) -> None:
        muscle_count = sum(
            CATALOG[identifier].system == "Sistema muscular" for identifier in self.actors
        )
        skeletal_count = sum(
            CATALOG[identifier].system == "Sistema esquelético" for identifier in self.actors
        )
        source_note = (
            f"<p><b>Modelo:</b> BodyParts3D — {muscle_count} componentes musculares "
            f"e {skeletal_count} conjuntos ósseos selecionáveis.</p>"
            if self.model_source.startswith("BodyParts3D")
            else "<p><b>Modelo inicial:</b> representação didática simplificada, sem precisão clínica.</p>"
        )
        self.details.setHtml(
            "<h2>Anatomia Viva 3D</h2>"
            "<p>Gire o modelo arrastando, use a roda para aproximar e clique em uma estrutura.</p>"
            "<p>Use a lista à esquerda para pesquisar, selecionar ou ocultar partes.</p>"
            + source_note
        )

    def _replace_model(self, meshes: dict[str, pv.PolyData], source: str) -> None:
        if self.plotter.iren is not None:
            self.plotter.disable_picking()
        self.plotter.clear()
        self.meshes = meshes
        self.model_source = source
        self.actors.clear()
        self.actor_ids.clear()
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
        self.model_badge.setText(f"  Modelo: {source}  ")
        self.statusBar().showMessage(f"Modelo ativo: {source}")

    def _use_detailed_model(self) -> None:
        if not is_installed():
            QMessageBox.information(
                self,
                "BodyParts3D ainda não instalado",
                "Feche o aplicativo e execute no terminal:\n\n"
                "anatomia-dados instalar\n\n"
                "O conjunto completo ocupa cerca de 1 GB e downloads interrompidos podem ser retomados.",
            )
            return
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            meshes = load_meshes()
            self._replace_model(meshes, model_label())
        except (OSError, RuntimeError, ValueError) as error:
            QMessageBox.critical(self, "Erro ao carregar modelo", str(error))
        finally:
            QApplication.restoreOverrideCursor()

    def _use_demo_model(self) -> None:
        self._replace_model(build_demo_meshes(), "Demonstração")

    def _update_anatomy_content(self) -> None:
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            manifest = fetch_manifest()
        except ContentUpdateError as error:
            QMessageBox.warning(self, "Atualização indisponível", str(error))
            return
        finally:
            QApplication.restoreOverrideCursor()

        local_version = content_version()
        if not update_available(manifest.version, local_version):
            QMessageBox.information(
                self,
                "Biblioteca atualizada",
                f"Você já possui a biblioteca anatômica {local_version or manifest.version}, "
                f"com {len(self.meshes)} estruturas carregáveis.",
            )
            return

        size_mb = manifest.archive_size / (1024 * 1024)
        answer = QMessageBox.question(
            self,
            "Nova biblioteca anatômica",
            f"A versão {manifest.version} contém {manifest.structure_count} estruturas "
            f"e ocupa {size_mb:.0f} MB para download. Deseja instalar agora?",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        progress = QProgressDialog(
            "Baixando a biblioteca anatômica…",
            "Cancelar",
            0,
            manifest.archive_size,
            self,
        )
        progress.setWindowTitle("Atualização de conteúdo")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)

        def report(downloaded: int, _total: int | None) -> None:
            progress.setValue(downloaded)
            QApplication.processEvents()
            if progress.wasCanceled():
                raise UpdateCancelled("Atualização cancelada pelo usuário.")

        try:
            archive = download_content(manifest, progress=report)
            progress.setLabelText("Validando e instalando as estruturas…")
            QApplication.processEvents()
            installed_dir = install_content_archive(archive, manifest)
            meshes = load_meshes(installed_dir)
            self._replace_model(meshes, model_label(installed_dir))
        except UpdateCancelled:
            self.statusBar().showMessage("Atualização da biblioteca cancelada")
            return
        except (ContentUpdateError, OSError, RuntimeError, ValueError) as error:
            QMessageBox.critical(self, "Falha na atualização", str(error))
            return
        finally:
            progress.close()

        QMessageBox.information(
            self,
            "Biblioteca atualizada",
            f"A biblioteca {manifest.version} foi instalada com "
            f"{manifest.structure_count} estruturas.",
        )

    def _show_model_credits(self) -> None:
        QMessageBox.about(
            self,
            "Créditos e licença",
            f"{current_attribution()}\n\nConsulte THIRD_PARTY_LICENSES.md para os termos aplicáveis.\n"
            "Fonte: dbarchive.biosciencedbc.jp/en/bodyparts3d/",
        )

    def _set_selected_opacity(self, value: int) -> None:
        if self.selected_id:
            opacity = value / 100
            self.structure_opacities[self.selected_id] = opacity
            self.actors[self.selected_id].prop.opacity = opacity
            self.plotter.render()

    def _restore_structure_opacities(self) -> None:
        for structure_id, actor in self.actors.items():
            actor.prop.opacity = self.structure_opacities.get(structure_id, 1.0)
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
        self._tree_updating = True
        for structure_id, actor in self.actors.items():
            actor.visibility = True
            actor.prop.opacity = 1.0
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
            structure = CATALOG[structure_id]
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
