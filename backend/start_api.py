import sys
import os

# Add current directory to path so 'api' can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api import create_app

if __name__ == "__main__":
    app = create_app()
    print(" Flask API running on http://localhost:5000")
    print(" Endpoints available at /api/...")
    # Debug mode (Werkzeug debugger) must never be reachable from the network,
    # so it is opt-in and binds to localhost only.
    debug = os.getenv("FLASK_DEBUG") == "1"
    app.run(debug=debug, port=int(os.getenv("PORT", 5000)), host="127.0.0.1" if debug else "0.0.0.0")