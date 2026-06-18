from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

try:
    import cv2
except Exception:  # pragma: no cover - optional dependency
    cv2 = None


@dataclass
class TrampolineDetection:
    bed_polygon: list[list[float]]
    frame_polygon: list[list[float]]
    mask: np.ndarray
    confidence: float = 1.0


class TrampolineDetector:
    def __init__(self, model_name: str = "yolov8n.pt") -> None:
        self.model_name = model_name
        self.model: Any | None = None
        self._load_model()

    def _load_model(self) -> None:
        try:
            from ultralytics import RTDETR, YOLO  # type: ignore

            self.model = RTDETR(self.model_name) if "rtdetr" in self.model_name.lower() else YOLO(self.model_name)
        except Exception:
            self.model = None


    @staticmethod
    def estimate_confidence(frame: np.ndarray, mask: np.ndarray) -> float:
        if mask.size == 0:
            return 0.0
        masked = frame[mask > 0]
        if masked.size == 0:
            return 0.0
        variance = float(np.var(masked))
        normalized = min(1.0, variance / 5000.0)
        return max(0.0, normalized)

    def detect(self, frame: np.ndarray) -> TrampolineDetection:
        height, width = frame.shape[:2]

        x1, y1 = int(width * 0.2), int(height * 0.25)
        x2, y2 = int(width * 0.8), int(height * 0.75)
        bed_polygon = [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]

        fx1, fy1 = int(width * 0.15), int(height * 0.2)
        fx2, fy2 = int(width * 0.85), int(height * 0.8)
        frame_polygon = [[fx1, fy1], [fx2, fy1], [fx2, fy2], [fx1, fy2]]

        mask = np.zeros((height, width), dtype=np.uint8)
        pts = np.array(bed_polygon, dtype=np.int32)
        if cv2 is not None:
            cv2.fillPoly(mask, [pts], 1)
        else:
            mask[y1:y2, x1:x2] = 1

        confidence = self.estimate_confidence(frame, mask)
        return TrampolineDetection(
            bed_polygon=bed_polygon,
            frame_polygon=frame_polygon,
            mask=mask,
            confidence=confidence,
        )


def detect_trampoline(frame: np.ndarray, detector: TrampolineDetector | None = None) -> dict[str, Any]:
    active_detector = detector or TrampolineDetector()
    result = active_detector.detect(frame)
    return {
        "bed_polygon": result.bed_polygon,
        "frame_polygon": result.frame_polygon,
        "mask": result.mask,
        "confidence": result.confidence,
    }
