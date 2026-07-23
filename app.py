#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask web server for the SU DIRECT Ticket Generator.
Serves the frontend and handles ticket generation via POST /api/generate or POST /generate
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from flask import Flask, request, send_file, jsonify
import random
import datetime
from ticket_generator import generate_ticket
import tempfile
import os

app = Flask(__name__)

# ── CORS: allow requests from any origin (Live Server, direct, etc.) ─
def cors(response):
    origin = os.environ.get("ALLOWED_ORIGIN", "*")
    response.headers["Access-Control-Allow-Origin"]  = origin
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response

app.after_request(cors)

@app.route("/api/generate", methods=["OPTIONS"])
@app.route("/generate", methods=["OPTIONS"])
@app.route("/api/random_ticket", methods=["OPTIONS"])
@app.route("/random_ticket", methods=["OPTIONS"])
def handle_options():
    """Pre-flight CORS requests from browser."""
    return "", 204

# ── Read the HTML template from file ─────────────────────────────
with open(os.path.join(os.path.dirname(__file__), "index.html"), encoding="utf-8") as f:
    HTML_TEMPLATE = f.read()

@app.route("/")
def index():
    return HTML_TEMPLATE

@app.route("/api/random_ticket", methods=["GET"])
@app.route("/random_ticket", methods=["GET"])
def random_ticket():
    """Return a random 8-digit ticket number and 8-char transaction ID."""
    ticket_num = str(random.randint(10000000, 99999999))
    tx_id = str(random.randint(10000000, 99999999))
    return jsonify({"ticket_number": ticket_num, "transaction_id": tx_id})

@app.route("/api/generate", methods=["POST"])
@app.route("/generate", methods=["POST"])
def generate():
    """Accept form JSON, generate the ticket PNG, return it as a download."""
    data = request.get_json(force=True)

    now = datetime.datetime.now()
    timestamp = data.get("timestamp") or now.strftime("%Y-%m-%d %H:%M:%S")

    # Build a temp output path
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp.close()

    try:
        generate_ticket(
            company_name   = data.get("company_name",   "SU DIRECT"),
            phone          = data.get("phone",           ""),
            customer       = data.get("customer",        ""),
            from_location  = data.get("from_location",   ""),
            to_location    = data.get("to_location",     ""),
            dep_date       = data.get("dep_date",        now.strftime("%Y-%m-%d")),
            dep_time       = data.get("dep_time",        "14:00"),
            boarding_time  = data.get("boarding_time",   "14:10"),
            ticket_number  = data.get("ticket_number",   ""),
            seat_no        = data.get("seat_no",         "1"),
            plate_no       = data.get("plate_no",        ""),
            price          = data.get("price",           "0 RWF"),
            cashier        = data.get("cashier",         ""),
            payment_method = data.get("payment_method",  "CASH"),
            timestamp      = timestamp,
            transaction_id = data.get("transaction_id",  ""),
            powered_by     = data.get("powered_by",      "TAP&GO/POWERED BY AC Mobility"),
            paper_width    = data.get("paper_width",     "57mm"),
            ticket_mode    = data.get("ticket_mode",     "original_15cm"),
            font_size      = int(data.get("font_size")) if data.get("font_size") else 21,
            line_spacing   = float(data.get("line_spacing")) if data.get("line_spacing") else 1.4,
            qr_size        = int(data.get("qr_size")) if data.get("qr_size") else 325,
            output_path    = tmp.name,
        )
        return send_file(
            tmp.name,
            mimetype="image/png",
            as_attachment=True,
            download_name=f"ticket_{data.get('ticket_number','')}.png",
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # Clean up after sending (best-effort)
        try:
            os.unlink(tmp.name)
        except Exception:
            pass

if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")
    print("SU DIRECT Ticket Generator")
    print(f"Open  --> http://{host}:{port}")
    print(f"(also works via Live Server -- API calls go to port {port})")
    app.run(debug=debug, host=host, port=port)
