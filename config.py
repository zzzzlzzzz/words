from os import environ


class Config:
    SECRET_KEY = environ.get('WORDS_SECRET_KEY', 'development')
    SQLALCHEMY_DATABASE_URI = environ.get('WORDS_SQLALCHEMY_DATABASE_URI', '')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = dict(pool_pre_ping=True)
    RECAPTCHA_PUBLIC_KEY = environ.get('WORDS_RECAPTCHA_PUBLIC_KEY', '')
    RECAPTCHA_PRIVATE_KEY = environ.get('WORDS_RECAPTCHA_PRIVATE_KEY', '')
    BRAND = environ.get('WORDS_BRAND', 'world')


class DevelopmentConfig(Config):
    pass


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    pass
