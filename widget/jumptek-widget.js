/**
 * JumpTek Widget v2.0.1
 *
 * Self-contained embeddable widget for the JumpTek AI Engine.
 * Connects to the JumpTek FastAPI backend via WebSocket and streams
 * live camera frames for real-time trampoline jump analysis.
 *
 * Public API
 * ----------
 *   JumpTekWidget.init(options)   – mount the widget into a host element
 *   JumpTekWidget.destroy()       – unmount and clean up
 *
 * Options
 * -------
 *   container   {string|Element}  CSS selector or DOM element to mount into (required)
 *   serverUrl   {string}          WebSocket base URL of the JumpTek backend
 *                                 (default: "ws://localhost:8000")
 *   fps         {number}          Target capture framerate sent to the server (default: 15)
 *   width       {number}          Video capture width in pixels (default: 640)
 *   height      {number}          Video capture height in pixels (default: 480)
 *   onEvent     {function}        Callback invoked with each server message object
 *
 * Element-attribute configuration (alternative to JS options)
 * -----------------------------------------------------------
 *   data-jumptek-server   WebSocket base URL
 *   data-jumptek-fps      Target FPS
 *
 * Usage example
 * -------------
 *   <div id="jumptek-host"></div>
 *   <script src="jumptek-widget.js"></script>
 *   <script>
 *     JumpTekWidget.init({
 *       container: '#jumptek-host',
 *       serverUrl: 'wss://your-server.example.com',
 *       fps: 15,
 *       onEvent: function(data) { console.log(data); }
 *     });
 *   </script>
 */
(function (global) {
  'use strict';

  // ── CSS injected into the host page (scoped to .jtw-* classes) ──────────
  var WIDGET_CSS = [
    '.jtw-container{',
    '  position:relative;',
    '  display:flex;',
    '  flex-direction:column;',
    '  align-items:center;',
    '  gap:8px;',
    '  font-family:system-ui,sans-serif;',
    '  background:#111;',
    '  color:#eee;',
    '  border-radius:8px;',
    '  padding:12px;',
    '  box-sizing:border-box;',
    '  min-width:320px;',
    '}',
    '.jtw-video{',
    '  width:100%;',
    '  border-radius:6px;',
    '  background:#000;',
    '}',
    '.jtw-canvas{',
    '  display:none;',
    '}',
    '.jtw-stats{',
    '  width:100%;',
    '  display:flex;',
    '  justify-content:space-around;',
    '  gap:8px;',
    '}',
    '.jtw-stat{',
    '  background:#222;',
    '  border-radius:6px;',
    '  padding:8px 12px;',
    '  flex:1;',
    '  text-align:center;',
    '}',
    '.jtw-stat-label{',
    '  font-size:10px;',
    '  text-transform:uppercase;',
    '  letter-spacing:1px;',
    '  color:#888;',
    '}',
    '.jtw-stat-value{',
    '  font-size:22px;',
    '  font-weight:700;',
    '  color:#4fc;',
    '  min-height:28px;',
    '}',
    '.jtw-badge{',
    '  position:absolute;',
    '  top:16px;',
    '  left:16px;',
    '  background:#4fc;',
    '  color:#111;',
    '  font-size:10px;',
    '  font-weight:700;',
    '  padding:2px 8px;',
    '  border-radius:99px;',
    '  opacity:0;',
    '  transition:opacity 0.3s;',
    '}',
    '.jtw-badge.jtw-visible{opacity:1;}',
    '.jtw-controls{',
    '  display:flex;',
    '  gap:8px;',
    '}',
    '.jtw-btn{',
    '  padding:6px 18px;',
    '  border:none;',
    '  border-radius:6px;',
    '  cursor:pointer;',
    '  font-size:13px;',
    '  font-weight:600;',
    '}',
    '.jtw-btn-start{background:#4fc;color:#111;}',
    '.jtw-btn-stop{background:#f44;color:#fff;}',
    '.jtw-status{font-size:11px;color:#888;}',
    '.jtw-event-log{',
    '  width:100%;',
    '  max-height:80px;',
    '  overflow-y:auto;',
    '  background:#1a1a1a;',
    '  border-radius:6px;',
    '  padding:4px 8px;',
    '  font-size:11px;',
    '  font-family:monospace;',
    '}',
  ].join('');

  // ── Internal state ───────────────────────────────────────────────────────
  var _mounted = false;
  var _ws = null;
  var _stream = null;
  var _frameTimer = null;
  var _styleEl = null;
  var _container = null;
  var _canvas = null;
  var _video = null;
  var _statusEl = null;
  var _logEl = null;
  var _airborneEl = null;
  var _heightEl = null;
  var _tofEl = null;
  var _badge = null;
  var _opts = {};

  // ── Helpers ──────────────────────────────────────────────────────────────
  function qs(selector, root) {
    return (root || document).querySelector(selector);
  }

  function injectStyles() {
    if (_styleEl) return;
    _styleEl = document.createElement('style');
    _styleEl.setAttribute('data-jumptek-widget', '');
    _styleEl.textContent = WIDGET_CSS;
    document.head.appendChild(_styleEl);
  }

  function removeStyles() {
    if (_styleEl && _styleEl.parentNode) {
      _styleEl.parentNode.removeChild(_styleEl);
    }
    _styleEl = null;
  }

  function setStatus(msg) {
    if (_statusEl) _statusEl.textContent = msg;
  }

  function appendLog(msg) {
    if (!_logEl) return;
    var line = document.createElement('div');
    line.textContent = msg;
    _logEl.appendChild(line);
    _logEl.scrollTop = _logEl.scrollHeight;
    // Keep log short
    while (_logEl.children.length > 20) {
      _logEl.removeChild(_logEl.firstChild);
    }
  }

  // ── Build DOM inside the host container ─────────────────────────────────
  function buildDOM(host) {
    host.innerHTML = '';

    var outer = document.createElement('div');
    outer.className = 'jtw-container';

    _badge = document.createElement('div');
    _badge.className = 'jtw-badge';
    _badge.textContent = 'AIRBORNE';
    outer.appendChild(_badge);

    _video = document.createElement('video');
    _video.className = 'jtw-video';
    _video.setAttribute('autoplay', '');
    _video.setAttribute('playsinline', '');
    _video.muted = true;
    outer.appendChild(_video);

    _canvas = document.createElement('canvas');
    _canvas.className = 'jtw-canvas';
    outer.appendChild(_canvas);

    var stats = document.createElement('div');
    stats.className = 'jtw-stats';

    _airborneEl = makeStat('In Air', '–', stats);
    _heightEl = makeStat('Height (m)', '–', stats);
    _tofEl = makeStat('ToF (s)', '–', stats);

    outer.appendChild(stats);

    var controls = document.createElement('div');
    controls.className = 'jtw-controls';

    var startBtn = document.createElement('button');
    startBtn.className = 'jtw-btn jtw-btn-start';
    startBtn.textContent = 'Start';
    startBtn.addEventListener('click', startSession);
    controls.appendChild(startBtn);

    var stopBtn = document.createElement('button');
    stopBtn.className = 'jtw-btn jtw-btn-stop';
    stopBtn.textContent = 'Stop';
    stopBtn.addEventListener('click', stopSession);
    controls.appendChild(stopBtn);

    outer.appendChild(controls);

    _statusEl = document.createElement('div');
    _statusEl.className = 'jtw-status';
    _statusEl.textContent = 'Ready – press Start to begin';
    outer.appendChild(_statusEl);

    _logEl = document.createElement('div');
    _logEl.className = 'jtw-event-log';
    outer.appendChild(_logEl);

    host.appendChild(outer);
  }

  function makeStat(label, value, parent) {
    var stat = document.createElement('div');
    stat.className = 'jtw-stat';

    var lbl = document.createElement('div');
    lbl.className = 'jtw-stat-label';
    lbl.textContent = label;
    stat.appendChild(lbl);

    var val = document.createElement('div');
    val.className = 'jtw-stat-value';
    val.textContent = value;
    stat.appendChild(val);

    parent.appendChild(stat);
    return val;
  }

  // ── Session lifecycle ────────────────────────────────────────────────────
  function startSession() {
    if (_ws && _ws.readyState === WebSocket.OPEN) return;

    var wsBase = (_opts.serverUrl || 'ws://localhost:8000').replace(/\/$/, '');
    var wsUrl = wsBase + '/live';

    setStatus('Connecting to ' + wsUrl + ' …');

    _ws = new WebSocket(wsUrl);
    _ws.binaryType = 'arraybuffer';

    _ws.onopen = function () {
      setStatus('Connected – starting camera …');
      startCamera();
    };

    _ws.onmessage = function (evt) {
      var data;
      try {
        data = JSON.parse(typeof evt.data === 'string' ? evt.data : new TextDecoder().decode(evt.data));
      } catch (e) {
        return;
      }
      handleServerMessage(data);
      if (typeof _opts.onEvent === 'function') {
        _opts.onEvent(data);
      }
    };

    _ws.onerror = function () {
      setStatus('WebSocket error. Is the JumpTek server running?');
    };

    _ws.onclose = function () {
      setStatus('Disconnected');
      stopCapture();
    };
  }

  function stopSession() {
    if (_ws) {
      _ws.close();
      _ws = null;
    }
    stopCapture();
    setStatus('Stopped');
  }

  function startCamera() {
    var constraints = {
      video: { width: _opts.width || 640, height: _opts.height || 480 },
    };
    navigator.mediaDevices
      .getUserMedia(constraints)
      .then(function (stream) {
        _stream = stream;
        _video.srcObject = stream;
        _video.play();
        _video.onloadedmetadata = function () {
          _canvas.width = _video.videoWidth;
          _canvas.height = _video.videoHeight;
          startCapture();
        };
        setStatus('Live – analysing …');
      })
      .catch(function (err) {
        setStatus('Camera error: ' + err.message);
      });
  }

  function startCapture() {
    var fps = _opts.fps || 15;
    var interval = Math.round(1000 / fps);
    _frameTimer = setInterval(captureAndSend, interval);
  }

  function stopCapture() {
    clearInterval(_frameTimer);
    _frameTimer = null;
    if (_stream) {
      _stream.getTracks().forEach(function (t) { t.stop(); });
      _stream = null;
    }
    if (_video) {
      _video.srcObject = null;
    }
  }

  function captureAndSend() {
    if (!_ws || _ws.readyState !== WebSocket.OPEN) return;
    var ctx = _canvas.getContext('2d');
    ctx.drawImage(_video, 0, 0, _canvas.width, _canvas.height);
    _canvas.toBlob(function (blob) {
      if (!blob) return;
      blob.arrayBuffer().then(function (buf) {
        if (_ws && _ws.readyState === WebSocket.OPEN) {
          _ws.send(buf);
        }
      });
    }, 'image/jpeg', 0.7);
  }

  // ── Render server messages ───────────────────────────────────────────────
  function handleServerMessage(data) {
    if (typeof data.isAirborne === 'boolean') {
      _airborneEl.textContent = data.isAirborne ? 'YES' : 'NO';
      if (_badge) {
        if (data.isAirborne) {
          _badge.classList.add('jtw-visible');
        } else {
          _badge.classList.remove('jtw-visible');
        }
      }
    }
    if (typeof data.height === 'number') {
      _heightEl.textContent = data.height.toFixed(2);
    }
    if (data.tofEvent) {
      var tofVal = typeof data.tofEvent.tof === 'number' ? data.tofEvent.tof.toFixed(3) : '–';
      _tofEl.textContent = tofVal;
      appendLog(
        'Jump #' + data.frameId +
        ' | ToF: ' + tofVal + 's' +
        ' | takeoff: ' + data.tofEvent.takeoffFrame +
        ' landing: ' + data.tofEvent.landingFrame
      );
    }
  }

  // ── Public API ───────────────────────────────────────────────────────────
  var JumpTekWidget = {
    /**
     * Mount the widget into a host container.
     *
     * @param {object} options
     * @param {string|Element} options.container  CSS selector or DOM node
     * @param {string}         [options.serverUrl]  WebSocket base URL (default: ws://localhost:8000)
     * @param {number}         [options.fps]        Capture FPS (default: 15)
     * @param {number}         [options.width]      Capture width (default: 640)
     * @param {number}         [options.height]     Capture height (default: 480)
     * @param {function}       [options.onEvent]    Callback for each server message
     */
    init: function (options) {
      if (_mounted) this.destroy();

      _opts = options || {};

      // Resolve container
      var host = typeof _opts.container === 'string'
        ? qs(_opts.container)
        : _opts.container;

      if (!host) {
        throw new Error('JumpTekWidget.init: container not found – ' + _opts.container);
      }

      // Allow data-attribute overrides on the container element
      if (host.dataset) {
        if (host.dataset.jumptekServer && !_opts.serverUrl) {
          _opts.serverUrl = host.dataset.jumptekServer;
        }
        if (host.dataset.jumptekFps && !_opts.fps) {
          _opts.fps = Number(host.dataset.jumptekFps);
        }
      }

      _container = host;
      injectStyles();
      buildDOM(host);
      _mounted = true;
    },

    /**
     * Tear down the widget: stop any active session, remove DOM, remove styles.
     */
    destroy: function () {
      stopSession();
      if (_container) {
        _container.innerHTML = '';
        _container = null;
      }
      removeStyles();
      _mounted = false;
      _opts = {};
    },
  };

  // Expose globally
  global.JumpTekWidget = JumpTekWidget;

})(typeof window !== 'undefined' ? window : this);
