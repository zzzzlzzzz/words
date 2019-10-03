from datetime import datetime

from flask import Blueprint, render_template, g, flash, url_for, redirect
from sqlalchemy.exc import IntegrityError
import readtime
from transliterate import translit, detect_language

from words.models import UserStatus, Post, PostTag
from words.user import only_for
from words.forms import ProfileForm, PostForm
from words.ext import db, celery
from words.utils import resize_logotype, TAG_EXTRACTOR


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
        g.user.about_time = readtime.of_markdown(form.about.data).minutes
        if form.logotype.data:
            try:
                g.user.logotype = resize_logotype(form.logotype.data.stream)
            except ValueError:
                flash('Avatar should be JPG or PNG file format', 'warning')
        db.session.commit()
    return render_template('edit/profile.html', form=form)


def generate_url(title):
    """Generate url for post from post title"""
    url = title.lower()
    lang = detect_language(url, fail_silently=True)
    return (translit(url, lang, True) if lang else url).replace(' ', '-')


@bp.route('post', methods=('GET', 'POST'))
@only_for(minimal=UserStatus.NORMAL)
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        title = form.title.data
        url = generate_url(title)
        tags = {_.group(1) for _ in TAG_EXTRACTOR.finditer(form.content.data)}
        content = form.content.data
        post = Post(url, title, content, readtime.of_markdown(content).minutes)
        post.post_tags.extend(PostTag(_) for _ in tags)
        g.user.posts.append(post)
        try:
            db.session.commit()
            post_url = url_for('post.post', username=g.user.username, postname=url, _external=True)
            celery.send_task('words.tasks.repost.all', (post.post_id, post_url))
            return redirect(post_url)
        except IntegrityError:
            flash('This title already exists. Please, enter another title.', 'warning')
            db.session.rollback()

    return render_template('edit/post.html',
                           form=form,
                           created=datetime.utcnow(),
                           edited=datetime.utcnow(),
                           content_time=0)


@bp.route('post/<postname>', methods=('GET', 'POST'))
@only_for(minimal=UserStatus.NORMAL)
def edit_post(postname):
    post = Post.query.filter_by(url=postname).first_or_404()
    form = PostForm(title=post.title, content=post.content)
    if form.validate_on_submit():
        title = form.title.data
        url = generate_url(title)
        tags = {_.group(1) for _ in TAG_EXTRACTOR.finditer(form.content.data)}
        content = form.content.data
        post.edited = datetime.utcnow()
        post.url = url
        post.title = title
        post.content = content
        post.content_time = readtime.of_markdown(content).minutes
        post.post_tags.clear()
        post.post_tags.extend(PostTag(_) for _ in tags)
        try:
            db.session.commit()
            return redirect(url_for('post.post', username=g.user.username, postname=url))
        except IntegrityError:
            flash('This title already exists. Please, enter another title.', 'warning')
            db.session.rollback()

    return render_template('edit/post.html',
                           form=form,
                           created=post.created,
                           edited=post.edited,
                           content_time=post.content_time)
