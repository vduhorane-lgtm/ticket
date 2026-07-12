#!/usr/bin/env python3
"""
Vercel serverless function — POST /api/generate
Accepts ticket form data as JSON and returns a ticket PNG image.
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import datetime
import tempfile

# Make the project root importable (ticket_generator.py lives there)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ticket_generator import generate_ticket  # noqa: E402


def _cors_headers() -> dict:
    return {
        "Access-Control-Allow-Origin":  "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }


class handler(BaseHTTPRequestHandler):
    """Vercel invokes this class for every request to /api/generate."""

    # ── CORS pre-flight ─────────────────────────────────────────
    def do_OPTIONS(self):
        self.send_response(204)
        for k, v in _cors_headers().items():
            self.send_header(k, v)
        self.end_headers()

    # ── Main handler ────────────────────────────────────────────
    def do_POST(self):
        # 1. Parse JSON body
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw    = self.rfile.read(length)
            data   = json.loads(raw) if raw else {}
        except Exception:
            self._json_error(400, "Invalid JSON body")
            return

        now       = datetime.datetime.now()
        timestamp = data.get("timestamp") or now.strftime("%Y-%m-%d %H:%M:%S")

        # 2. Write to /tmp — the only writable path in Vercel's Lambda runtime
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False, dir="/tmp")
        tmp.close()

        try:
            generate_ticket(
                company_name   = data.get("company_name",   "Volcano Express Ltd"),
                phone          = data.get("phone",           "null"),
                customer       = data.get("customer",        ""),
                from_location  = data.get("from_location",   ""),
                to_location    = data.get("to_location",     ""),
                dep_date       = data.get("dep_date",        now.strftime("%Y-%m-%d")),
                dep_time       = data.get("dep_time",        "14:00"),
                boarding_time  = data.get("boarding_time",   "14:10"),
                ticket_number  = data.get("ticket_number",   ""),
                seat_no        = data.get("seat_no",         "1"),
                plate_no       = data.get("plate_no",        ""),
                price          = data.get("price",           "0RWF"),
                cashier        = data.get("cashier",         ""),
                timestamp      = timestamp,
                transaction_id = data.get("transaction_id",  ""),
                output_path    = tmp.name,
            )

            with open(tmp.name, "rb") as f:
                png_bytes = f.read()

            ticket_number = data.get("ticket_number", "new")
            filename      = f"ticket_{ticket_number}.png"

            # 3. Stream PNG back to the client
            self.send_response(200)
            for k, v in _cors_headers().items():
                self.send_header(k, v)
            self.send_header("Content-Type",        "image/png")
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.send_header("Content-Length",      str(len(png_bytes)))
            self.end_headers()
            self.wfile.write(png_bytes)

        except Exception as e:
            self._json_error(500, str(e))

        finally:
            try:
                os.unlink(tmp.name)
            except Exception:
                pass

    # ── Helper ──────────────────────────────────────────────────
    def _json_error(self, code: int, message: str):
        body = json.dumps({"error": message}).encode()
        self.send_response(code)
        for k, v in _cors_headers().items():
            self.send_header(k, v)
        self.send_header("Content-Type",   "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
