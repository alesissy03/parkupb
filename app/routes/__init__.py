"""
Pachetul routes gestioneaza toate Blueprint-urile API.
"""

from .auth import auth_bp
from .parking import parking_bp
from .reservation import reservation_bp
from .admin import admin_bp

def register_blueprints(app):
    app.register_blueprint(auth_bp, url_prefix="/")
    app.register_blueprint(parking_bp, url_prefix="/parking")
    app.register_blueprint(reservation_bp, url_prefix="/reservations")
    app.register_blueprint(admin_bp, url_prefix="/admin")
