"""
Modelul ParkingSpot.
- Structura tabelei `parking_spots`:
    - id: INTEGER, PK, auto-increment
    - lot_id: INTEGER, FK -> parking_lots.id
    - spot_number: VARCHAR / INTEGER (ex: 1, 2, "A23")
    - type: VARCHAR (ex: 'student', 'staff', 'disabled', 'visitor')
    - current_status: VARCHAR (ex: 'free', 'occupied', 'reserved', 'out_of_service')
    - last_status_change: DATETIME (ultima schimbare de status)
    - polygon_geojson: TEXT (geometria locului în format GeoJSON)
- Relația many-to-one cu ParkingLot (parking_spot.lot).
TODO (Task 9): i did it
- Relația one-to-many cu Reservation (spot.reservations).
"""

from ..extensions import db
from datetime import datetime
from app.extensions import db
from app.utils.constants import SPOT_STATUSES

class ParkingSpot(db.Model):
    __tablename__ = "parking_spots"

    id = db.Column(db.Integer, primary_key=True)

    # NEW: real relation to ParkingLot
    lot_id = db.Column(db.Integer, db.ForeignKey("parking_lots.id"), nullable=True)
    lot = db.relationship("ParkingLot", back_populates="spots")

    parking_lot = db.Column(db.String(100), nullable=False)  # Numele locului de parcare
    spot_number = db.Column(db.String(20), nullable=True)  # Numărul/ID-ul locului în cadrul parcării (ex: 1, A12)
    latitude = db.Column(db.Float, nullable=False)  # Coordonata latitudine
    longitude = db.Column(db.Float, nullable=False)  # Coordonata longitudine
    is_occupied = db.Column(db.Boolean, default=False, nullable=False)  # Ocupat (True/False)
    occupied_by_email = db.Column(db.String(120), db.ForeignKey('users.email', ondelete="SET NULL"), nullable=True)
    polygon_geojson = db.Column(db.Text, nullable=True)  # GeoJSON Polygon (dreptunghiul locului)
    
    # Informații despre rezervare (dacă există)
    reservation_start_time = db.Column(db.DateTime, nullable=True)  # Ora de început a rezervării
    reservation_end_time = db.Column(db.DateTime, nullable=True)  # Ora de plecare a rezervării
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    reservations = db.relationship(
        "Reservation",
        back_populates="spot",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self):
        return f"<ParkingSpot {self.parking_lot} ({self.id})>"
    
    def to_dict(self):
        """Convertește modelul la dicționar pentru API response"""
        try:
            import ast
            poly = ast.literal_eval(self.polygon_geojson) if self.polygon_geojson else None
        except Exception:
            poly = self.polygon_geojson
        
        return {
            'id': self.id,
            'parking_lot': self.parking_lot,
            'spot_number': self.spot_number,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'is_occupied': self.is_occupied,
            'occupied_by_email': self.occupied_by_email,
            'polygon_geojson': poly,
            'reservation': {
                'start_time': self.reservation_start_time.isoformat() if self.reservation_start_time else None,
                'end_time': self.reservation_end_time.isoformat() if self.reservation_end_time else None,
            } if self.reservation_start_time or self.reservation_end_time else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
    
    def set_status(self, new_status: str):
        """Utilitar pentru a actualiza statusul și timestamp-ul"""
        self.current_status = new_status
        self.last_status_change = datetime.now()