from flask import current_app, render_template
from words.ext import db


def page_500(_):
    """Page 500"""
    current_app.logger.exception('page_500')
    db.session.rollback()
    return render_template('error/500.html'), 500


def page_400(_):
    """Page 400"""
    return render_template('error/400.html'), 400


def page_404(_):
    """Page 404"""
    return render_template('error/404.html'), 404
