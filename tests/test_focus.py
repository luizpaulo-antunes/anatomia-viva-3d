import pyvista as pv
import pytest

from anatomia_app.main_window import camera_focus_bounds


def test_camera_focus_bounds_center_and_pad_selected_mesh() -> None:
    mesh = pv.Box(bounds=(1, 3, -2, 2, 5, 6))

    bounds = camera_focus_bounds(mesh)

    # The longest axis is 4 units, so every side receives 0.72 unit padding.
    assert bounds == pytest.approx((0.28, 3.72, -2.72, 2.72, 4.28, 6.72))
