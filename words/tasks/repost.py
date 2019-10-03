from celery.utils.log import get_task_logger
from flask import current_app
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import SQLAlchemyError
from telegram import Bot, ParseMode, TelegramError
from telegram.error import BadRequest, Unauthorized
from telegram.utils.request import Request

from words.models import Post, ServiceSubscribe, Service
from words.ext import db


logger = get_task_logger(__name__)


def repost(self, post_id, post_url):
    try:
        post = Post.query.filter_by(post_id=post_id).one()
        for services in ServiceSubscribe.query.filter_by(user_id=post.user_id, alive=True).all():
            if services.service == Service.TELEGRAM.name:
                self.app.send_task('words.tasks.repost.telegram', (services.service_subscribe_id, post_id, post_url))
            elif services.service == Service.TWITTER.name:
                self.app.send_task('words.tasks.repost.twitter', (services.service_subscribe_id, post_id, post_url))
    except NoResultFound:
        pass
    except SQLAlchemyError as e:
        logger.exception('repost')
        raise self.retry(exc=e)


def telegram(self, service_id, post_id, post_url):
    try:
        service = ServiceSubscribe.query.filter_by(service_subscribe_id=service_id, alive=True).one()
        post = Post.query.filter_by(post_id=post_id).one()
        bot = Bot(current_app.config['TELEGRAM_BOT_TOKEN'],
                  request=Request(proxy_url=current_app.config['TELEGRAM_BOT_PROXY']))
        try:
            bot.send_message(service.credentials['channel_name'],
                             '*{}*\n\n{}'.format(post.title, post_url),
                             ParseMode.MARKDOWN)
        except (BadRequest, Unauthorized):
            service.alive = False
            db.session.commit()
    except NoResultFound:
        pass
    except (SQLAlchemyError, TelegramError) as e:
        logger.exception('telegram')
        raise self.retry(exc=e, countdown=self.default_retry_delay * (self.request.retries + 1))


def twitter(self, service_id, post_id, post_url):
    pass
