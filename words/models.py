import enum
from datetime import datetime

import markdown2
from flask import Markup, current_app, url_for

from words.ext import db
from words.utils import TAG_EXTRACTOR, html2plain


class UserStatus(enum.Enum):
    GUEST = 1
    NORMAL = 2
    ADMINISTRATOR = 3


class Service(enum.Enum):
    TELEGRAM = 1
#   TWITTER = 2


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

    def about_html(self):
        return Markup(markdown2.markdown(self.about))

    def about_plain(self):
        return html2plain(str(self.about_html()))

    def __str__(self):
        return self.username


class ServiceSubscribe(db.Model):
    __tablename__ = 'service_subscribe'

    service_subscribe_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id', ondelete='CASCADE'), nullable=False)
    user = db.relationship('User', back_populates='service_subscribes')
    service = db.Column(db.String(32), nullable=False)
    credentials = db.Column(db.JSON, nullable=False)
    alive = db.Column(db.Boolean, nullable=False, default=True)

    def __init__(self, service=None, credentials=None):
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

    def content_html(self, full=False):
        tag_url = r'''[#\g<1>]({})\g<2>'''.\
            format(url_for('post.posts_by_tag', username=self.user.username, tagname='tagname').
                   replace('tagname', '\\g<1>'))
        return Markup(
            markdown2.markdown(
                TAG_EXTRACTOR.sub(tag_url,
                                  self.content if full
                                  else '\n'.join(self.content.split('\n')[:current_app.config['LINES_FOR_ANNOTATION']])
                                  )))

    def content_plain(self, full=False):
        return html2plain(str(self.content_html(full)))


class PostTag(db.Model):
    __tablename__ = 'post_tag'

    post_tag_id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.post_id', ondelete='CASCADE'), nullable=False)
    post = db.relationship('Post', back_populates='post_tags')
    content = db.Column(db.String(256), nullable=False, index=True)

    def __init__(self, content):
        self.content = content
