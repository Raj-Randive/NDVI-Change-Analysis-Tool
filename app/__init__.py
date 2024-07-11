from flask import Flask
from .celery import celery

def create_app():
    app = Flask(__name__)
    # Other app initialization code
    return app

app = create_app()