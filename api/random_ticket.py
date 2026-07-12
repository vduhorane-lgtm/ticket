#!/usr/bin/env python3
"""
Vercel serverless function — GET /api/random_ticket
Returns a random 18-digit ticket number and 10-char alphanumeric transaction ID.
"""

from http.server import BaseHTTPRequestHandler
import json
import random
import string


def _cors_headers() -> dict:
    return {
        "Access-Control-Allow-Origin":  "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }


class handler(BaseHTTPRequestHandler):
    """Vercel invokes this class for every request to /api/random_ticket."""

    # ── CORS pre-flight ─────────────────────────────────────────
    def do_OPTIONS(self):
        self.send_response(204)
        for k, v in _cors_headers().items():
            self.send_header(k, v)
        self.end_headers()

    # ── Main handler ────────────────────────────────────────────
    def do_GET(self):
        ticket_num = "".join(random.choices(string.digits, k=18))
        tx_id      = "".join(random.choices(string.ascii_uppercase + string.digits, k=10))

        body = json.dumps({
            "ticket_number":  ticket_num,
            "transaction_id": tx_id,
        }).encode()

        self.send_response(200)
        for k, v in _cors_headers().items():
            self.send_header(k, v)
        self.send_header("Content-Type",   "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
