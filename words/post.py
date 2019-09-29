from math import ceil
from xml.etree.ElementTree import Element, SubElement, ElementTree
from io import BytesIO
from email.utils import format_datetime

from sqlalchemy.orm.exc import NoResultFound
from flask import Blueprint, render_template, current_app, g, abort, redirect, url_for

from words.models import User, Post, PostTag
from words.ext import db


bp = Blueprint('post', __name__, url_prefix='/user/<username>')


@bp.url_value_preprocessor
def pull_user(endpoint, values):
    g.post_user_raw = User.query.filter_by(username=values.pop('username')).first_or_404()
    g.post_user = g.post_user_raw.serialize()


def global_posts(page):
    """Global related posts
    """
    try:
        g.post_user_raw = User.query.filter_by(username=current_app.config['BRAND']).one()
    except NoResultFound:
        return redirect(url_for('user.sign_up'))
    g.post_user = g.post_user_raw.serialize()
    post_per_page = current_app.config['POST_PER_PAGE']
    total_posts = db.session.query(db.func.count(Post.post_id)).scalar() or 0
    total_pages = ceil(total_posts / post_per_page)
    if total_pages == 0:
        total_pages = 1
    if page < 1 or page > total_pages:
        raise abort(404)
    posts = [_.serialize()
             for _ in Post.query.
                 order_by(Post.post_id.desc()).
                 offset((page - 1) * post_per_page).
                 limit(post_per_page).
                 all()]
    tags = None
    if page == 1:
        tags = [_[0] for _ in db.session.query(PostTag.content).all()]  # TODO: maybe in feature need limit this query
    return render_template('post/multiple.html', page=page, total_pages=total_pages, posts=posts, tags=tags)


@bp.route('', methods=('GET', ), defaults={'page': 1})
@bp.route('page/<int:page>', methods=('GET', ))
def posts(page):
    """View for show profile posts

    :param page: Page for show
    """
    post_per_page = current_app.config['POST_PER_PAGE']
    total_user_posts = db.session.query(db.func.count(Post.post_id)).\
                           filter_by(user_id=g.post_user_raw.user_id).\
                           scalar() or 0
    total_pages = ceil(total_user_posts / post_per_page)
    if total_pages == 0:
        total_pages = 1
    if page < 1 or page > total_pages:
        raise abort(404)
    user_posts = [_.serialize()
                  for _ in Post.query.
                      filter_by(user_id=g.post_user_raw.user_id).
                      order_by(Post.post_id.desc()).
                      offset((page - 1) * post_per_page).
                      limit(post_per_page).
                      all()]
    user_tags = None
    if page == 1:
        user_tags = [_[0] for _ in db.session.query(PostTag.content).
            join(PostTag.post).
            filter(Post.user_id == g.post_user_raw.user_id).
            all()]
    return render_template('post/multiple.html', page=page, total_pages=total_pages, posts=user_posts, tags=user_tags)


def strip_html(source):
    return ' '.join(ElementTree(file=BytesIO('<body>{}</body>'.format(source).encode('utf8'))).getroot().itertext())


def get_feed(page_link, self_link, user_root_raw, user_posts_raw):
    """Generate RSS feed using as source user_root_raw and user_posts_raw

    :param page_link: Link to resource index
    :param self_link: link to this view
    :param user_root_raw: User for using as root
    :param user_posts_raw: Posts for using as source
    """
    user_root = user_root_raw.serialize()
    rss = Element('rss', {'version': '2.0',
                          'xmlns:atom': 'http://www.w3.org/2005/Atom', })
    channel = SubElement(rss, 'channel')

    title = SubElement(channel, 'title')
    title.text = '{} {} {}'.format(user_root['first_name'], user_root['last_name'], user_root['username']).strip()
    link = SubElement(channel, 'link')
    link.text = page_link
    description = SubElement(channel, 'description')
    description.text = strip_html(str(user_root['about']))
    atom_link = SubElement(channel, 'atom:link',
                           {'href': self_link,
                            'rel': 'self',
                            'type': 'application/rss+xml'})
    if user_posts_raw:
        last_build_date = SubElement(channel, 'lastBuildDate')
        last_build_date.text = format_datetime(user_posts_raw[0].serialize()['edited'])

    for user_post_raw in user_posts_raw:
        user_post = user_post_raw.serialize()
        item = SubElement(channel, 'item')
        item_link = SubElement(item, 'link')
        item_link.text = url_for('post.post', username=user_post_raw.user.username, postname=user_post['url'], _external=True)
        guid = SubElement(item, 'guid')
        guid.text = item_link.text
        item_title = SubElement(item, 'title')
        item_title.text = strip_html(user_post['title'])
        item_description = SubElement(item, 'description')
        item_description.text = strip_html(user_post['content'])
        item_pub_date = SubElement(item, 'pubDate')
        item_pub_date.text = format_datetime(user_post['edited'])

    buffer_rss = BytesIO()
    ElementTree(rss).write(buffer_rss, 'UTF-8', True)
    return buffer_rss.getvalue().decode('utf8'), {'content-type': 'text/xml'}


@bp.route('/feed', methods=('GET', ))
def posts_feed():
    """View for RSS (Return POST_PER_PAGE posts)"""
    return get_feed(url_for('post.posts', username=g.post_user['username']),
                    url_for('post.posts_feed', username=g.post_user['username']),
                    g.post_user_raw,
                    Post.query.filter_by(user_id=g.post_user_raw.user_id).
                    order_by(Post.post_id.desc()).
                    limit(current_app.config['POST_PER_PAGE']).
                    all())


def global_feed():
    """View for global RSS feed (Return POST_PER_PAGE posts)"""
    try:
        g.post_user_raw = User.query.filter_by(username=current_app.config['BRAND']).one()
    except NoResultFound:
        return redirect(url_for('user.sign_up'))
    return get_feed(url_for('index'),
                    url_for('index_feed'),
                    g.post_user_raw,
                    Post.query.
                    order_by(Post.post_id.desc()).
                    limit(current_app.config['POST_PER_PAGE']).
                    all())


@bp.route('post/<postname>', methods=('GET', ))
def post(postname):
    """View post for username and postname

    :param postname: Postname for show post
    """
    user_post = Post.query.filter_by(user_id=g.post_user_raw.user_id, url=postname).first_or_404().serialize(True)
    return render_template('post/single.html', post=user_post)


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
                           filter(Post.user_id == g.post_user_raw.user_id, PostTag.content == tagname).\
                           scalar() or 0
    total_pages = ceil(total_user_posts / post_per_page)
    if page < 1 or page > total_pages:
        raise abort(404)
    user_posts = [_.serialize()
                  for _ in db.session.query(Post).
                      select_from(PostTag).
                      join(PostTag.post).
                      filter(Post.user_id == g.post_user_raw.user_id, PostTag.content == tagname).
                      order_by(Post.post_id.desc()).
                      offset((page - 1) * post_per_page).
                      limit(post_per_page).
                      all()]
    return render_template('post/multiple-tag.html', tag=tagname, page=page, total_pages=total_pages, posts=user_posts)
