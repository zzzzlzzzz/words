from os import environ

from flask import Flask
from flask_wtf.csrf import CSRFError

from words.ext import db, csrf, bootstrap, app_bcrypt
from words import user, error


def create_app():
    """
    Create instance of application

    :return: Instance of application
    """
    app = Flask(__name__)
    app.config.from_object(environ.get('WORDS_CONFIG', 'config.DevelopmentConfig'))
    db.init_app(app)
    csrf.init_app(app)
    bootstrap.init_app(app)
    app_bcrypt.init_app(app)
    app.register_blueprint(user.bp)
    app.register_error_handler(Exception, error.page_500)
    app.register_error_handler(500, error.page_500)
    app.register_error_handler(CSRFError, error.page_400)
    app.register_error_handler(400, error.page_400)
    app.register_error_handler(404, error.page_404)
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True
    return app
