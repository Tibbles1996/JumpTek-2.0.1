from __future__ import annotations

import numpy as np

LEFT_ANKLE_INDEX = 15
RIGHT_ANKLE_INDEX = 16


def _foot_midpoint_xy(keypoints: np.ndarray) -> np.ndarray:
    left = keypoints[LEFT_ANKLE_INDEX]
    right = keypoints[RIGHT_ANKLE_INDEX]
    return (left + right) / 2.0


def compute_tof(
    jump: dict[str, int],
    heights_m: list[float],
    keypoints_per_frame: list[np.ndarray],
    fps: float,
) -> dict[str, object]:
    start = jump["start_frame"]
    end = jump["end_frame"]
    if end < start:
        raise ValueError("end_frame must be >= start_frame")

    frames = list(range(start, end + 1))
    segment_heights = [float(h) for h in heights_m[start : end + 1]]
    takeoff_time = start / fps
    landing_time = end / fps
    tof = landing_time - takeoff_time
    peak_height = float(max(segment_heights) if segment_heights else 0.0)

    start_mid = _foot_midpoint_xy(keypoints_per_frame[start])
    end_mid = _foot_midpoint_xy(keypoints_per_frame[end])
    horizontal_drift = float(np.linalg.norm(end_mid - start_mid))

    return {
        "tof": float(tof),
        "peak_height": peak_height,
        "takeoff_time": float(takeoff_time),
        "landing_time": float(landing_time),
        "takeoff_point": start_mid.tolist(),
        "landing_point": end_mid.tolist(),
        "horizontal_drift": horizontal_drift,
        "frames": frames,
    }
