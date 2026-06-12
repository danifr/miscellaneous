#!/usr/bin/python3
from datetime import datetime
import functools
import logging
import socketserver
from http import server
from threading import Condition
from picamera2 import Picamera2
from picamera2.encoders import MJPEGEncoder
from picamera2.outputs import Output

WIDTH, HEIGHT = 1280, 720  # Common resolutions: 640x480, 1280x720 (720p), 1920x1080 (1080p)
FPS = 10  # Reduce if CPU usage is too high
PORT = 8888

# HTML page served at the root
PAGE = """\
<html>
<head>
<meta charset="utf-8">
<title>Raspberry Pi Streaming</title>
</head>
<body style="background-color: #111; color: #eee; text-align: center; font-family: sans-serif;">
<h1>Live Streaming</h1>
<img src="stream.mjpg" width="WIDTH_VAL" height="HEIGHT_VAL" style="border: 3px solid #333; border-radius: 8px;" />
<p style="margin-top: 10px; font-size: 0.9em; color: #aaa;">CPU temp: <span id="temp">--</span> &nbsp;|&nbsp; <span id="time">--</span></p>
<script>
  function updateTemp() {
    fetch('/temp').then(function(r) { return r.text(); }).then(function(t) { document.getElementById('temp').innerHTML = t; });
  }
  function updateTime() {
    fetch('/time').then(function(r) { return r.text(); }).then(function(t) { document.getElementById('time').innerText = t; });
  }
  updateTemp();
  updateTime();
  setInterval(updateTemp, 10000);
  setInterval(updateTime, 1000);
</script>
</body>
</html>
""".replace('WIDTH_VAL', str(WIDTH)).replace('HEIGHT_VAL', str(HEIGHT))

class StreamingOutput(Output):
    def __init__(self):
        super().__init__()
        self.frame = None
        self.condition = Condition()

    # *args and **kwargs for compatibility with any function signature
    # (regardless of keyframe, timestamp, packet, audio, etc.)
    def outputframe(self, frame, *args, **kwargs):
        with self.condition:
            self.frame = frame
            self.condition.notify_all()

class StreamingHandler(server.BaseHTTPRequestHandler):
    def __init__(self, output, *args, **kwargs):
        self.output = output
        super().__init__(*args, **kwargs)

    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/temp':
            with open('/sys/class/thermal/thermal_zone0/temp') as f:
                temp = round(int(f.read()) / 1000, 1)
            content = f'{temp}&deg;C'.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/time':
            content = datetime.now().strftime('%d-%m-%Y %H:%M:%S').encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Content-Length', len(content))
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
                        self.output.condition.wait()
                        frame = self.output.frame
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
config = picam2.create_video_configuration(main={"size": (WIDTH, HEIGHT)}, controls={"FrameRate": FPS})
picam2.configure(config)
output = StreamingOutput()

try:
    # Start recording using hardware MJPEG encoding (very efficient)
    picam2.start_recording(MJPEGEncoder(), output)
    # Listen on all network interfaces
    address = ('', PORT)
    handler = functools.partial(StreamingHandler, output)
    streaming_server = StreamingServer(address, handler)
    print(f"Streaming server started at http://localhost:{PORT}")
    streaming_server.serve_forever()
finally:
    picam2.stop_recording()
