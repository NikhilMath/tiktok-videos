#!/usr/bin/env python3
"""Render a sim page to a TikTok-ready video file, hands-free.

Usage:
    python3 render.py pokemon-evolve.html        # full round
    python3 render.py pokemon-evolve.html 8      # quick 8-second test

Starts a local server for this folder, opens the page in headless Google Chrome
with ?autorecord (so it records one full round with sound), waits for the page
to upload the finished video, and saves it to renders/. Needs only Python 3 and
Google Chrome — no other installs.

Browsers record "fragmented" MP4 (no duration in the header), so the file is then
rewritten losslessly into a standard MP4 with macOS's built-in avconvert, which
phones, Photos and TikTok all handle cleanly.
"""
import http.server
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.parse

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(ROOT, "renders")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PORT = 8765
TIMEOUT_SECONDS = 600

done = threading.Event()
result = {}


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        if url.path != "/upload":
            self.send_error(404)
            return
        query = urllib.parse.parse_qs(url.query)
        name = os.path.basename(query.get("name", ["video.mp4"])[0])
        body = self.rfile.read(int(self.headers["Content-Length"]))
        os.makedirs(OUT_DIR, exist_ok=True)
        path = os.path.join(OUT_DIR, name)
        with open(path, "wb") as f:
            f.write(body)
        result.update(path=path, fps=query.get("fps", ["?"])[0], size=len(body))
        self.send_response(204)
        self.end_headers()
        done.set()

    def log_message(self, *args):
        pass  # keep the terminal quiet


def main():
    page = sys.argv[1] if len(sys.argv) > 1 else "pokemon-evolve.html"
    seconds = f"&seconds={sys.argv[2]}" if len(sys.argv) > 2 else ""
    server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    url = f"http://127.0.0.1:{PORT}/{page}?autorecord&upload=/upload{seconds}"
    profile = tempfile.mkdtemp(prefix="render-chrome-")
    chrome = subprocess.Popen(
        [
            CHROME,
            "--headless=new",
            "--autoplay-policy=no-user-gesture-required",  # sound without a tap
            "--window-size=540,960",
            "--disable-background-timer-throttling",
            "--disable-renderer-backgrounding",
            "--disable-backgrounding-occluded-windows",
            f"--user-data-dir={profile}",
            "--no-first-run",
            url,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(f"Recording {page} (one full round, real time)…", flush=True)
    try:
        if not done.wait(TIMEOUT_SECONDS):
            sys.exit("Timed out waiting for the video.")
    finally:
        chrome.terminate()
        server.shutdown()

    path = result["path"]
    if shutil.which("avconvert"):
        raw = path + ".raw.mp4"
        os.replace(path, raw)
        subprocess.run(
            ["avconvert", "--source", raw, "--output", path, "--preset", "PresetPassthrough", "--replace"],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        os.remove(raw)

    mb = os.path.getsize(path) / 1e6
    print(f"Saved {path} ({mb:.1f} MB, ~{result['fps']} fps while recording)")


if __name__ == "__main__":
    main()
