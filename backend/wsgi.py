"""WSGI entry point. Gunicorn starts the API with: gunicorn wsgi:app"""
from app import create_app

app = create_app()
