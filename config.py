from os import environ
import re


class Config:
    SECRET_KEY = environ.get('WORDS_SECRET_KEY', 'development')
    SQLALCHEMY_DATABASE_URI = environ.get('WORDS_SQLALCHEMY_DATABASE_URI', '')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = dict(pool_pre_ping=True, echo=True)
    RECAPTCHA_PUBLIC_KEY = environ.get('WORDS_RECAPTCHA_PUBLIC_KEY', '')
    RECAPTCHA_PRIVATE_KEY = environ.get('WORDS_RECAPTCHA_PRIVATE_KEY', '')
    BRAND = environ.get('WORDS_BRAND', 'world')
    POST_PER_PAGE = environ.get('WORDS_POST_PER_PAGE', 3)
    LINES_FOR_ANNOTATION = environ.get('WORDS_LINES_PER_ANNOTATION', 3)
    CELERY = dict(
        broker_url=environ.get('WORDS_CELERY_BROKER_URL', ''),
        broker_connection_max_retries=None,
        worker_max_memory_per_child=256 * 1024,
        task_default_queue='default',
        task_routes={
            'words.tasks.repost.*': {
                'queue': 'repost',
            },
        },
    )


class DevelopmentConfig(Config):
    pass


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    pass
