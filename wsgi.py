# Point d'entrée gunicorn : l'application est créée une seule fois dans app.py,
# avec la configuration donnée par FLASK_ENV (production dans le conteneur).
from app import app as application

if __name__ == "__main__":
    application.run(host='0.0.0.0', port=5000, debug=True)
