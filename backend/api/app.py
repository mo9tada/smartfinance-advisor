"""Point d'entrée principal de l'application Flask."""

import os

from api import create_app

if __name__ == "__main__":
    # Lancement du serveur API (debug opt-in via FLASK_DEBUG=1, localhost only)
    app = create_app()
    app.run(debug=os.getenv("FLASK_DEBUG") == "1", port=int(os.getenv("PORT", 5000)))
