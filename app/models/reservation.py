"""
Modelul Reservation.

TODO (Task 2):
- Creează tabela `reservations` cu câmpurile:
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
    spot = db.relationship("ParkingSpot", back_populates="reservations")
    
    # def is_valid_timeframe(self):
    #     """Check if timeframe is logical."""
    #     return self.start_time < self.end_time
    
    # @staticmethod
    # def overlaps(spot_id, start, end):
    #     """Check if the requested time interval overlaps with existing reservations."""
    #     return Reservation.query.filter(
    #         Reservation.spot_id == spot_id,
    #         Reservation.status == "active",  # only active reservations matter
    #         and_(
    #             Reservation.start_time < end,
    #             Reservation.end_time > start
    #         )
    #     ).first()

    # @staticmethod
    # def create_reservation(user, spot, start, end):
    #     """Create reservation with full validation."""
    #     # 1. Time check
    #     if start >= end:
    #         raise ValueError("Start time must be before end time.")

    #     # 2. Check overlapping reservations
    #     if Reservation.overlaps(spot.id, start, end):
    #         raise ValueError("Spot is already reserved in this timeframe.")

    #     # 3. Create and save
    #     reservation = Reservation(
    #         user_id=user.id,
    #         spot_id=spot.id,
    #         start_time=start,
    #         end_time=end,
    #         status="active"
    #     )

    #     db.session.add(reservation)
    #     db.session.commit()
    #     return reservation
    
    # def cancel(self):
    #     """Cancel a reservation."""
    #     if self.status != "active":
    #         raise ValueError("Reservation is already canceled.")

    #     self.status = "cancelled"
    #     db.session.commit()

    # @staticmethod
    # def get_user_reservations(user_id):
    #     """Return all reservations of an user."""
    #     return Reservation.query.filter_by(user_id=user_id).order_by(Reservation.start_time.desc()).all()
    
    # @staticmethod
    # def get_spot_reservations(spot_id):
    #     """Return all reservations for a parking spot."""
    #     return Reservation.query.filter_by(spot_id=spot_id).order_by(Reservation.start_time.desc()).all()