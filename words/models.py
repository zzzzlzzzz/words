import enum
from datetime import datetime

import markdown2
from flask import Markup, current_app

from words.ext import db


class UserStatus(enum.Enum):
    GUEST = 1
    NORMAL = 2
    ADMINISTRATOR = 3


class Service(enum.Enum):
    TELEGRAM = 1


class User(db.Model):
    __tablename__ = 'user'

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(16), nullable=False, unique=True)
    password = db.Column(db.Binary(128), nullable=False)
    status = db.Column(db.String(32), nullable=False, default=UserStatus.NORMAL.name)
    registered = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    edited = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    logotype = db.Column(db.Text, nullable=False)
    first_name = db.Column(db.String(32), nullable=False, default='')
    last_name = db.Column(db.String(32), nullable=False, default='')
    about = db.Column(db.Text, nullable=False, default='')
    about_time = db.Column(db.Integer, nullable=False, default=0)
    service_subscribes = db.relationship('ServiceSubscribe', back_populates='user', cascade='all, delete-orphan', passive_deletes=True)
    posts = db.relationship('Post', back_populates='user', cascade='all, delete-orphan', passive_deletes=True)

    def __init__(self, username, password, logotype):
        self.username = username
        self.password = password
        self.logotype = logotype

    def serialize(self):
        """Serialize user-object to pass template engine"""
        return dict(user_id=self.user_id,
                    username=self.username,
                    registered=self.registered,
                    edited=self.edited,
                    logotype=self.logotype,
                    first_name=self.first_name,
                    last_name=self.last_name,
                    about=Markup(markdown2.markdown(self.about)),
                    about_time=self.about_time)


class ServiceSubscribe(db.Model):
    __tablename__ = 'service_subscribe'

    service_subscribe_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id', ondelete='CASCADE'), nullable=False)
    user = db.relationship('User', back_populates='service_subscribes')
    service = db.Column(db.String(32), nullable=False)
    credentials = db.Column(db.JSON, nullable=False)

    def __init__(self, service, credentials):
        self.service = service
        self.credentials = credentials


class Post(db.Model):
    __tablename__ = 'post'
    __table_args__ = (
        db.UniqueConstraint('user_id', 'title', name='post_user_id_title_key'),
    )

    post_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id', ondelete='CASCADE'), nullable=False)
    user = db.relationship('User', back_populates='posts')
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    edited = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    url = db.Column(db.String(256), nullable=False)
    title = db.Column(db.String(256), nullable=False)
    content = db.Column(db.Text, nullable=False)
    content_time = db.Column(db.Integer, nullable=False, default=0)
    post_tags = db.relationship('PostTag', back_populates='post', cascade='all, delete-orphan', passive_deletes=True)

    def __init__(self, url, title, content, content_time):
        self.url = url
        self.title = title
        self.content = content
        self.content_time = content_time

    def serialize(self, full=False):
        """Serialize post-object to pass template engine

        :param full: Serialize full content or annotation
        """
        return dict(created=self.created,
                    edited=self.edited,
                    url=self.url,
                    title=self.title,
                    content_time=self.content_time,
                    content=Markup(markdown2.markdown(
                        self.content if full else
                        '\n'.join(self.content.split('\n')[:current_app.config['LINES_FOR_ANNOTATION']])
                    )),
                    tags=[_.content for _ in self.post_tags])


class PostTag(db.Model):
    __tablename__ = 'post_tag'

    post_tag_id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.post_id', ondelete='CASCADE'), nullable=False)
    post = db.relationship('Post', back_populates='post_tags')
    content = db.Column(db.String(256), nullable=False, index=True)

    def __init__(self, content):
        self.content = content
