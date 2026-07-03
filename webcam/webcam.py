#!/usr/bin/python3
import io
import json
import time
from datetime import datetime
import functools
import logging
import socketserver
from http import server
from threading import Condition
from picamera2 import Picamera2
from picamera2.encoders import MJPEGEncoder, Quality
from picamera2.outputs import FileOutput

WIDTH, HEIGHT = 1296, 972  # Matches sensor mode 4 exactly (2x2 binned, full FoV, no ISP rescale needed)
FPS = 10  # Reduce if CPU usage is too high
PORT = 8888

# HTML page served at the root (pre-encoded at startup)
PAGE_BYTES = b"""\
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black">
<title>Raspberry Pi Streaming</title>
</head>
<body style="background-color: #111; color: #eee; text-align: center; font-family: sans-serif; margin: 0; padding: 10px; box-sizing: border-box;">
<style>
  #stream-container { position: relative; display: inline-block; max-width: 100%; }
  #stream { max-width: 100%; max-height: calc(100vh - 100px); border: 3px solid #333; border-radius: 8px; width: auto; height: auto; background: #000; }
  #fs-btn { position: absolute; bottom: 12px; right: 12px; background: rgba(0,0,0,0.6); border: none; color: #fff; font-size: 1.6em; padding: 8px 12px; border-radius: 6px; cursor: pointer; line-height: 1; z-index: 10; touch-action: manipulation; -webkit-tap-highlight-color: transparent; }
  .fullscreen { position: fixed !important; top: 0; left: 0; width: 100vw !important; height: 100vh !important; display: flex !important; align-items: center; justify-content: center; background: #000; z-index: 9999; border: none; border-radius: 0; }
  .fullscreen #stream { max-width: 100vw; max-height: 100vh; border: none; border-radius: 0; object-fit: contain; }
</style>
<h1>Live Streaming</h1>
<div id="stream-container">
  <img id="stream" style="display:none;" />
  <button id="fs-btn" title="Toggle fullscreen">&#x26F6;</button>
</div>
<p style="margin-top: 10px; font-size: 0.9em; color: #aaa;">CPU temp: <span id="temp">--</span> &nbsp;|&nbsp; <span id="time">--</span></p>
<script>
  var img = document.getElementById('stream');

  // Start loading the stream after page renders
  img.src = 'stream.mjpg';
  img.onload = function() { img.style.display = 'block'; };
  img.onerror = function() {
    setTimeout(function() { img.src = 'stream.mjpg?' + Date.now(); }, 2000);
  };

  var container = document.getElementById('stream-container');
  function toggleFullscreen() {
    container.classList.toggle('fullscreen');
  }
  document.getElementById('fs-btn').addEventListener('click', toggleFullscreen);
  img.addEventListener('dblclick', toggleFullscreen);
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') container.classList.remove('fullscreen');
  });

  function updateStatus() {
    fetch('/status').then(function(r) { return r.json(); }).then(function(d) {
      document.getElementById('temp').innerHTML = d.temp + '&deg;C';
      document.getElementById('time').innerText = d.time;
    }).catch(function(){});
  }
  updateStatus();
  setInterval(updateStatus, 5000);
</script>
</body>
</html>
"""

# Cached status to avoid redundant sysfs reads with multiple clients
_status_cache = {"data": None, "expires": 0}
CACHE_TTL = 3  # seconds


def get_status():
    now = time.monotonic()
    if _status_cache["data"] and now < _status_cache["expires"]:
        return _status_cache["data"]
    with open('/sys/class/thermal/thermal_zone0/temp') as f:
        temp = round(int(f.read()) / 1000, 1)
    data = json.dumps({
        "temp": temp,
        "time": datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    }).encode('utf-8')
    _status_cache["data"] = data
    _status_cache["expires"] = now + CACHE_TTL
    return data


class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()


class StreamingHandler(server.BaseHTTPRequestHandler):
    def __init__(self, output, *args, **kwargs):
        self.output = output
        super().__init__(*args, **kwargs)

    def log_message(self, format, *args):
        pass  # Suppress per-request logging to save CPU/IO

    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.send_header('Connection', 'close')
            self.end_headers()
        elif self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(PAGE_BYTES))
            self.send_header('Connection', 'close')
            self.end_headers()
            self.wfile.write(PAGE_BYTES)
        elif self.path == '/status':
            content = get_status()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', len(content))
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'close')
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with self.output.condition:
                        if not self.output.condition.wait(timeout=5):
                            continue  # No frame within timeout, retry
                        frame = self.output.frame
                    if frame is None:
                        continue
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning('Client disconnected %s: %s', self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


# Initialize and configure the camera
picam2 = Picamera2()
config = picam2.create_video_configuration(
    main={"size": (WIDTH, HEIGHT)},
    controls={
        "FrameRate": FPS,
        "Sharpness": 2.0,
        "Contrast": 1.1,
        "Saturation": 1.1,
        "NoiseReductionMode": 2,  # 0=Off, 1=Fast, 2=HighQuality (temporal, runs on ISP)
        "AwbEnable": True,
        "AeEnable": True,
    },
    sensor={"output_size": (1296, 972), "bit_depth": 10}
)
picam2.configure(config)
output = StreamingOutput()

try:
    # Start recording using hardware MJPEG encoding with high quality (GPU-based, no CPU cost)
    picam2.start_recording(MJPEGEncoder(), FileOutput(output), quality=Quality.MEDIUM)
    # Listen on all network interfaces
    address = ('', PORT)
    handler = functools.partial(StreamingHandler, output)
    streaming_server = StreamingServer(address, handler)
    print(f"Streaming server started at http://localhost:{PORT}")
    streaming_server.serve_forever()
finally:
    picam2.stop_recording()
