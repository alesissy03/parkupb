# TODO:
# filtrează locuri libere/ocupate
# returnează parcări disponibile
# interogări SQLAlchemy complexe

from app.extensions import db
from app.models import ParkingSpot

def get_all_spots(lot_id=None):
    query = ParkingSpot.query
    if lot_id is not None:
        query = query.filter_by(lot_id=lot_id)
    return query.all()


def get_free_spots(lot_id=None):
    query = ParkingSpot.query.filter_by(current_status="free")
    if lot_id is not None:
        query = query.filter_by(lot_id=lot_id)
    return query.all()


def get_occupied_spots(lot_id=None):
    query = ParkingSpot.query.filter_by(current_status="occupied")
    if lot_id is not None:
        query = query.filter_by(lot_id=lot_id)
    return query.all()


def mark_spot_free(spot_id):
    spot = ParkingSpot.query.get(spot_id)
    spot.current_status = "free"
    db.session.commit()
    return spot


def mark_spot_occupied(spot_id):
    spot = ParkingSpot.query.get(spot_id)
    spot.current_status = "occupied"
    db.session.commit()
    return spot
