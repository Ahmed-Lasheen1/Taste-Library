#!/usr/bin/env python3
"""
Serve the Design Taste Library.

The page reads its JSON with fetch(), which browsers block on file:// URLs, so it
needs a real HTTP origin. This finds a free port, starts a static server, and opens
a browser at it.

It also writes local.json — the absolute path to images/ on *this* machine. Copied
briefs embed that path so Claude Code can open the reference screenshot from any
project directory. It is gitignored and regenerated on every run, which is why the
committed data carries no machine-specific paths.

    python3 serve.py            # auto-pick a port from 8137
    python3 serve.py 4610       # start looking from a specific port
    python3 serve.py --no-open  # don't launch a browser
"""
from __future__ import annotations

import http.server
import json
import os
import socket
import socketserver
import sys
import threading
import webbrowser

ROOT = os.path.dirname(os.path.abspath(__file__))
START_PORT = 8137
PORT_TRIES = 40


def free_port(start: int, tries: int) -> int:
    for port in range(start, start + tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise SystemExit(f"No free port in {start}–{start + tries - 1}.")


def write_local_config() -> str:
    """Point briefs at this machine's images/ directory."""
    images = os.path.join(ROOT, "images") + os.sep
    path = os.path.join(ROOT, "local.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"images_path": images}, fh, indent=2)
        fh.write("\n")
    return images


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def log_message(self, fmt, *args):  # quiet; errors still surface below
        if not str(args[1] if len(args) > 1 else "").startswith(("2", "3")):
            sys.stderr.write("  %s\n" % (fmt % args))

    def end_headers(self):
        # always re-read the JSON, so edits show up on a plain refresh
        self.send_header("Cache-Control", "no-store, max-age=0")
        super().end_headers()


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    start = int(args[0]) if args and args[0].isdigit() else START_PORT
    no_open = "--no-open" in sys.argv

    missing = [f for f in ("index.html", "design-taste-library.json", "vocabulary.json")
               if not os.path.exists(os.path.join(ROOT, f))]
    if missing:
        raise SystemExit("Missing required file(s): " + ", ".join(missing))

    images = write_local_config()
    port = free_port(start, PORT_TRIES)
    url = f"http://localhost:{port}"

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", port), Handler) as httpd:
        # flush explicitly: stdout is block-buffered when piped or redirected,
        # which would otherwise hide the URL until the server exits
        print(f"Design Taste Library  →  {url}", flush=True)
        print(f"  serving  {ROOT}", flush=True)
        print(f"  images   {images}", flush=True)
        print("  Ctrl-C to stop.\n", flush=True)
        if not no_open:
            threading.Timer(0.8, lambda: webbrowser.open(url)).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")


if __name__ == "__main__":
    main()
