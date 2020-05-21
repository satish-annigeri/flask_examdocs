from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=False)
    email = db.Column(db.String(40), nullable=False, unique=True)
    password = db.Column(db.String(200), primary_key=False, nullable=False, unique=False)
    website = db.Column(db.String(60), index=False, nullable=True, unique=False)
    created_on = db.Column(db.DateTime, index=False, nullable=True, unique=False)
    last_login = db.Column(db.DateTime, index=False, nullable=True, unique=False)

    def set_password(self, password):
        self.password = generate_password_hash(password, method='sha256')

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f'<User {self.name} {self.created_on}>'


class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.Integer, nullable=False, unique=True)
    subject = db.Column(db.String(100), nullable=True, unique=False)
    email_from = db.Column(db.String(40), nullable=False, unique=False)
    date = db.Column(db.DateTime(timezone=True), nullable=False, unique=False)
    usn = db.Column(db.String(15), nullable=False, unique=False)
    payment_id = db.Column(db.String(20), nullable=True, unique=True)
    amount = db.Column(db.Float, nullable=True, unique=False)
    doc_type = db.Column(db.String(60), nullable=True, unique=False)

    def __repr__(self):
        return f"{self.uid}: {self.email_from}, {self.date}, {self.usn}"

