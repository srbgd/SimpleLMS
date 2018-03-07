import os


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you secret key'  # any but yours


mongodb_link = "your mongodb link"