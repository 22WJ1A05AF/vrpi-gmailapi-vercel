
import json
import os
import logging
from http.server import BaseHTTPRequestHandler

from app import process_pending_rows

log = logging.getLogger("vrpi.process")


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

    def _process(self):
        try:
            max_rows = int(os.getenv("MAX_ROWS_PER_RUN", "1"))

            if max_rows < 1 or max_rows > 5:
                return self._send(
                    400,
                    {"ok": False, "error": "MAX_ROWS_PER_RUN must be between 1 and 5."}
                )

            result = process_pending_rows(max_rows=max_rows)
            return self._send(200, {"ok": True, **result})

        except Exception:
            log.exception("Internship processing failed")
            return self._send(
                500,
                {
                    "ok": False,
                    "error": "Processing failed. Check Vercel function logs."
                }
            )

    def do_GET(self):
        if not self._authorized():
            return self._send(401, {"error": "Unauthorized"})

        return self._process()

    def do_POST(self):
        if not self._authorized("X-Webhook-Secret") and not self._authorized():
            return self._send(401, {"error": "Unauthorized"})

        return self._process()
