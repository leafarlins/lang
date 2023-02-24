import os

MONGO_URI = os.getenv('MONGO_URI')
SECRET_KEY = os.getenv('SECRET_KEY')
LOGLEVEL = os.environ.get('LOGLEVEL', 'INFO').upper()
