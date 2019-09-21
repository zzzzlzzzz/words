from os import environ


class Config:
    SECRET_KEY = environ.get('WORDS_SECRET_KEY', 'development')
    SQLALCHEMY_DATABASE_URI = environ.get('WORDS_SQLALCHEMY_DATABASE_URI', '')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = dict(pool_pre_ping=True)


class DevelopmentConfig(Config):
    pass


class TestConfig(Config):
    pass


class ProductionConfig(Config):
    pass
