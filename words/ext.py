from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_bootstrap import Bootstrap
from flask_bcrypt import Bcrypt
from flask_moment import Moment
from celery import Celery


db = SQLAlchemy()
csrf = CSRFProtect()
bootstrap = Bootstrap()
app_bcrypt = Bcrypt()
moment = Moment()
celery = Celery(__name__.split('.', 1)[0])
