from flask import g, redirect, url_for, flash, request
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

from words.ext import db
from words.models import User, UserStatus


class AdminRequiredMixin:
    def is_accessible(self):
        user_status = UserStatus[g.user.status] if g.user else UserStatus.GUEST
        return user_status.value >= UserStatus.ADMINISTRATOR.value

    def inaccessible_callback(self, name, **kwargs):
        flash('This account not have right for access to requested page, login to another account.', 'warning')
        return redirect(url_for('user.sign_in', next=request.url))


class UserModelView(AdminRequiredMixin, ModelView):
    column_list = ('username', 'status', 'registered', 'edited', 'first_name', 'last_name', )


def init_app(app):
    """Init admin panel"""
    root_url = app.config['ADMIN_URL']
    admin = Admin(app, name='Words', template_mode='bootstrap3',
                  index_view=UserModelView(User, db.session, endpoint='admin', url=root_url, static_folder='static'))
