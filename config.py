import os

class Config:
    # Flask
    DEBUG = True
    SECRET_KEY = b'_5#xy2L"F1\n\xec]/'

    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI = 'sqlite:///examdocs.sqlite'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
