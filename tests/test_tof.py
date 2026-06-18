import numpy as np
import pytest

from app.core.tof import compute_tof


def test_compute_tof_returns_metrics() -> None:
    jump = {"start_frame": 10, "end_frame": 40}
    heights = [0.0] * 50
    heights[20] = 1.2

    keypoints = []
    for idx in range(50):
        pts = np.zeros((17, 2), dtype=np.float32)
        pts[15] = [100 + idx, 200]
        pts[16] = [120 + idx, 200]
        keypoints.append(pts)

    result = compute_tof(jump, heights, keypoints, fps=30.0)

    assert result["tof"] == 1.0
    assert result["peak_height"] == 1.2
    assert result["takeoff_point"] == [120.0, 200.0]
    assert result["landing_point"] == [150.0, 200.0]
    assert result["horizontal_drift"] == 30.0


def test_compute_tof_invalid_range_raises() -> None:
    with pytest.raises(ValueError):
        compute_tof({"start_frame": 5, "end_frame": 4}, [0.0] * 10, [np.zeros((17, 2), dtype=np.float32) for _ in range(10)], fps=30.0)
