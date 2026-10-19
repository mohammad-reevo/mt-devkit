#!/usr/bin/env python3
"""Serve one value from the agent login file to a single localhost GET, then exit.

playwright-isolated's code sandbox has no `fs`, `require` or dynamic import, so the browser
fetches the password server-side (`page.request.get`) instead of the agent typing it — the
secret never enters the transcript.

  serve_secret.py [KEY]     # default AGENT_PASSWORD; port 8931; run in the background
"""

import http.server
import pathlib
import re
import sys

LOGIN_FILE = pathlib.Path.home() / ".config/reevo/agent-login.env"
PORT = 8931

key = sys.argv[1] if len(sys.argv) > 1 else "AGENT_PASSWORD"
match = re.search(rf"^{re.escape(key)}=(.*)$", LOGIN_FILE.read_text(), re.M)
if not match:
    sys.exit(f"{key} not in {LOGIN_FILE}")
value = match.group(1).strip().encode()


class OneShot(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(value)

    def log_message(self, *_: object) -> None:
        pass


http.server.HTTPServer(("127.0.0.1", PORT), OneShot).handle_request()
