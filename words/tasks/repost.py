from celery.utils.log import get_task_logger
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import SQLAlchemyError

from words.models import Post, ServiceSubscribe, Service


logger = get_task_logger(__name__)


def repost(self, post_id, post_url):
    try:
        post = Post.query.filter_by(post_id=post_id).one()
        for services in ServiceSubscribe.query.filter_by(user_id=post.user_id).all():
            if services.service == Service.TELEGRAM.name:
                self.app.send_task('words.tasks.repost.telegram', (services.service_subscribe_id, post_id, post_url))
    except NoResultFound:
        pass
    except SQLAlchemyError as e:
        logger.exception('repost')
        raise self.retry(exc=e, countdown=self.default_retry_delay * (self.request.retries + 1))


def telegram(self, service_id, post_id, post_url):
    try:
        service = ServiceSubscribe.query.filter_by(service_subscribe_id=service_id).one()
        post = Post.query.filter_by(post_id=post_id).one()
        # TODO: send post here
    except NoResultFound:
        pass
    except SQLAlchemyError as e:
        logger.exception('telegram')
        raise self.retry(exc=e, countdown=self.default_retry_delay * (self.request.retries + 1))
