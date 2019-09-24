from flask import Blueprint, redirect, url_for


bp = Blueprint('post', __name__, url_prefix='/')


@bp.route('', methods=('GET', ))
def index():
    return redirect(url_for('.profile', username='world'))


@bp.route('<username>', methods=('GET', ))
def profile(username):
    """View for show profile page

    :param username: Username for show profile
    """
    pass


@bp.route('<username>/', methods=('GET', ))
def posts(username):
    """View for show profile posts

    :param username: Username for show posts
    """
    pass


@bp.route('<username>/<postname>', methods=('GET', ))
def post(username, postname):
    """View post for username and postname

    :param username: Username for show post
    :param postname: Postname for show post
    """
    pass


@bp.route('<username>/tag/<tagname>/', methods=('GET', ))
def posts_by_tag(username, tagname):
    """View for show profile posts by tag

    :param username: Username for show posts
    :param tagname: Tagname for show posts
    """
    pass
