"""
Modelul ParkingSpot.

TODO (Task 2):
- Creează tabela `parking_spots` cu câmpurile:
    - id: INTEGER, PK, auto-increment
    - lot_id: INTEGER, FK -> parking_lots.id
    - spot_number: VARCHAR / INTEGER (ex: 1, 2, "A23")
    - type: VARCHAR (ex: 'student', 'staff', 'disabled', 'visitor')
    - current_status: VARCHAR (ex: 'free', 'occupied', 'reserved', 'out_of_service')
    - last_status_change: DATETIME (ultima schimbare de status)
    - polygon_geojson: TEXT (geometria locului în format GeoJSON)

TODO (Task 6):
- Relația many-to-one cu ParkingLot (parking_spot.lot).

TODO (Task 9):
- Relația one-to-many cu Reservation (spot.reservations).
"""

from ..extensions import db
from datetime import datetime
from app.extensions import db
from app.utils.constants import SPOT_TYPES, SPOT_STATUSES

class ParkingSpot(db.Model):
    __tablename__ = "parking_spots"

    # TODO (Task 2, 6, 9): definește coloanele și relațiile
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey("parking_lots.id"), nullable=False)

    spot_number = db.Column(db.String(20), nullable=False)  # poate fi și cod, nu doar număr
    type = db.Column(db.String(20), nullable=False, default="student")
    current_status = db.Column(db.String(20), nullable=False, default="free")
    last_status_change = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    polygon_geojson = db.Column(db.Text, nullable=True)

    # Relații
    lot = db.relationship("ParkingLot", back_populates="parking_spots")
    reservations = db.relationship(
        "Reservation",
        back_populates="spot",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self):
        return f"<ParkingSpot {self.spot_number} in lot {self.lot_name}"
    
    def set_status(self, new_status: str):
        """Utilitar pentru a actualiza statusul și timestamp-ul"""
        self.current_status = new_status
        self.last_status_change = datetime.utcnow()