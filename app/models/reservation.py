"""
Modelul Reservation.

- Strcutura tabelei `reservations`:
    - id: INTEGER, PK, auto-increment
    - user_id: INTEGER, FK -> users.id
    - spot_id: INTEGER, FK -> parking_spots.id
    - start_time: DATETIME (începutul rezervării)
    - end_time: DATETIME (sfârșitul rezervării)
    - status: VARCHAR (ex: 'active', 'cancelled', 'finished')

TODO (Task 9):
- Logica pentru creare/anulare rezervări + validări (interval valid, disponibilitate spot).

TODO (Task 10):
- Query-uri pentru istoricul rezervărilor unui user.
"""

from ..extensions import db
from datetime import datetime
from app.utils.constants import RESERVATION_STATUSES
from sqlalchemy import and_

class Reservation(db.Model):
    __tablename__ = "reservations"

    # TODO (Task 2, 9, 10): definește coloanele și relațiile
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    spot_id = db.Column(db.Integer, db.ForeignKey("parking_spots.id"), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Reservation user={self.user_id} spot={self.spot_id} {self.start_time}-{self.end_time}>"
    
    # Relații
    #  1 user -> N reservations
    user = db.relationship("User", back_populates="reservations")
    #  1 parking_spot -> N reservations
    # Comentat pentru acum - va fi activat când ParkingSpot va avea relația back_populates
    spot = db.relationship("ParkingSpot", back_populates="reservations")
    