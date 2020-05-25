from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required, logout_user

from . import exdocs

# Blueprint configuration
main_bp = Blueprint('main_bp', __name__, template_folder='templates', static_folder='static')


@main_bp.route('/')
def home():
    num_messages = exdocs.get_num_messages(['INBOX', 'printed', 'error'])
    dashboard = {'inbox_folder': num_messages[0][1]}
    dashboard['printed_folder'] = num_messages[1][1]
    dashboard['error_folder'] = num_messages[2][1]
    return render_template('home.html', title='Welcome', dashboard=dashboard)


@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth_bp.login'))


@main_bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

