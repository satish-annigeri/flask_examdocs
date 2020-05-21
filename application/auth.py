from flask import redirect, render_template, flash, Blueprint, request, url_for
from flask_login import current_user, login_user
from .forms import LoginForm, SignupForm
from .models import db, User
from . import login_manager

auth_bp = Blueprint('auth_bp', __name__, template_folder='templates', static_folder='static')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user is None:
            user = User(name=form.name.data, email=form.email.data, website=form.website.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('main_bp.home'))
        flash('A user with email already exists')
    return render_template(
        'signup.html', title='Sign up for an account', form=form,
        body='Sign up for a user account')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # if current_user.is_authenticated:
    #     return redirect(url_for('main_bp.home'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(password=form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main_bp.home'))
        flash('Incorrect username or password')
        return redirect(url_for('auth_bp.login'))
    return render_template('login.html', form=form, title='Log In', body='Login with your user account')



@login_manager.user_loader
def load_user(user_id):
    if user_id is not None:
        return User.query.get(user_id)
    return None


@login_manager.unauthorized_handler
def unauthorized():
    flash('You must be logged in to view that page')
    return redirect(url_for('auth_bp.login'))

