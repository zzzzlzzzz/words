from math import ceil

from flask import Blueprint, render_template, current_app, g, abort, Markup
import markdown2

from words.models import User, Post, PostTag
from words.ext import db


bp = Blueprint('post', __name__, url_prefix='/user/<username>')


@bp.url_value_preprocessor
def pull_user(endpoint, values):
    post_user = User.query.filter_by(username=values.pop('username')).first_or_404()
    g.post_user = {'user_id': post_user.user_id,
                   'username': post_user.username,
                   'registered': post_user.registered,
                   'edited': post_user.edited,
                   'logotype': post_user.logotype,
                   'first_name': post_user.first_name,
                   'last_name': post_user.last_name,
                   'about': Markup(markdown2.markdown(post_user.about)),
                   'about_time': post_user.about_time, }


def get_annotation(text):
    """
    Extract annotation from text (first N lines of text)

    :param text: Text for extracting
    :return: Annotation
    """
    return '\n'.join(text.split('\n')[:current_app.config['LINES_FOR_ANNOTATION']])


@bp.route('', methods=('GET', ), defaults={'page': 1})
@bp.route('page/<int:page>', methods=('GET', ))
def posts(page):
    """View for show profile posts

    :param page: Page for show
    """
    post_per_page = current_app.config['POST_PER_PAGE']
    total_user_posts = db.session.query(db.func.count(Post.post_id)).\
                           filter_by(user_id=g.post_user['user_id']).\
                           scalar() or 0
    total_pages = ceil(total_user_posts / post_per_page)
    if total_pages == 0:
        total_pages = 1
    if page < 1 or page > total_pages:
        raise abort(404)
    user_posts = [{'created': _.created,
                   'edited': _.edited,
                   'url': _.url,
                   'title': _.title,
                   'content_time': _.content_time,
                   'content': Markup(markdown2.markdown(get_annotation(_.content))),
                   'tags': [_.content for _ in PostTag.query.filter_by(post_id=_.post_id).all()]}
                  for _ in Post.query.
                      filter_by(user_id=g.post_user['user_id']).
                      order_by(Post.post_id).
                      offset((page - 1) * post_per_page).
                      limit(post_per_page).
                      all()]
    user_tags = None
    if page == 1:
        user_tags = [_[0] for _ in db.session.query(PostTag.content).
            join(PostTag.post).
            filter(Post.user_id == g.post_user['user_id']).
            all()]
    return render_template('post/multiple.html', page=page, total_pages=total_pages, posts=user_posts, tags=user_tags)


@bp.route('post/<postname>', methods=('GET', ))
def post(postname):
    """View post for username and postname

    :param postname: Postname for show post
    """
    post = Post.query.filter_by(user_id=g.post_user['user_id'], url=postname).first_or_404()
    post = {'created': post.created,
            'edited': post.edited,
            'url': post.url,
            'title': post.title,
            'content_time': post.content_time,
            'content': Markup(markdown2.markdown(post.content)),
            'tags': [_.content for _ in PostTag.query.filter_by(post_id=post.post_id)]}
    return render_template('post/single.html', post=post)


@bp.route('tag/<tagname>', methods=('GET', ), defaults={'page': 1})
@bp.route('tag/<tagname>/page/<int:page>', methods=('GET', ))
def posts_by_tag(tagname, page):
    """View for show profile posts by tag

    :param tagname: Tagname for show posts
    :param page: Page for show
    """
    post_per_page = current_app.config['POST_PER_PAGE']
    total_user_posts = db.session.query(db.func.count(Post.post_id)).\
                           select_from(PostTag).\
                           join(PostTag.post).\
                           filter(Post.user_id == g.post_user['user_id'], PostTag.content == tagname).\
                           scalar() or 0
    total_pages = ceil(total_user_posts / post_per_page)
    if page < 1 or page > total_pages:
        raise abort(404)
    user_posts = [{'created': _.created,
                   'edited': _.edited,
                   'url': _.url,
                   'title': _.title,
                   'content_time': _.content_time,
                   'content': Markup(markdown2.markdown(get_annotation(_.content))),
                   'tags': [_.content for _ in PostTag.query.filter_by(post_id=_.post_id).all()]}
                  for _ in db.session.query(Post).
                      select_from(PostTag).
                      join(PostTag.post).
                      filter(Post.user_id == g.post_user['user_id'], PostTag.content == tagname).
                      order_by(Post.post_id).
                      offset((page - 1) * post_per_page).
                      limit(post_per_page).
                      all()]
    return render_template('post/multiple-tag.html', tag=tagname, page=page, total_pages=total_pages, posts=user_posts)
