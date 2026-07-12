#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask web server for the Volcano Express Ltd Ticket Generator.
Serves the frontend and handles ticket generation via POST /generate
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from flask import Flask, request, send_file, jsonify, after_this_request
from functools import wraps
import io
import random
import string
import datetime
from ticket_generator import generate_ticket
import tempfile, os

app = Flask(__name__)

# ── CORS: allow requests from any origin (Live Server, direct, etc.) ─
def cors(response):
    origin = os.environ.get("ALLOWED_ORIGIN", "*")
    response.headers["Access-Control-Allow-Origin"]  = origin
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response

app.after_request(cors)

@app.route("/generate", methods=["OPTIONS"])
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

@app.route("/random_ticket", methods=["GET"])
def random_ticket():
    """Return a random 18-digit ticket number and 8-char transaction ID."""
    ticket_num = "".join(random.choices(string.digits, k=18))
    tx_id = "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
    return jsonify({"ticket_number": ticket_num, "transaction_id": tx_id})

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
    print("Volcano Express Ticket Generator")
    print(f"Open  --> http://{host}:{port}")
    print(f"(also works via Live Server -- API calls go to port {port})")
    app.run(debug=debug, host=host, port=port)
