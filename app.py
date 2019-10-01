from words import create_app
from words.ext import celery


flask_app = create_app()
celery_app = celery
