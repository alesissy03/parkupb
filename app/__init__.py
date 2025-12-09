
# TODO (Task 4): importă load_config, extensii și blueprint-uri

from flask import Flask, render_template
from .config import load_config
from .extensions import db, login_manager
from .routes import register_blueprints
from .utils.logger import configure_logging

def create_app(config_name: str = "development"):
    app = Flask(__name__, instance_relative_config=True)

    # Incarca setarile din config.json folosind load_config
    app_config = load_config(config_name)
    app.config.update(app_config)
    configure_logging(app)

    # Initializeaza baza de date SQLAlchemy (db.init_app(app))
    db.init_app(app)

    # Configureaza Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    from app.models import user, parking_lot, parking_spot, reservation

    # Inregistreaza blueprint-urile API
    register_blueprints(app)

    @app.route("/")
    def index():
        return render_template("index.html")
    
    return app
