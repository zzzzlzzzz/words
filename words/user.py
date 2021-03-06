from functools import wraps
from urllib.parse import urlparse

from sqlalchemy.exc import IntegrityError
from flask import Blueprint, render_template, flash, session, redirect, url_for, g, abort, request

from words.forms import SignUpForm, SignInForm, PasswordChangeForm, service_forms
from words.utils import generate_logotype
from words.models import User, UserStatus, Service, ServiceSubscribe
from words.ext import db, app_bcrypt


bp = Blueprint('user', __name__, url_prefix='/user')


def load_user():
    """Load user from database by session (if exists)"""
    try:
        g.user = User.query.get(session['user_id'])
    except KeyError:
        g.user = None


def only_for(minimal=None, maximal=None):
    """Decorate view only for UserStatus

    :param minimal: If set, user status need be highest that minimal
    :param maximal: If set, user status need be lowest that maximal
    """
    def _only_for(view):
        @wraps(view)
        def _only_for_wraps(*args, **kwargs):
            user_status = UserStatus[g.user.status] if g.user else UserStatus.GUEST
            if minimal and user_status.value < minimal.value:
                flash('This account not have right for access to requested page, login to another account.', 'warning')
                return redirect(url_for('user.sign_in', next=request.url))
            if maximal and user_status.value > maximal.value:
                raise abort(404)
            return view(*args, **kwargs)
        return _only_for_wraps
    return _only_for


def is_url_safe(url):
    try:
        target_url = urlparse(url)
        test_url = urlparse(request.url)
        return target_url.scheme == test_url.scheme and target_url.netloc == test_url.netloc
    except (TypeError, ValueError):
        return False


@bp.route('sign-up', methods=('GET', 'POST', ))
@only_for(maximal=UserStatus.GUEST)
def sign_up():
    """Sign Up in application"""
    form = SignUpForm()
    if form.validate_on_submit():
        logotype = generate_logotype('@{}'.format(form.username.data[0]).upper())
        try:
            user = User(form.username.data, app_bcrypt.generate_password_hash(form.password.data), logotype)
            if user.username == 'world':
                user.status = UserStatus.ADMINISTRATOR.name
            db.session.add(user)
            db.session.commit()
            flash('Registration completed! Please, save your password in safe place - we not recovery lost password!', 'warning')
            return redirect(url_for('user.sign_in'))
        except IntegrityError:
            flash('This username already registered. Think better and try again.', 'danger')
            db.session.rollback()
    return render_template('user/forms.html', form=form, form_title='Sign Up')


@bp.route('sign-in', methods=('GET', 'POST', ))
def sign_in():
    """Sign In in application"""
    form = SignInForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and app_bcrypt.check_password_hash(user.password, form.password.data):
            session['user_id'] = user.user_id
            try:
                redirect_next = request.args['next']
                if is_url_safe(redirect_next):
                    return redirect(redirect_next)
            except KeyError:
                return redirect(url_for('post.posts', username=user.username))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('user/forms.html', form=form, form_title='Sign In')


@bp.route('sign-out', methods=('GET', ))
@only_for(minimal=UserStatus.NORMAL)
def sign_out():
    """Sign Out from application"""
    session.pop('user_id', None)
    return redirect(url_for('post.posts', username=g.user.username))


@bp.route('change-password', methods=('GET', 'POST', ))
@only_for(minimal=UserStatus.NORMAL)
def change_password():
    """Change user password"""
    form = PasswordChangeForm()
    if form.validate_on_submit():
        if app_bcrypt.check_password_hash(g.user.password, form.old_password.data):
            g.user.password = app_bcrypt.generate_password_hash(form.password.data)
            db.session.commit()
            return redirect(url_for('post.posts', username=g.user.username))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('user/forms.html', form=form, form_title='Change password')


@bp.route('service', methods=('GET', ))
@only_for(minimal=UserStatus.NORMAL)
def service_all():
    """Show all user service to reposting"""
    return render_template('user/services.html', services=g.user.service_subscribes, Service=Service)


@bp.route('service/delete/<int:service_id>', methods=('POST', ))
@only_for(minimal=UserStatus.NORMAL)
def service_delete(service_id):
    """Delete service from reposting"""
    if ServiceSubscribe.query.filter_by(user_id=g.user.user_id, service_subscribe_id=service_id).delete():
        db.session.commit()
    else:
        flash('Service ID is invalid', 'danger')
        db.session.rollback()
    return redirect(url_for('user.service_all'))


@bp.route('service/create/<service_name>', methods=('GET', 'POST', ))
@only_for(minimal=UserStatus.NORMAL)
def service_new(service_name):
    """Add service to reposting"""
    try:
        service = Service[service_name.upper()].name
    except KeyError:
        raise abort(404)
    form = service_forms[service]()
    form.back.href = url_for('user.service_all')
    if form.validate_on_submit():
        g.user.service_subscribes.append(ServiceSubscribe(service, form.dump()))
        db.session.commit()
        return redirect(url_for('user.service_all'))
    return render_template('user/forms.html', form=form, form_title='Add {}'.format(service.lower()))


@bp.route('service/<int:service_subscribe_id>', methods=('GET', 'POST', ))
@only_for(minimal=UserStatus.NORMAL)
def service_edit(service_subscribe_id):
    service = ServiceSubscribe.query.get_or_404(service_subscribe_id)
    form = service_forms[service.service](**service.credentials)
    form.back.href = url_for('user.service_all')
    if form.validate_on_submit():
        service.credentials = form.dump()
        service.alive = True
        db.session.commit()
        return redirect(url_for('user.service_all'))
    return render_template('user/forms.html', form=form, form_title='Edit {}'.format(service.service.lower()))
