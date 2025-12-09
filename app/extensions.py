# from app.models.user import User
"""
Extensii globale Flask (DB, LoginManager, etc.)

TODO (Task 2, Task 5):
- Creează instanța SQLAlchemy pentru acces la baza de date.
- Creează instanța LoginManager pentru autentificare.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Instanta SQLAlchemy pentru modele si conexiune la DB
db = SQLAlchemy()

# Instanta LoginManager pentru gestionarea sesiunilor de utilizator
login_manager = LoginManager()

# Configureaza pagina de login
login_manager.login_view = "auth.login"

@login_manager.user_loader
def load_user(user_id):
    from app.models.user import User
    return User.query.get(int(user_id))