from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class PoseResult:
    keypoints: list[list[float]]
    confidence: list[float]


class PoseTracker:
    def __init__(self, model_name: str = "vitpose", smoothing_alpha: float = 0.4) -> None:
        self.model_name = model_name
        self.smoothing_alpha = smoothing_alpha
        self._prev_keypoints: np.ndarray | None = None
        self.model: Any | None = None
        self._load_model()

    def _load_model(self) -> None:
        self.model = None

    def _default_keypoints(self, frame_shape: tuple[int, ...]) -> tuple[np.ndarray, np.ndarray]:
        height, width = frame_shape[:2]
        center_x, center_y = width / 2.0, height / 2.0
        keypoints = np.array([[center_x, center_y] for _ in range(17)], dtype=np.float32)
        confidence = np.array([0.2 for _ in range(17)], dtype=np.float32)
        return keypoints, confidence

    def track(self, frame: np.ndarray, raw_keypoints: np.ndarray | None = None, raw_confidence: np.ndarray | None = None) -> PoseResult:
        if raw_keypoints is None or raw_confidence is None:
            raw_keypoints, raw_confidence = self._default_keypoints(frame.shape)

        if self._prev_keypoints is None:
            smoothed = raw_keypoints
        else:
            smoothed = (self.smoothing_alpha * raw_keypoints) + ((1.0 - self.smoothing_alpha) * self._prev_keypoints)

        self._prev_keypoints = smoothed

        return PoseResult(keypoints=smoothed.tolist(), confidence=raw_confidence.tolist())


def track_pose(frame: np.ndarray, tracker: PoseTracker | None = None) -> dict[str, Any]:
    active_tracker = tracker or PoseTracker()
    result = active_tracker.track(frame)
    return {"keypoints": result.keypoints, "confidence": result.confidence}
