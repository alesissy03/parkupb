"""
Modelul ParkingLot.

TODO (Task 2):
- Creează tabela `parking_lots` cu câmpurile:
    - id: INTEGER, PK, auto-increment
    - name: VARCHAR (ex: "Parcare Cămin A"), not null
    - campus_zone: VARCHAR (ex: "Nord", "Sud"), opțional
    - lat_center: FLOAT (latitudinea centrului parcării)
    - lng_center: FLOAT (longitudinea centrului parcării)
    - total_spots: INTEGER (numărul total de locuri)
    - polygon_geojson: TEXT (geometria parcării în format GeoJSON, opțional)

TODO (Task 6):
- Relația one-to-many cu ParkingSpot:
    - lots.spots -> listă de locuri aparținând parcării.
"""

from ..extensions import db

class ParkingLot(db.Model):
    __tablename__ = "parking_lots"

    # TODO (Task 2): definește coloanele conform documentației

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    campus_zone = db.Column(db.String(50), nullable=True)
    lat_center = db.Column(db.Float, nullable=True)
    lng_center = db.Column(db.Float, nullable=True)
    total_spots = db.Column(db.Integer, nullable=True)
    polygon_geojson = db.Column(db.Text, nullable=True)

    # TODO (Task 6): definește relația `spots` = db.relationship("ParkingSpot", ...)
    parking_spots = db.relationship(
        "ParkingSpot",
        back_populates="lot",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self):
        return f"<ParkingLot  {self.name}>"
