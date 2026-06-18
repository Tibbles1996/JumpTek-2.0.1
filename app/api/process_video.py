from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

import numpy as np
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.config import get_settings
from app.core.calibration import auto_calibrate
from app.core.jump_segmenter import JumpSegmenter
from app.core.pose_tracker import PoseTracker
from app.core.tof import compute_tof
from app.core.trampoline_detector import TrampolineDetector
from app.core.utils import download_video, extract_frames, to_serializable

router = APIRouter()


class ProcessVideoRequest(BaseModel):
    videoUrl: str = Field(..., min_length=1)
    sessionId: str = Field(..., min_length=1)


@router.post("/process-video")
def process_video(payload: ProcessVideoRequest) -> dict[str, object]:
    settings = get_settings()

    with tempfile.TemporaryDirectory(prefix="jumptek-") as tmp:
        tmp_path = Path(tmp)
        video_path = download_video(payload.videoUrl, tmp_path / "input.mp4")
        frames = extract_frames(video_path)
        if not frames:
            return {"sessionId": payload.sessionId, "jumps": []}

        detector = TrampolineDetector()
        detection = detector.detect(frames[0])
        calibration = auto_calibrate(
            bed_polygon=detection.bed_polygon,
            trampoline_width_m=settings.trampoline_width_m,
            trampoline_length_m=settings.trampoline_length_m,
        )

        tracker = PoseTracker()
        tracked_keypoints: list[np.ndarray] = []
        heights_m: list[float] = []

        bed_top = float(min(point[1] for point in detection.bed_polygon))
        bed_height_px = max(float(np.ptp([point[1] for point in detection.bed_polygon])), 1.0)

        for frame in frames:
            pose = tracker.track(frame)
            keypoints = np.array(pose.keypoints, dtype=np.float32)
            tracked_keypoints.append(keypoints)
            center_y = float(np.mean(keypoints[:, 1]))
            heights_m.append(max(0.0, (bed_top - center_y) / bed_height_px * settings.vertical_height_scale_m))

        segmenter = JumpSegmenter(settings.jump_height_threshold_m)
        jumps = segmenter.segment(tracked_keypoints, heights_m, detection.mask)

        jump_results: list[dict[str, object]] = []
        for jump in jumps:
            tof = compute_tof(jump, heights_m, tracked_keypoints, settings.default_fps)
            jump_results.append(
                {
                    "start": jump["start_frame"],
                    "end": jump["end_frame"],
                    "tof": tof["tof"],
                    "peakHeight": tof["peak_height"],
                    "takeoffPoint": tof["takeoff_point"],
                    "landingPoint": tof["landing_point"],
                }
            )

        debug_payload = {
            "sessionId": payload.sessionId,
            "detection": {
                "bed_polygon": detection.bed_polygon,
                "frame_polygon": detection.frame_polygon,
            },
            "calibration": calibration,
            "jumps": jump_results,
        }
        session_key = hashlib.sha256(payload.sessionId.encode("utf-8")).hexdigest()[:32]
        debug_dir = Path(settings.debug_output_dir) / session_key
        debug_dir.mkdir(parents=True, exist_ok=True)
        (debug_dir / "analysis.json").write_text(json.dumps(to_serializable(debug_payload), indent=2), encoding="utf-8")

    return {"sessionId": payload.sessionId, "jumps": jump_results}
