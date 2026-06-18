import numpy as np

from app.core.trampoline_detector import TrampolineDetector


def test_detector_returns_expected_shapes() -> None:
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detector = TrampolineDetector()

    result = detector.detect(frame)

    assert len(result.bed_polygon) == 4
    assert len(result.frame_polygon) == 4
    assert result.mask.shape == (480, 640)
    assert int(result.mask.sum()) > 0
