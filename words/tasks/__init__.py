from words.ext import celery
from words.tasks import repost


def init_app(app):
    celery.conf.update(app.config['CELERY'])

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    setattr(celery, 'Task', ContextTask)


@celery.task(name='words.tasks.repost.all', bind=True, ignore_result=True, max_retries=3, default_retry_delay=2 * 60)
def repost_all(self, post_id, post_url):
    repost.repost(self, post_id, post_url)


@celery.task(name='words.tasks.repost.telegram', bind=True, ignore_result=True, max_retries=3, default_retry_delay=2 * 60)
def repost_telegram(self, service_id, post_id, post_url):
    repost.telegram(self, service_id, post_id, post_url)
