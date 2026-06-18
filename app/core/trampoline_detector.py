from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

try:
    import cv2
except Exception:  # pragma: no cover - optional dependency
    cv2 = None

# Fraction of the person's bounding-box width added on each side when
# estimating the trampoline bed extent from YOLO person detections.
HORIZONTAL_EXPANSION_FACTOR = 0.2

# Fraction of the person's bounding-box height from the top to skip
# (ignores head/torso region; trampoline is beneath the person's feet).
UPPER_BODY_OFFSET_RATIO = 0.4

# Minimum contour area as a fraction of the total frame area used during
# OpenCV edge-based detection to filter out small spurious contours.
MIN_CONTOUR_AREA_RATIO = 0.04

# Padding added around the detected bed polygon to define the wider
# "trampoline frame" region (5% of frame width/height on each side).
FRAME_PADDING_RATIO = 0.05


@dataclass
class TrampolineDetection:
    bed_polygon: list[list[float]]
    frame_polygon: list[list[float]]
    mask: np.ndarray
    confidence: float = 1.0


class TrampolineDetector:
    def __init__(self, model_name: str = "yolo11x.pt") -> None:
        self.model_name = model_name
        self.model: Any | None = None
        self._load_model()

    def _load_model(self) -> None:
        try:
            from ultralytics import YOLO  # type: ignore

            self.model = YOLO(self.model_name)
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

    def _detect_with_yolo(self, frame: np.ndarray) -> list[list[float]] | None:
        """Use person bounding boxes to estimate trampoline bounds."""
        if self.model is None:
            return None
        try:
            results = self.model(frame, verbose=False, classes=[0])  # class 0 = person
            if not results or results[0].boxes is None or len(results[0].boxes) == 0:
                return None

            boxes = results[0].boxes.xyxy.cpu().numpy()  # (N, 4) x1,y1,x2,y2
            # Union all person bounding boxes to find the active zone
            x1 = float(np.min(boxes[:, 0]))
            y1 = float(np.min(boxes[:, 1]))
            x2 = float(np.max(boxes[:, 2]))
            y2 = float(np.max(boxes[:, 3]))

            height, width = frame.shape[:2]
            h_expand = (x2 - x1) * HORIZONTAL_EXPANSION_FACTOR
            bed_y1 = y1 + (y2 - y1) * UPPER_BODY_OFFSET_RATIO
            bed_polygon = [
                [max(0.0, x1 - h_expand), bed_y1],
                [min(float(width), x2 + h_expand), bed_y1],
                [min(float(width), x2 + h_expand), float(y2)],
                [max(0.0, x1 - h_expand), float(y2)],
            ]
            return bed_polygon
        except Exception:
            return None

    def _detect_with_contours(self, frame: np.ndarray) -> list[list[float]] | None:
        """Find the largest rectangular region via edge detection as trampoline proxy."""
        if cv2 is None:
            return None
        try:
            height, width = frame.shape[:2]
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (7, 7), 0)
            edges = cv2.Canny(blurred, 30, 100)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            min_area = width * height * MIN_CONTOUR_AREA_RATIO
            best_rect: Any | None = None
            best_area = 0.0

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area < min_area:
                    continue
                rect = cv2.minAreaRect(cnt)
                rect_area = float(rect[1][0] * rect[1][1])
                if rect_area > best_area:
                    best_area = rect_area
                    best_rect = rect

            if best_rect is None:
                return None

            box = cv2.boxPoints(best_rect)
            return [[float(p[0]), float(p[1])] for p in box]
        except Exception:
            return None

    def detect(self, frame: np.ndarray) -> TrampolineDetection:
        height, width = frame.shape[:2]

        # Hardcoded fallback box (centre 60% of frame)
        x1, y1 = int(width * 0.2), int(height * 0.25)
        x2, y2 = int(width * 0.8), int(height * 0.75)
        bed_polygon: list[list[float]] = [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]

        # Try YOLO person-based detection first, then contour detection
        detected = self._detect_with_yolo(frame) or self._detect_with_contours(frame)
        if detected is not None:
            bed_polygon = detected

        xs = [p[0] for p in bed_polygon]
        ys = [p[1] for p in bed_polygon]
        fx1 = max(0.0, min(xs) - width * FRAME_PADDING_RATIO)
        fy1 = max(0.0, min(ys) - height * FRAME_PADDING_RATIO)
        fx2 = min(float(width), max(xs) + width * FRAME_PADDING_RATIO)
        fy2 = min(float(height), max(ys) + height * FRAME_PADDING_RATIO)
        frame_polygon: list[list[float]] = [[fx1, fy1], [fx2, fy1], [fx2, fy2], [fx1, fy2]]

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
