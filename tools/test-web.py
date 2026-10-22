#!/usr/bin/env python3
"""Run the browser bundle, DOM transformation and playground tests in Chromium.

    python3 tools/test-web.py

Requires chromium on PATH. Serves only on loopback; creates no project files.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
import subprocess
import tempfile
import threading

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(ROOT)))
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
try:
    with tempfile.TemporaryDirectory(prefix="sigil-browser-") as profile:
        result = subprocess.run([
            "chromium", "--headless", "--no-sandbox", "--disable-gpu",
            f"--user-data-dir={profile}", "--virtual-time-budget=10000", "--dump-dom",
            f"http://127.0.0.1:{server.server_port}/web/tests.html",
        ], text=True, capture_output=True, timeout=120)
    assert result.returncode == 0, result.stderr
    match = re.search(r'<pre id="result">(.*?)</pre>', result.stdout, re.S)
    assert match, result.stdout[-2000:]
    assert match[1].startswith("PASS:"), match[1]
    print(match[1])
finally:
    server.shutdown()
    server.server_close()
    thread.join()
