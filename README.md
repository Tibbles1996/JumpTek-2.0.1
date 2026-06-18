# JumpTek 2.0.1 AI Engine

Production-ready FastAPI service for trampoline motion analysis.

## Features

- Live camera analysis via WebSocket (`/live`)
- Uploaded video analysis (`POST /process-video`)
- Trampoline detection and calibration
- Pose tracking and smoothing
- Jump segmentation
- Time-of-flight (ToF), peak height, and drift metrics

## Project Layout

```text
app/
  api/
    health.py
    live.py
    process_video.py
  core/
    calibration.py
    jump_segmenter.py
    pose_tracker.py
    tof.py
    trampoline_detector.py
    utils.py
  models/
    yolo/
    vitpose/
  config.py
  main.py
tests/
```

## Run

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## API

- `GET /health`
- `POST /process-video`
- `WS /live`

## Test

```bash
pytest -q
```
