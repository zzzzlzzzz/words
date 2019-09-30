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
    g.post_user = User.query.filter_by(username=values.pop('username')).first_or_404()


def pull_user_global():
    """Pull global user by brand-name"""
    g.post_user = User.query.filter_by(username=current_app.config['BRAND']).one()


def global_posts(page):
    """Global related posts
    """
    try:
        pull_user_global()
    except NoResultFound:
        return redirect(url_for('user.sign_up'))
    post_per_page = current_app.config['POST_PER_PAGE']
    total_posts = db.session.query(db.func.count(Post.post_id)).scalar() or 0
    total_pages = ceil(total_posts / post_per_page)
    if total_pages == 0:
        total_pages = 1
    if page < 1 or page > total_pages:
        raise abort(404)
    user_posts = Post.query.order_by(Post.post_id.desc()).offset((page - 1) * post_per_page).limit(post_per_page).all()
    tags = [_[0] for _ in db.session.query(PostTag.content).all()] if page == 1 else None   # TODO: maybe in feature need limit this query
    return render_template('post/multiple.html', page=page, total_pages=total_pages, posts=user_posts, tags=tags)


@bp.route('', methods=('GET', ), defaults={'page': 1})
@bp.route('page/<int:page>', methods=('GET', ))
def posts(page):
    """View for show profile posts

    :param page: Page for show
    """
    post_per_page = current_app.config['POST_PER_PAGE']
    total_user_posts = db.session.query(db.func.count(Post.post_id)).\
                           filter_by(user_id=g.post_user.user_id).\
                           scalar() or 0
    total_pages = ceil(total_user_posts / post_per_page)
    if total_pages == 0:
        total_pages = 1
    if page < 1 or page > total_pages:
        raise abort(404)
    user_posts = Post.query.\
        filter_by(user_id=g.post_user.user_id).\
        order_by(Post.post_id.desc()).\
        offset((page - 1) * post_per_page).\
        limit(post_per_page).\
        all()
    user_tags = [_[0]
                 for _ in db.session.query(PostTag.content).
                     join(PostTag.post).
                     filter(Post.user_id == g.post_user.user_id).
                     all()] if page == 1 else None
    return render_template('post/multiple.html', page=page, total_pages=total_pages, posts=user_posts, tags=user_tags)


def get_feed(page_link, self_link, user_posts):
    """Generate RSS feed using as source user_root_raw and user_posts_raw

    :param page_link: Link to resource index
    :param self_link: link to this view
    :param user_posts: Posts for using as source
    """
    rss = Element('rss', {'version': '2.0',
                          'xmlns:atom': 'http://www.w3.org/2005/Atom', })
    channel = SubElement(rss, 'channel')

    title = SubElement(channel, 'title')
    title.text = '{} {} {}'.format(g.post_user.first_name, g.post_user.last_name, g.post_user.username).strip()
    link = SubElement(channel, 'link')
    link.text = page_link
    description = SubElement(channel, 'description')
    description.text = g.post_user.about_plain()
    SubElement(channel, 'atom:link',
               {'href': self_link,
                'rel': 'self',
                'type': 'application/rss+xml'})
    if user_posts:
        last_build_date = SubElement(channel, 'lastBuildDate')
        last_build_date.text = format_datetime(user_posts[0].edited)

    for user_post in user_posts:
        item = SubElement(channel, 'item')
        item_link = SubElement(item, 'link')
        item_link.text = url_for('post.post', username=user_post.user.username, postname=user_post.url, _external=True)
        guid = SubElement(item, 'guid')
        guid.text = item_link.text
        item_title = SubElement(item, 'title')
        item_title.text = user_post.title
        item_description = SubElement(item, 'description')
        item_description.text = user_post.content_plain()
        item_pub_date = SubElement(item, 'pubDate')
        item_pub_date.text = format_datetime(user_post.edited)

    buffer_rss = BytesIO()
    ElementTree(rss).write(buffer_rss, 'UTF-8', True)
    return buffer_rss.getvalue().decode('utf8'), {'content-type': 'text/xml'}


@bp.route('/feed', methods=('GET', ))
def posts_feed():
    """View for RSS (Return POST_PER_PAGE posts)"""
    return get_feed(url_for('post.posts', username=g.post_user.username, _external=True),
                    url_for('post.posts_feed', username=g.post_user.username, _external=True),
                    Post.query.filter_by(user_id=g.post_user.user_id).
                    order_by(Post.post_id.desc()).
                    limit(current_app.config['POST_PER_PAGE']).
                    all())


def global_feed():
    """View for global RSS feed (Return POST_PER_PAGE posts)"""
    try:
        pull_user_global()
    except NoResultFound:
        return redirect(url_for('user.sign_up'))
    return get_feed(url_for('index', _external=True),
                    url_for('index_feed', _external=True),
                    Post.query.
                    order_by(Post.post_id.desc()).
                    limit(current_app.config['POST_PER_PAGE']).
                    all())


@bp.route('post/<postname>', methods=('GET', ))
def post(postname):
    """View post for username and postname

    :param postname: Postname for show post
    """
    user_post = Post.query.filter_by(user_id=g.post_user.user_id, url=postname).first_or_404()
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
                           filter(Post.user_id == g.post_user.user_id, PostTag.content == tagname).\
                           scalar() or 0
    total_pages = ceil(total_user_posts / post_per_page)
    if page < 1 or page > total_pages:
        raise abort(404)
    user_posts = db.session.query(Post).\
        select_from(PostTag).\
        join(PostTag.post).\
        filter(Post.user_id == g.post_user.user_id, PostTag.content == tagname).\
        order_by(Post.post_id.desc()).\
        offset((page - 1) * post_per_page).\
        limit(post_per_page).\
        all()
    return render_template('post/multiple-tag.html', tag=tagname, page=page, total_pages=total_pages, posts=user_posts)


@bp.route('/sitemap.xml', methods=('GET', ))
def posts_sitemap():
    post_per_page = current_app.config['POST_PER_PAGE']

    url_set = Element('urlset', {'xmlns': 'http://www.sitemaps.org/schemas/sitemap/0.9', })

    root_total_posts = db.session.query(db.func.count(Post.post_id)).\
                           filter_by(user_id=g.post_user.user_id).\
                           scalar() or 0
    root_total_pages = ceil(root_total_posts / post_per_page)
    root_url = SubElement(url_set, 'url')
    root_url_loc = SubElement(root_url, 'loc')
    root_url_loc.text = url_for('post.posts', username=g.post_user.username, _external=True)
    for page in range(2, root_total_pages):
        root_url_page = SubElement(url_set, 'url')
        root_url_page_loc = SubElement(root_url_page, 'loc')
        root_url_page_loc.text = url_for('post.posts', username=g.post_user.username, page=page, _external=True)

    tag_query = db.session.query(PostTag.content).\
        join(PostTag.post).\
        filter(Post.user_id == g.post_user.user_id).\
        group_by(PostTag.content)
    for tag, in tag_query.all():
        tag_total_posts = db.session.query(db.func.count(Post.post_id)).\
                              select_from(PostTag).\
                              join(PostTag.post).\
                              filter(Post.user_id == g.post_user.user_id, PostTag.content == tag).\
                              scalar() or 0
        tag_total_pages = ceil(tag_total_posts / post_per_page)
        tag_url = SubElement(url_set, 'url')
        tag_url_loc = SubElement(tag_url, 'loc')
        tag_url_loc.text = url_for('post.posts_by_tag', username=g.post_user.username, tagname=tag, _external=True)
        for page in range(2, tag_total_pages):
            tag_url_page = SubElement(url_set, 'url')
            tag_url_page_loc = SubElement(tag_url_page, 'loc')
            tag_url_page_loc.text = url_for('post.posts_by_tag', username=g.post_user.username, tagname=tag, page=page, _external=True)

    for user_post in Post.query.filter_by(user_id=g.post_user.user_id).order_by(Post.post_id.desc()).all():
        post_url = SubElement(url_set, 'url')
        post_url_loc = SubElement(post_url, 'loc')
        post_url_loc.text = url_for('post.post', username=g.post_user.username, postname=user_post.url, _external=True)
        post_url_lastmod = SubElement(post_url, 'lastmod')
        post_url_lastmod.text = user_post.edited.strftime('%Y-%m-%dT%H:%M:%S+00:00')

    buffer_sitemap = BytesIO()
    ElementTree(url_set).write(buffer_sitemap, 'UTF-8', True)
    return buffer_sitemap.getvalue().decode('utf8'), {'content-type': 'text/xml'}


def global_sitemap():
    """Global sitemap.xml for global level"""
    sitemap_index = Element('sitemapindex', {'xmlns': 'http://www.sitemaps.org/schemas/sitemap/0.9', })
    for user in User.query.filter(User.username != current_app.config['BRAND']).all():
        sitemap = SubElement(sitemap_index, 'sitemap')
        sitemap_loc = SubElement(sitemap, 'loc')
        sitemap_loc.text = url_for('post.posts_sitemap', username=user.username, _external=True)
        sitemap_lastmod = SubElement(sitemap, 'lastmod')
        last_edited = db.session.query(Post.edited).\
                          filter_by(user_id=user.user_id).\
                          order_by(Post.post_id.desc()).\
                          limit(1).\
                          scalar() or user.edited
        sitemap_lastmod.text = last_edited.strftime('%Y-%m-%dT%H:%M:%S+00:00')

    buffer_sitemap = BytesIO()
    ElementTree(sitemap_index).write(buffer_sitemap, 'UTF-8', True)
    return buffer_sitemap.getvalue().decode('utf8'), {'content-type': 'text/xml'}
