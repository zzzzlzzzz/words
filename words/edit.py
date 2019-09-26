from datetime import datetime
import re

from flask import Blueprint, render_template, g, flash, url_for
from sqlalchemy.exc import IntegrityError
import readtime
from transliterate import translit

from words.models import UserStatus, Post, PostTag
from words.user import only_for
from words.forms import ProfileForm, PostForm
from words.ext import db
from words.utils import resize_logotype


bp = Blueprint('edit', __name__, url_prefix='/edit')


TITLE_EXTRACTOR = re.compile(r'''^# ([\w\d\s]{1,256})$''', re.MULTILINE)
TAG_EXTRACTOR = re.compile(r'''#([\w\d_?!]+?)(\s|$)''', re.MULTILINE)


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


@bp.route('post', methods=('GET', 'POST'))
@only_for(minimal=UserStatus.NORMAL)
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        title = translit(TITLE_EXTRACTOR.search(form.content.data).group(1).strip().lower(), reversed=True)
        tags = {_.group(1) for _ in TAG_EXTRACTOR.finditer(form.content.data)}
        tag_url = '[#\\g<1>]({})\\g<2>'.format(url_for('post.posts_by_tag', username=g.user.username, tagname='tagname').replace('tagname', '\\g<1>'))
        content_with_tag = TAG_EXTRACTOR.sub(tag_url, form.content.data)

        post = Post(title, content_with_tag, readtime.of_markdown(content_with_tag))
        for tag in tags:
            post.post_tags.append(PostTag(tag))
        g.user.posts.append(post)
        try:
            db.session.commit()
        except IntegrityError:
            pass  # TODO: already exists title

    return render_template('edit/post.html',
                           form=form,
                           created=datetime.utcnow(),
                           edited=datetime.utcnow(),
                           content_time=0)


@bp.route('post/<postname>', methods=('GET', 'POST'))
@only_for(minimal=UserStatus.NORMAL)
def edit_post(postname):
    return render_template('edit/post.html')
