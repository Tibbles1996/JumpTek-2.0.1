import numpy as np

from app.core.calibration import auto_calibrate


def test_auto_calibrate_returns_homography_and_extrinsics() -> None:
    bed_polygon = [[10, 10], [110, 10], [110, 60], [10, 60]]

    calibration = auto_calibrate(bed_polygon, trampoline_width_m=4.28, trampoline_length_m=2.14)

    assert calibration["homography"].shape == (3, 3)
    assert "tilt_deg" in calibration["extrinsics"]
    assert "distance_m" in calibration["extrinsics"]
    assert np.isfinite(calibration["extrinsics"]["distance_m"])
