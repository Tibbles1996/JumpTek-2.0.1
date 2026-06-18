import numpy as np
import pytest

from app.core.pose_tracker import PoseTracker


def test_pose_tracker_smooths_keypoints() -> None:
    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    tracker = PoseTracker(smoothing_alpha=0.5)

    first = np.array([[10.0, 10.0] for _ in range(17)], dtype=np.float32)
    second = np.array([[20.0, 20.0] for _ in range(17)], dtype=np.float32)
    conf = np.array([1.0 for _ in range(17)], dtype=np.float32)

    result1 = tracker.track(frame, raw_keypoints=first, raw_confidence=conf)
    result2 = tracker.track(frame, raw_keypoints=second, raw_confidence=conf)

    assert result1.keypoints[0] == pytest.approx([10.0, 10.0])
    assert result2.keypoints[0] == pytest.approx([15.0, 15.0])
