from __future__ import annotations

from typing import Any

import numpy as np

try:
    import cv2
except Exception:  # pragma: no cover - optional dependency
    cv2 = None


DISTANCE_BASE_M = 5.0
DISTANCE_SCALE = 1000.0


class CameraCalibrator:
    def __init__(self, trampoline_width_m: float, trampoline_length_m: float) -> None:
        self.trampoline_width_m = trampoline_width_m
        self.trampoline_length_m = trampoline_length_m

    def calibrate(self, bed_polygon: list[list[float]]) -> dict[str, Any]:
        image_pts = np.array(bed_polygon, dtype=np.float32)
        world_pts = np.array(
            [
                [0.0, 0.0],
                [self.trampoline_width_m, 0.0],
                [self.trampoline_width_m, self.trampoline_length_m],
                [0.0, self.trampoline_length_m],
            ],
            dtype=np.float32,
        )

        if cv2 is not None:
            homography, _ = cv2.findHomography(image_pts, world_pts)
            if homography is None:
                homography = np.eye(3, dtype=np.float32)
        else:
            homography = np.eye(3, dtype=np.float32)

        y_span = float(np.max(image_pts[:, 1]) - np.min(image_pts[:, 1]))
        x_span = float(np.max(image_pts[:, 0]) - np.min(image_pts[:, 0]))
        # Approximate camera tilt from bed distortion in image space:
        # as vertical/horizontal span diverges, perspective tilt is likely larger.
        tilt_deg = float(np.degrees(np.arctan2(abs(y_span - x_span), max(x_span, 1.0))))
        # Distance proxy based on inverse projected area (~1 / (x_span*y_span));
        # as a planar object moves farther from the camera, its image area shrinks.
        # DISTANCE_BASE_M sets a nominal baseline and DISTANCE_SCALE tunes sensitivity
        # of this heuristic for expected trampoline capture framing.
        distance_m = float(DISTANCE_BASE_M + (DISTANCE_SCALE / max(y_span * x_span, 1.0)))

        return {
            "homography": homography,
            "extrinsics": {
                "tilt_deg": tilt_deg,
                "distance_m": distance_m,
            },
            "bed_plane": {
                "normal": [0.0, 0.0, 1.0],
                "origin": [0.0, 0.0, 0.0],
            },
        }


def auto_calibrate(
    bed_polygon: list[list[float]],
    trampoline_width_m: float,
    trampoline_length_m: float,
) -> dict[str, Any]:
    calibrator = CameraCalibrator(trampoline_width_m, trampoline_length_m)
    return calibrator.calibrate(bed_polygon)
