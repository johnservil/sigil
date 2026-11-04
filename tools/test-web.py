#!/usr/bin/env python3
"""Run the browser bundle, DOM transformation and playground tests in Chromium.

    python3 tools/test-web.py

Requires chromium on PATH. Serves only on loopback; creates no project files.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import html
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
    # The volunteers' font test, on its own: a result in the form
    # tools/import-fonts.py reads, thanks, and a wall of every letter.
    with tempfile.TemporaryDirectory(prefix="sigil-browser-") as profile:
        page = subprocess.run([
            "chromium", "--headless", "--no-sandbox", "--disable-gpu",
            f"--user-data-dir={profile}", "--virtual-time-budget=10000", "--dump-dom",
            f"http://127.0.0.1:{server.server_port}/web/check.html",
        ], text=True, capture_output=True, timeout=120).stdout
    lines = html.unescape(re.search(r'<pre id="out">(.*?)</pre>', page, re.S)[1]).split("\n")
    assert re.fullmatch(r"Sigil font test 0\.2, page \d+: \d+ candidates, set [0-9a-f]{12}", lines[1]), lines[1]
    assert re.fullmatch(r"Drawn in full: \d+ of \d+ scripts", lines[2]) and lines[3] == "", lines[2:4]
    assert all(re.fullmatch(r"[A-Za-z_]+: \d+/\d+( missing [0-9a-f -]+)?", l) for l in lines[4:]), lines[4:]
    assert re.search(r'<p class="thanks" id="thanks">Thank you', page), "the page thanks its visitor"
    assert "title%3DFonts%200.2" in page or "title=Fonts%200.2" in page, "Send opens a round 0.2 issue"
    wall = html.unescape(re.sub(r"<[^>]+>", "", re.search(r'<div id="wall">(.*?)</div>', page, re.S)[1]))
    assert len(set(wall) - set("0123456789abcdef\u200e")) == 2048, "the wall uses every letter"
    print("PASS: the font test page")
finally:
    server.shutdown()
    server.server_close()
    thread.join()
