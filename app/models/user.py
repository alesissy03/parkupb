"""
Modelul User.

"""

from ..extensions import db, login_manager
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # relatia cu tabela rezervari, 1 -> N: 
    reservations = db.relationship(
        "Reservation",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def set_password(self, raw_password: str):
        """Hash-uieste parola și o salvează în password_hash."""
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        """Verifică parola primită cu hash-ul stocat."""
        return check_password_hash(self.password_hash, raw_password)

    def __repr__(self):
        return f"<User id={self.id} email={self.email} role={self.role}>"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
