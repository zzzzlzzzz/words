from os import environ

from flask import Flask
from flask_wtf.csrf import CSRFError
from flask_bootstrap import WebCDN

from words.ext import db, csrf, bootstrap, app_bcrypt, moment
from words.models import UserStatus
from words import user, edit, post, error


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
    app.extensions['bootstrap']['cdns'].update({'simplemde-css': WebCDN('//cdn.jsdelivr.net/simplemde/latest/'),
                                                'simplemde-js': WebCDN('//cdn.jsdelivr.net/simplemde/latest/'),
                                                'infinite-scroll': WebCDN('//unpkg.com/infinite-scroll@3/dist/'), })
    app_bcrypt.init_app(app)
    moment.init_app(app)
    app.register_blueprint(user.bp)
    app.register_blueprint(edit.bp)
    app.register_blueprint(post.bp)
    #app.add_url_rule('/', 'index', methods=('GET', ))
    app.register_error_handler(Exception, error.page_500)
    app.register_error_handler(500, error.page_500)
    app.register_error_handler(CSRFError, error.page_400)
    app.register_error_handler(400, error.page_400)
    app.register_error_handler(404, error.page_404)

    @app.before_request
    def app_before_request():
        user.load_user()

    @app.context_processor
    def app_context_processor():
        return {'UserStatus': UserStatus}

    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True
    return app