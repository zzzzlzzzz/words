from datetime import datetime

from flask import Blueprint, render_template, g, flash

from words.models import UserStatus
from words.user import only_for
from words.forms import ProfileForm, PostForm
from words.ext import db
from words.utils import resize_logotype


bp = Blueprint('edit', __name__, url_prefix='/edit')


@bp.route('profile', methods=('GET', 'POST'))
@only_for(minimal=UserStatus.NORMAL)
def profile():
    form = ProfileForm(first_name=g.user.first_name, last_name=g.user.last_name, about=g.user.about)
    if form.validate_on_submit():
        g.user.edited = datetime.utcnow()
        g.user.first_name = form.first_name.data
        g.user.last_name = form.last_name.data
        g.user.about = form.about.data
        if form.logotype.data:
            try:
                g.user.logotype = resize_logotype(form.logotype.data.stream)
            except ValueError:
                flash('Avatar should be JPG or PNG file format', 'warning')
        db.session.commit()
    return render_template('edit/profile.html', form=form)


@bp.route('post', methods=('GET', 'POST'))
@only_for(minimal=UserStatus.NORMAL)
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        pass
    return render_template('edit/post.html', form=form)


@bp.route('post/<postname>', methods=('GET', 'POST'))
@only_for(minimal=UserStatus.NORMAL)
def edit_post(postname):
    pass
