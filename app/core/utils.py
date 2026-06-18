from __future__ import annotations

import base64
from urllib.parse import urlparse

import ffmpeg
from pathlib import Path
from typing import Any

import numpy as np

try:
    import cv2
except Exception:  # pragma: no cover - optional dependency
    cv2 = None


def download_video(url: str, destination: Path) -> Path:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only http/https URLs are supported")

    destination.parent.mkdir(parents=True, exist_ok=True)
    (
        ffmpeg.input(url)
        .output(str(destination), c="copy")
        .overwrite_output()
        .run(capture_stdout=True, capture_stderr=True)
    )
    return destination


def extract_frames(video_path: Path, max_frames: int | None = None) -> list[np.ndarray]:
    if cv2 is None:
        raise RuntimeError("OpenCV is required to extract frames")

    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise ValueError(f"Unable to open video: {video_path}")

    frames: list[np.ndarray] = []
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        frames.append(frame)
        if max_frames is not None and len(frames) >= max_frames:
            break
    capture.release()
    return frames


def decode_frame_payload(payload: bytes | str) -> np.ndarray:
    raw = payload
    if isinstance(payload, str):
        raw = base64.b64decode(payload)
    array = np.frombuffer(raw, dtype=np.uint8)
    if cv2 is None:
        raise RuntimeError("OpenCV is required to decode frame payloads")
    frame = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("Invalid frame payload")
    return frame


def to_serializable(obj: Any) -> Any:
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.float32, np.float64, np.float16)):
        return float(obj)
    if isinstance(obj, (np.int32, np.int64, np.int16, np.uint8)):
        return int(obj)
    if isinstance(obj, dict):
        return {key: to_serializable(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [to_serializable(item) for item in obj]
    if isinstance(obj, tuple):
        return [to_serializable(item) for item in obj]
    return obj

