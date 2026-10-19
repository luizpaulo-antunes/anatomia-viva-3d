import pyvista as pv
import pytest

from anatomia_app.main_window import camera_focus_bounds


def test_camera_focus_bounds_center_and_pad_selected_mesh() -> None:
    mesh = pv.Box(bounds=(1, 3, -2, 2, 5, 6))

    bounds = camera_focus_bounds(mesh)

    # The selected view is 30% wider than before: 1.536 units of padding.
    assert bounds == pytest.approx((-0.536, 4.536, -3.536, 3.536, 3.464, 7.536))
