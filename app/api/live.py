from __future__ import annotations

import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.config import get_settings
from app.core.jump_segmenter import LEFT_ANKLE_INDEX, RIGHT_ANKLE_INDEX
from app.core.pose_tracker import PoseTracker
from app.core.trampoline_detector import TrampolineDetector
from app.core.utils import decode_frame_payload

router = APIRouter()


@router.websocket("/live")
async def live_analysis(websocket: WebSocket) -> None:
    await websocket.accept()

    settings = get_settings()
    detector = TrampolineDetector()
    tracker = PoseTracker()

    detection = None
    frame_id = 0
    in_air = False
    air_start_frame: int | None = None

    try:
        while True:
            payload = await websocket.receive()
            data = payload.get("bytes") if payload.get("bytes") is not None else payload.get("text")
            if data is None:
                continue

            frame = decode_frame_payload(data)

            if detection is None or detection.confidence < settings.live_recalibration_confidence_threshold:
                detection = detector.detect(frame)

            pose = tracker.track(frame)
            keypoints = np.array(pose.keypoints, dtype=np.float32)
            bed_top = float(min(point[1] for point in detection.bed_polygon))
            bed_height_px = max(float(np.ptp([point[1] for point in detection.bed_polygon])), 1.0)
            center_y = float(np.mean(keypoints[:, 1]))
            height_m = max(0.0, (bed_top - center_y) / bed_height_px * settings.vertical_height_scale_m)

            h, w = detection.mask.shape[:2]
            feet = [keypoints[LEFT_ANKLE_INDEX], keypoints[RIGHT_ANKLE_INDEX]]
            feet_on_bed = False
            for foot in feet:
                x = int(np.clip(foot[0], 0, w - 1))
                y = int(np.clip(foot[1], 0, h - 1))
                if detection.mask[y, x] > 0:
                    feet_on_bed = True
                    break

            is_airborne = (not feet_on_bed) or (height_m > settings.jump_height_threshold_m)

            tof_event = None
            if is_airborne and not in_air:
                in_air = True
                air_start_frame = frame_id
            elif not is_airborne and in_air:
                if air_start_frame is not None:
                    tof_event = {
                        "takeoffFrame": air_start_frame,
                        "landingFrame": frame_id,
                        "tof": (frame_id - air_start_frame) / settings.default_fps,
                    }
                in_air = False
                air_start_frame = None

            response = {
                "frameId": frame_id,
                "keypoints": pose.keypoints,
                "height": height_m,
                "isAirborne": is_airborne,
            }
            if tof_event is not None:
                response["tofEvent"] = tof_event

            detection.confidence = detector.estimate_confidence(frame, detection.mask)
            await websocket.send_json(response)
            frame_id += 1

    except WebSocketDisconnect:
        return
