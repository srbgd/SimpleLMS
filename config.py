import os


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'greenGoldenField'


mongodb_link = "mongodb://reshreshus:1JohnBardeen@ds040898.mlab.com:40898/dbslms"