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

## Deploy to Render (Lovable integration)

1. **Deploy the backend** — Go to [render.com](https://render.com), create a new service from this repo, and Render will use `render.yaml` automatically.

2. **Set the CORS origin** — After your Render service is live, go to its *Environment* settings and set:
   ```
   CORS_ORIGINS=https://your-app.lovable.app
   ```
   Use `*` during development to allow any origin.

3. **Wire Lovable** — In your Lovable project, add an environment variable:
   ```
   VITE_API_URL=https://jumptek-engine.onrender.com
   ```
   Then call the API from your frontend:
   - REST: `POST $VITE_API_URL/process-video`
   - WebSocket: `wss://$VITE_API_URL/live`
