"""WSGI entry point. Gunicorn starts the API with: gunicorn wsgi:app"""
try:  # Local development only: load backend/.env. Production uses real environment variables.
    from dotenv import load_dotenv

    load_dotenv(override=False)
except ImportError:
    pass

from app import create_app

app = create_app()
