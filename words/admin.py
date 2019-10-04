from contextlib import suppress

from flask import g, redirect, url_for, flash, request, Markup, escape
from flask_admin import Admin
from flask_admin.model.form import InlineFormAdmin
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.filters import (DateTimeBetweenFilter, DateTimeSmallerFilter, DateTimeGreaterFilter,
                                              EnumFilterInList, FilterLike)
from flask_admin.form.upload import ImageUploadField, ImageUploadInput
from wtforms.fields import PasswordField
import readtime

from words.ext import db, app_bcrypt
from words.utils import resize_logotype
from words.models import User, UserStatus, ServiceSubscribe, Service
from words.forms import MarkdownField


class AdminRequiredMixin:
    def is_accessible(self):
        user_status = UserStatus[g.user.status] if g.user else UserStatus.GUEST
        return user_status.value >= UserStatus.ADMINISTRATOR.value

    def inaccessible_callback(self, name, **kwargs):
        flash('This account not have right for access to requested page, login to another account.', 'warning')
        return redirect(url_for('user.sign_in', next=request.url))


class LogotypeUploadInput(ImageUploadInput):
    data_template = ('<div class="image-thumbnail">'
                     ' <img %(image)s>'
                     '</div>'
                     '<input %(file)s>')

    def get_url(self, field):
        return field.data


class LogotypeUploadField(ImageUploadField):
    widget = LogotypeUploadInput()

    def __init__(self, *args, **kwargs):
        kwargs.update(validators=[])
        super().__init__(*args, **kwargs)

    def _delete_file(self, filename):
        pass

    def _save_file(self, data, filename):
        pass


class UserModelView(AdminRequiredMixin, ModelView):
    can_create = False
    column_list = ('username', 'status', 'registered', 'edited', 'first_name', 'last_name', )
    column_searchable_list = ('username', 'first_name', 'last_name', )
    column_sortable_list = ('username', 'status', 'registered', 'edited', 'first_name', 'last_name', )
    form_choices = {'status': [(_.name, _.name) for _ in UserStatus], }
    form_excluded_columns = ('password', 'posts', 'about_time', )
    form_extra_fields = {'new_password': PasswordField('Password'), }
    form_overrides = {'logotype': LogotypeUploadField,
                      'about': MarkdownField, }
    extra_css = ('//cdn.jsdelivr.net/simplemde/latest/simplemde.min.css', )

    def on_model_change(self, form, model, is_created):
        with suppress(AttributeError):
            if form.new_password.data:
                model.password = app_bcrypt.generate_password_hash(form.new_password.data)
            if form.logotype.data.stream:
                form.logotype.data.stream.seek(0)
                model.logotype = resize_logotype(form.logotype.data.stream)
            if form.about.data:
                model.about_time = readtime.of_markdown(form.about.data).minutes

    class ServiceSubscribeModelForm(InlineFormAdmin):
        can_create = False
        form_choices = {'service': [(_.name, _.name) for _ in Service], }

    inline_models = (ServiceSubscribeModelForm(ServiceSubscribe), )
    column_filters = (FilterLike(User.username, 'Username'),
                      EnumFilterInList(User.status, 'Status', [(_.name, _.name) for _ in UserStatus]),
                      DateTimeBetweenFilter(User.registered, 'Registered'),
                      DateTimeSmallerFilter(User.registered, 'Registered'),
                      DateTimeGreaterFilter(User.registered, 'Registered'),
                      DateTimeBetweenFilter(User.edited, 'Edited'),
                      DateTimeSmallerFilter(User.edited, 'Edited'),
                      DateTimeGreaterFilter(User.edited, 'Edited'),
                      FilterLike(User.first_name, 'First Name'),
                      FilterLike(User.last_name, 'Last Name'), )

    def _username_formatter(view, context, model, name):
        # `view` is current administrative view
        # `context` is instance of jinja2.runtime.Context
        # `model` is model instance
        # `name` is property name
        return Markup('<img src="{}" width="20px" height="20px" class="img-circle"> {}'.
                      format(escape(getattr(model, 'logotype')), escape(getattr(model, name))))

    column_formatters = {'username': _username_formatter, }


def init_app(app):
    """Init admin panel"""
    root_url = app.config['ADMIN_URL']
    admin = Admin(app, name='Words', template_mode='bootstrap3',
                  index_view=UserModelView(User, db.session, endpoint='admin', url=root_url, static_folder='static'))
