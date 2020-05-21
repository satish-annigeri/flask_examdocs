from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional

class SignupForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2)])
    email = StringField('Email', validators=[Email(message='Enter a valid email'), DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm = PasswordField('Re-enter Password', validators=[EqualTo('password', message='Passwords must match')])
    website = StringField('Website', validators=[Optional()])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email('Enter your email')])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField('Log In')

