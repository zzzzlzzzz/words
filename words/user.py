from sqlalchemy.exc import IntegrityError
from flask import Blueprint, render_template, flash, session, redirect, url_for

from words.forms import SignUpForm, SignInForm
from words.utils import generate_logotype
from words.models import User, UserStatus
from words.ext import db, app_bcrypt


bp = Blueprint('user', __name__, url_prefix='/user')


@bp.route('sign-up', methods=('GET', 'POST', ))
def sign_up():
    """Sign Up in application"""
    form = SignUpForm()
    if form.validate_on_submit():
        logotype = generate_logotype('@{}'.format(form.username.data[0]).upper())
        try:
            user = User(form.username.data, app_bcrypt.generate_password_hash(form.password.data).decode('utf8'), logotype)
            if user.username == 'world':
                user.status = UserStatus.ADMINISTRATOR.name
            db.session.add(user)
            db.session.commit()
            flash('Registration completed! Please, save your password in safe place - we not recovery lost password!', 'warning')
            return redirect(url_for('.sign_in'))
        except IntegrityError:
            flash('This username already registered. Think better and try again.', 'danger')
    return render_template('user/base.html', form=form, form_title='Sign Up')


@bp.route('sign-in', methods=('GET', 'POST', ))
def sign_in():
    """Sign In in application"""
    form = SignInForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and app_bcrypt.check_password_hash(user.password, form.password.data):
            session['user_id'] = user.user_id
        else:
            flash('Invalid credentials', 'danger')
    return render_template('user/base.html', form=form, form_title='Sign In')


@bp.route('sign-out', methods=('GET', ))
def sign_out():
    """Sign Out from application"""
    pass


@bp.route('password-change', methods=('GET', 'POST', ))
def password_change():
    """Change user password"""
    return render_template('user/base.html')
