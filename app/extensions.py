# from app.models.user import User
"""
Extensii globale Flask (DB, LoginManager, etc.)

TODO (Task 2, Task 5):
- Creează instanța SQLAlchemy pentru acces la baza de date.
- Creează instanța LoginManager pentru autentificare.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# TODO (Task 2): instanța SQLAlchemy pentru modele și conexiune la DB
db = SQLAlchemy()

# TODO (Task 5): instanța LoginManager pentru gestionarea sesiunilor de utilizator
login_manager = LoginManager()

# TODO (Task 5): configurează pagina de login (când vei avea una)
login_manager.login_view = "auth.login"

@login_manager.user_loader
def load_user(user_id):
    """
    TODO (Task 5):
    - Înlocuiește acest placeholder cu logica reală:
        from app.models import User
        return User.query.get(int(user_id))

    Deocamdată returnează None ca să nu mai arunce Flask-Login
    excepția 'Missing user_loader or request_loader'.
    """
    from app.models.user import User
    return User.query.get(int(user_id))