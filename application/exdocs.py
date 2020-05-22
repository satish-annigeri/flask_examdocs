from pathlib import Path

from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required, logout_user
from .process_emails import *
from .proc_email import *


host = 'mail.vtu.ac.in'
user = 'examdocs@vtu.ac.in'
password = 'examdocs@2020'


# Blueprint configuration
exdocs_bp = Blueprint('exdocs_bp', __name__, template_folder='templates', static_folder='static')

@exdocs_bp.route('/dashboard')
@exdocs_bp.route('/dashboard/<string:folder>')
@login_required
def dashboard(folder='INBOX'):
    imap = IMAP_Server(host, user, passwd)
    messages = imap.get_headers(folder)
    # messages = get_messages(host, user, password, folder)
    return render_template('exdocs/dashboard.html', folder=folder, messages=messages)

@exdocs_bp.route('/notify/<string:date>')
def notify(date='2020-05-11'):
    folder = '/mnt/c/Users/satish/Documents/WES'
    path = Path(folder) / date
    if path.is_dir():
        file_list = path.glob('*.pdf')
        return render_template('exdocs/notify.html', date=date, file_list=file_list)
    else:
        return render_template('exdocs/notify.html', date=date, file_list=None)

@exdocs_bp.route('/pull')
@exdocs_bp.route('/pull/<string:folder>')
@login_required
def pull_messages(folder='INBOX'):
    imap = IMAP_Server(host, user, password)
    msg_ids = imap.get_msg_ids(folder)
    message_list = []
    for msg_id in msg_ids:
        message = imap.get_message(folder, msg_id)
        message_list.append(message)
    return render_template('exdocs/message_list.html', title="Message List", message_list=message_list)


