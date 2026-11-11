import json, os
from http.server import BaseHTTPRequestHandler
from app import process_pending_rows

class handler(BaseHTTPRequestHandler):
    def _send(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _authorized(self, header_name="Authorization"):
        secret = os.getenv("CRON_SECRET", "")
        if not secret:
            return False
        value = self.headers.get(header_name, "")
        return value == f"Bearer {secret}" or value == secret

    def do_GET(self):
        # Vercel Cron sends Authorization: Bearer <CRON_SECRET>.
        if not self._authorized():
            return self._send(401, {"error": "Unauthorized"})
        try:
            result = process_pending_rows(max_rows=int(os.getenv("MAX_ROWS_PER_RUN", "5")))
            return self._send(200, {"ok": True, **result})
        except Exception as exc:
            return self._send(500, {"ok": False, "error": str(exc)[:500]})

    def do_POST(self):
        # Use this endpoint as a website form webhook or invoke it from a scheduler.
        if not self._authorized("X-Webhook-Secret") and not self._authorized():
            return self._send(401, {"error": "Unauthorized"})
        try:
            result = process_pending_rows(max_rows=int(os.getenv("MAX_ROWS_PER_RUN", "5")))
            return self._send(200, {"ok": True, **result})
        except Exception as exc:
            return self._send(500, {"ok": False, "error": str(exc)[:500]})
