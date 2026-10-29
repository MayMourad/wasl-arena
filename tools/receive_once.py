"""One-shot local receiver used to save a chat export from the browser pane to disk."""
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

out = sys.argv[1]

class H(BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        open(out, "wb").write(self.rfile.read(n))
        self.send_response(200); self.send_header("Access-Control-Allow-Origin", "*"); self.end_headers()
        self.wfile.write(b"ok")
    def do_OPTIONS(self):
        self.send_response(204)
        for k, v in (("Access-Control-Allow-Origin", "*"), ("Access-Control-Allow-Methods", "POST"), ("Access-Control-Allow-Headers", "*")):
            self.send_header(k, v)
        self.end_headers()
    def log_message(self, *a): pass

s = HTTPServer(("127.0.0.1", 8765), H)
s.handle_request()
s.handle_request() if False else None
