from os import environ

from flask import Flask

from words.ext import db


def create_app():
    """
    Create instance of application

    :return: Instance of application
    """
    app = Flask(__name__)
    app.config.from_object(environ.get('WORDS_CONFIG', 'config.DevelopmentConfig'))
    db.init_app(app)
    return app
