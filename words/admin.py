from contextlib import suppress

from flask import g, redirect, url_for, flash, request, Markup, escape
from flask_admin import Admin
from flask_admin.menu import MenuLink
from flask_admin.model.form import InlineFormAdmin
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.ajax import QueryAjaxModelLoader
from flask_admin.contrib.sqla.filters import (DateTimeBetweenFilter, DateTimeSmallerFilter, DateTimeGreaterFilter,
                                              EnumFilterInList, FilterLike)
from flask_admin.form.upload import ImageUploadField, ImageUploadInput
from wtforms.fields import PasswordField
import readtime

from words.ext import db, app_bcrypt
from words.utils import resize_logotype, TAG_EXTRACTOR
from words.models import User, UserStatus, ServiceSubscribe, Service, Post, PostTag
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


def datetime_formatter(self, context, model, name):
    dt = getattr(model, name)
    return Markup(escape(dt.strftime('%d.%m.%y %H:%M')))
    

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

    column_formatters = {'username': _username_formatter,
                         'registered': datetime_formatter,
                         'edited': datetime_formatter, }


class PostModelView(AdminRequiredMixin, ModelView):
    can_create = False

    form_ajax_refs = {
        'user': QueryAjaxModelLoader('user', db.session, User, fields=['username'], page_size=10)
    }
    form_excluded_columns = ('content_time', 'post_tags', )

    column_list = ('user.username',  'title', 'url', 'created', 'edited')
    column_labels = {'user.username': 'Username',
                     'url': 'URL'}
    column_sortable_list = ('user.username', 'title', 'url', 'created', 'edited', )
    column_searchable_list = ('user.username', 'title', 'url', )
    column_filters = (FilterLike(User.username, 'Username'),
                      FilterLike(Post.title, 'Title'),
                      FilterLike(Post.url, 'URL'),
                      DateTimeBetweenFilter(Post.created, 'Created'),
                      DateTimeSmallerFilter(Post.created, 'Created'),
                      DateTimeGreaterFilter(Post.created, 'Created'),
                      DateTimeBetweenFilter(Post.edited, 'Edited'),
                      DateTimeSmallerFilter(Post.edited, 'Edited'),
                      DateTimeGreaterFilter(Post.edited, 'Edited'), )
    form_overrides = {'content': MarkdownField, }
    extra_css = ('//cdn.jsdelivr.net/simplemde/latest/simplemde.min.css', )

    def on_model_change(self, form, model, is_created):
        with suppress(AttributeError):
            if form.content.data:
                tags = {_.group(1) for _ in TAG_EXTRACTOR.finditer(form.content.data)}
                model.content_time = readtime.of_markdown(form.content.data).minutes
                model.post_tags.clear()
                model.post_tags.extend((PostTag(_) for _ in tags))

    def _username_formatter(view, context, model, name):
        # `view` is current administrative view
        # `context` is instance of jinja2.runtime.Context
        # `model` is model instance
        # `name` is property name
        user = getattr(model, 'user')
        return Markup('<img src="{}" width="20px" height="20px" class="img-circle"> {}'.
                      format(escape(getattr(user, 'logotype')), escape(getattr(user, 'username'))))

    def _url_formatter(self, context, model, name):
        user = getattr(model, 'user')
        url = getattr(model, name)
        full_url = url_for('post.post', username=getattr(user, 'username'), postname=url)
        return Markup('<a href="{}">{}</a>'.format(escape(full_url), escape(url)))

    column_formatters = {'user.username': _username_formatter,
                         'url': _url_formatter,
                         'created': datetime_formatter,
                         'edited': datetime_formatter, }


def init_app(app):
    """Init admin panel"""
    root_url = app.config['ADMIN_URL']
    admin = Admin(app, name='Words', template_mode='bootstrap3',
                  index_view=UserModelView(User, db.session, endpoint='admin', url=root_url, static_folder='static'))
    admin.add_view(PostModelView(Post, db.session, endpoint='admin.post', url='{}/post'.format(root_url)))
    admin.add_link(MenuLink('Home', endpoint='index'))
