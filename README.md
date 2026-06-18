# JumpTek 2.0.1 AI Engine

Production-ready FastAPI service for trampoline motion analysis.  
The engine ships with a **self-contained JavaScript widget** (`widget/jumptek-widget.js`)
that lets any web page embed a live jump-analysis panel without coupling to the backend stack.

## Features

- Live camera analysis via WebSocket (`/live`)
- Uploaded video analysis (`POST /process-video`)
- Trampoline detection and calibration
- Pose tracking and smoothing
- Jump segmentation
- Time-of-flight (ToF), peak height, and drift metrics
- **Embeddable JS widget** with a clean host-page API

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
widget/
  jumptek-widget.js   ← embeddable widget
  example.html        ← host-page integration example
```

## Run

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

By default the server accepts cross-origin requests from **any** origin (`*`).
To restrict to specific origins set the `CORS_ALLOW_ORIGINS` environment variable
(comma-separated list):

```bash
CORS_ALLOW_ORIGINS="https://myapp.example.com,https://dashboard.example.com" \
  uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API

- `GET /health`
- `POST /process-video`
- `WS /live`

## Test

```bash
pytest -q
```

---

## Embedding the Widget

The widget is a **zero-dependency, self-contained JavaScript file**.
No build step is required on the host page.

### Quick start (3 steps)

```html
<!-- 1. Load the widget script -->
<script src="https://your-cdn.example.com/jumptek-widget.js"></script>

<!-- 2. Reserve a container anywhere on your page -->
<div id="jumptek-host"></div>

<!-- 3. Initialise -->
<script>
  JumpTekWidget.init({
    container: '#jumptek-host',          // CSS selector or DOM element
    serverUrl: 'wss://your-server.example.com',  // JumpTek backend URL
    fps: 15,                             // capture frames per second (default: 15)
    onEvent: function (data) {           // optional callback for every server message
      console.log(data);
    }
  });
</script>
```

Open `widget/example.html` in your browser alongside a running local server to see
a complete working integration.

### Configuration options

| Option      | Type             | Default                    | Description                                         |
|-------------|------------------|----------------------------|-----------------------------------------------------|
| `container` | string\|Element  | *(required)*               | CSS selector or DOM node to mount the widget into   |
| `serverUrl` | string           | `ws://localhost:8000`      | WebSocket base URL of the JumpTek backend           |
| `fps`       | number           | `15`                       | Target frames per second sent to the server         |
| `width`     | number           | `640`                      | Camera capture width (pixels)                       |
| `height`    | number           | `480`                      | Camera capture height (pixels)                      |
| `onEvent`   | function         | —                          | Callback invoked with each parsed server message    |

### Element-attribute configuration

Options can also be set directly on the container element, which is useful when
the host page is rendered server-side:

```html
<div
  id="jumptek-host"
  data-jumptek-server="wss://your-server.example.com"
  data-jumptek-fps="15"
></div>
```

Attributes are read during `init()` and are **overridden** by any matching JS
option passed to the same call.

### Tearing down

```js
JumpTekWidget.destroy();
```

This stops the WebSocket connection, releases the camera stream, and removes the
widget DOM and its injected styles from the page.

### Server events (`onEvent` payload)

Every WebSocket message from the server is forwarded to `onEvent` as a parsed
JavaScript object.  Key fields:

```jsonc
{
  "frameId": 42,
  "keypoints": [[x, y], ...],   // 17-point pose keypoints
  "height": 0.34,               // estimated height above bed (metres)
  "isAirborne": true,
  // present only when a jump completes:
  "tofEvent": {
    "takeoffFrame": 30,
    "landingFrame": 55,
    "tof": 0.833                // time-of-flight in seconds
  }
}
```

### CORS

The JumpTek backend uses FastAPI's built-in CORS middleware.
Allowed origins are controlled by the `CORS_ALLOW_ORIGINS` environment variable
(default `*`).  Set it to the exact origin(s) of your host page for production
deployments.
