
# TODO (Task 4): importă load_config, extensii și blueprint-uri

from flask import Flask, render_template
from .config import load_config
from .extensions import db, login_manager
from .routes import register_blueprints
from .utils.logger import configure_logging

def create_app(config_name: str = "development"):
    """
    Factory principală de aplicație Flask.

    TODO (Task 4):
    - creează instanța de Flask
    - încarcă configurația (Task 1)
    - inițializează extensiile (Task 2, 5)
    - înregistrează blueprint-urile (Task 4)
    """
    app = Flask(__name__, instance_relative_config=True)

    # TODO (Task 1): încarcă setările din config.json / .env folosind load_config
    app_config = load_config(config_name)
    app.config.update(app_config)
    configure_logging(app)

    # TODO (Task 2): inițializează baza de date SQLAlchemy (db.init_app(app))
    db.init_app(app)

    # TODO (Task 5): configurează Flask-Login (login_manager.init_app(app))
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    from app.models import user, parking_lot, parking_spot, reservation

    # TODO (Task 4): înregistrează blueprint-urile API
    register_blueprints(app)

    @app.route("/")
    def index():
        # TODO (Task 7): înlocuiește cu harta reală și UI
        return render_template("index.html")
    
    return app
