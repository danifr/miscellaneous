# Webcam Streaming

Live MJPEG streaming from a Raspberry Pi camera over HTTP, using `picamera2`.

## Requirements

```bash
sudo apt install python3-picamera2 --no-install-recommends
```

## Configuration

At the top of `webcam.py`:

```python
WIDTH, HEIGHT = 1280, 720  # Common resolutions: 640x480, 1280x720 (720p), 1920x1080 (1080p)
PORT = 8888
```

## Run manually

```bash
python3 webcam.py
```

Then open `http://<pi-ip>:8888` in your browser.

## Install as a systemd service

1. Download the files:

```bash
sudo curl -o /usr/local/bin/webcam.py https://raw.githubusercontent.com/danifr/miscellaneous/devel/webcam/webcam.py
sudo curl -o /etc/systemd/system/webcam.service https://raw.githubusercontent.com/danifr/miscellaneous/devel/webcam/webcam.service
```

2. Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable webcam
sudo systemctl start webcam
```

3. Check the status:

```bash
sudo systemctl status webcam
```

4. View logs:

```bash
journalctl -u webcam -f
```
