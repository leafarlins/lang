from flask import Flask
from .routes.user import usermod
from .routes.langapp import langapp
from .routes.backend import backend
from .extentions import database
from .commands.userCommands import userCommands
from .commands.email import emailCommands
from .cache import cache

def create_app(config_object="app.settings"):
    app = Flask(__name__)
    app.config.from_object(config_object)
    app.register_blueprint(usermod)
    app.register_blueprint(langapp)
    app.register_blueprint(backend)
    app.register_blueprint(userCommands)
    app.register_blueprint(emailCommands)
    LOGLEVEL = app.config.get('LOGLEVEL')
    app.logger.setLevel(LOGLEVEL)
    
    
    cache.init_app(app)
    database.init_app(app)
    
    return app