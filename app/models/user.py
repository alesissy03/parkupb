"""
Modelul User.

TODO (Task 2):
- Creează tabela `users` cu câmpurile:
    - id: INTEGER, PK, auto-increment
    - email: VARCHAR, unic, not null
    - password_hash: VARCHAR, not null (parola hash-uită, nu în clar)
    - full_name: VARCHAR
    - role: VARCHAR (ex: 'student', 'staff', 'admin')
    - created_at: DATETIME (data creării contului)

TODO (Task 5):
- Integrare cu Flask-Login (UserMixin).
- Metode:
    - set_password(self, raw_password): setează password_hash
    - check_password(self, raw_password): verifică parola primită.
"""

from ..extensions import db, login_manager
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
# from app.utils.constants import USER_ROLES

class User(UserMixin, db.Model):
    __tablename__ = "users"

    # TODO (Task 2): definește coloanele (id, email, password_hash, full_name, role, created_at)
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    # role = db.Column(db.String(20), nullable=False, default="student")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # relatia cu tabela rezervari, 1 -> N: 
    reservations = db.relationship(
        "Reservation",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    # TODO (Task 5): metode set_password(self, raw_password) și check_password(self, raw_password)

    def set_password(self, raw_password: str):
        """Hash-uieste parola și o salvează în password_hash."""
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        """Verifică parola primită cu hash-ul stocat."""
        return check_password_hash(self.password_hash, raw_password)

    def __repr__(self):
        # TODO (Task 2): întoarce un string util pentru debugging
        return f"<User {self.email}>"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
