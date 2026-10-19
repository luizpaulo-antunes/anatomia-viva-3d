from types import SimpleNamespace

import pyvista as pv
import pytest

from anatomia_app.main_window import (
    AnatomyWindow,
    bounds_intersect,
    camera_focus_bounds,
    combined_bounds,
    is_focus_context_structure,
    local_focus_bounds,
)
from anatomia_app.catalog import Structure


def test_camera_focus_bounds_center_and_pad_selected_mesh() -> None:
    mesh = pv.Box(bounds=(1, 3, -2, 2, 5, 6))

    bounds = camera_focus_bounds(mesh)

    # The selected view is 30% wider than before: 1.536 units of padding.
    assert bounds == pytest.approx((-0.536, 4.536, -3.536, 3.536, 3.464, 7.536))


def test_combined_bounds_contains_all_meshes() -> None:
    bounds = combined_bounds(
        [
            pv.Box(bounds=(-2, -1, 0, 1, 3, 4)),
            pv.Box(bounds=(1, 5, -4, -2, 8, 9)),
        ]
    )

    assert bounds == pytest.approx((-2, 5, -4, 1, 3, 9))


def test_region_filter_keeps_only_structures_in_current_focus() -> None:
    face_focus = (-0.16, 0.16, -0.12, 0.12, 1.34, 1.73)
    facial_nerve = (-0.08, 0.02, -0.09, -0.02, 1.43, 1.59)
    sciatic_nerve = (-0.09, -0.03, -0.08, 0.02, 0.25, 0.82)

    assert bounds_intersect(facial_nerve, face_focus)
    assert not bounds_intersect(sciatic_nerve, face_focus)


def test_region_filter_includes_structure_crossing_focus_boundary() -> None:
    focus = (-1, 1, -1, 1, 5, 8)
    crossing_nerve = (0, 0.2, 0, 0.2, 2, 5)

    assert bounds_intersect(crossing_nerve, focus)


def test_local_focus_bounds_limits_depth_behind_selected_structure() -> None:
    scene = (-0.34, 0.34, -0.14, 0.14, 0.0, 1.70)
    mouth_muscle = pv.Box(bounds=(0.0, 0.03, -0.10, -0.07, 1.51, 1.55))

    bounds = local_focus_bounds(mouth_muscle, scene)

    assert bounds == pytest.approx((-0.0272, 0.0572, -0.128, -0.042, 1.459, 1.601))


def test_selection_context_keeps_nearby_bones_but_hides_other_tissues() -> None:
    focus = (-0.1, 0.1, -0.1, 0.1, 1.4, 1.6)
    nearby_mesh = pv.Box(bounds=(-0.05, 0.05, -0.05, 0.05, 1.45, 1.55))
    distant_mesh = pv.Box(bounds=(-0.05, 0.05, -0.05, 0.05, 0.2, 0.4))
    bone = Structure("mandibula", "Mandíbula", "Mandibula", "Sistema esquelético", "", "")
    muscle = Structure("masseter", "Masseter", "Masseter", "Sistema muscular", "", "")

    assert is_focus_context_structure("mandibula", bone, nearby_mesh, "masseter", focus)
    assert not is_focus_context_structure("mandibula", bone, distant_mesh, "masseter", focus)
    assert not is_focus_context_structure("masseter", muscle, nearby_mesh, "masseter", focus)


def test_system_change_preserves_camera_and_filters_current_region() -> None:
    class FakePlotter:
        def __init__(self) -> None:
            self.reset_calls = 0
            self.render_calls = 0

        def reset_camera(self, render=False) -> None:
            self.reset_calls += 1

        def render(self) -> None:
            self.render_calls += 1

    class FakeItem:
        def __init__(self) -> None:
            self.state = None

        def setCheckState(self, _column, state) -> None:
            self.state = state

    class FakeStatusBar:
        def showMessage(self, message: str) -> None:
            self.message = message

    identifiers = ("nervo_face", "nervo_perna", "osso_face")
    actors = {identifier: SimpleNamespace(visibility=True) for identifier in identifiers}
    items = {identifier: FakeItem() for identifier in identifiers}
    plotter = FakePlotter()
    status = FakeStatusBar()
    window = SimpleNamespace(
        active_focus_bounds=(-0.2, 0.2, -0.2, 0.2, 1.3, 1.7),
        active_filter_bounds=(-0.15, 0.15, -0.15, 0.05, 1.35, 1.65),
        actors=actors,
        catalog={
            "nervo_face": SimpleNamespace(system="Sistema nervoso"),
            "nervo_perna": SimpleNamespace(system="Sistema nervoso"),
            "osso_face": SimpleNamespace(system="Sistema esquelético"),
        },
        meshes={
            "nervo_face": pv.Box(bounds=(-0.1, 0.1, -0.1, 0.1, 1.4, 1.6)),
            "nervo_perna": pv.Box(bounds=(-0.1, 0.1, -0.1, 0.1, 0.2, 0.8)),
            "osso_face": pv.Box(bounds=(-0.1, 0.1, -0.1, 0.1, 1.4, 1.6)),
        },
        items=items,
        plotter=plotter,
        _view_frustum=lambda: None,
        _restore_structure_opacities=lambda: None,
        _tree_updating=False,
        statusBar=lambda: status,
    )

    AnatomyWindow._show_system(window, "Sistema nervoso")

    assert actors["nervo_face"].visibility
    assert not actors["nervo_perna"].visibility
    assert not actors["osso_face"].visibility
    assert plotter.reset_calls == 0
    assert plotter.render_calls == 1
    assert "região em foco" in status.message


def test_tiny_facial_structure_uses_stable_head_frame() -> None:
    scene = (-0.34, 0.34, -0.14, 0.14, 0.0, 1.70)
    tiny_bone = pv.Box(bounds=(-0.01, 0.01, -0.08, -0.07, 1.54, 1.56))

    bounds = camera_focus_bounds(tiny_bone, scene, "Cabeça")
    spans = (bounds[1] - bounds[0], bounds[3] - bounds[2], bounds[5] - bounds[4])

    assert spans == pytest.approx((0.3264, 0.2408, 0.391))
    assert (bounds[4] + bounds[5]) / 2 == pytest.approx(1.53)


def test_repeated_tiny_selections_do_not_return_to_mega_zoom() -> None:
    scene = (-0.34, 0.34, -0.14, 0.14, 0.0, 1.70)
    first = pv.Box(bounds=(-0.015, -0.005, -0.08, -0.07, 1.52, 1.53))
    second = pv.Box(bounds=(0.005, 0.015, -0.08, -0.07, 1.58, 1.59))

    first_bounds = camera_focus_bounds(first, scene, "Cabeça")
    second_bounds = camera_focus_bounds(second, scene, "Cabeça")

    assert first_bounds[1] - first_bounds[0] == pytest.approx(
        second_bounds[1] - second_bounds[0]
    )
    assert first_bounds[5] - first_bounds[4] == pytest.approx(
        second_bounds[5] - second_bounds[4]
    )


def test_large_selected_structure_is_never_clipped_by_region_frame() -> None:
    scene = (-0.34, 0.34, -0.14, 0.14, 0.0, 1.70)
    femur = pv.Box(bounds=(0.03, 0.12, -0.08, 0.07, 0.35, 0.90))

    bounds = camera_focus_bounds(femur, scene, "Membro inferior")

    assert bounds[0] < femur.bounds[0]
    assert bounds[1] > femur.bounds[1]
    assert bounds[2] < femur.bounds[2]
    assert bounds[3] > femur.bounds[3]
    assert bounds[4] < femur.bounds[4]
    assert bounds[5] > femur.bounds[5]
