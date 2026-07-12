import os
import sys
from waitress import serve
from app import app

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Volcano Express Ticket Generator Production WSGI server...")
    print(f"Server is listening on http://{host}:{port}")
    serve(app, host=host, port=port, threads=4)
