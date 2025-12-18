# TODO:
# filtrează locuri libere/ocupate
# returnează parcări disponibile

from app.extensions import db
from app.models import ParkingSpot, User
from datetime import datetime

def _now():
    return datetime.now()

def get_all_spots(parking_lot : str):
    query = ParkingSpot.query
    if parking_lot:
        query = query.filter_by(parking_lot=parking_lot)
    return query.all()

def get_occupied_spots(parking_lot : str):
    """
    Occupied = is_occupied True
    """
    query = ParkingSpot.query.filter_by(is_occupied=True)
    if parking_lot:
        query = query.filter_by(parking_lot=parking_lot)
    return query.all()

def get_reserved_spots(parking_lot : str):
    """
    Reserved now = reservation_start_time <= now < reservation_end_time
    """
    now = _now()
    query = ParkingSpot.query.filter(
        ParkingSpot.reservation_start_time.isnot(None),
        ParkingSpot.reservation_end_time.isnot(None),
        ParkingSpot.reservation_start_time <= now,
        ParkingSpot.reservation_end_time > now,
    )
    if parking_lot:
        query = query.filter(ParkingSpot.parking_lot == parking_lot)
    return query.all()

def get_free_spots(parking_lot : str):
    """
    Free now = not occupied AND not reserved now
    """
    now = _now()

    query = ParkingSpot.query.filter(ParkingSpot.is_occupied == False)  # noqa: E712

    # exclude "reserved now"
    query = query.filter(
        ~(
            (ParkingSpot.reservation_start_time.isnot(None)) &
            (ParkingSpot.reservation_end_time.isnot(None)) &
            (ParkingSpot.reservation_start_time <= now) &
            (ParkingSpot.reservation_end_time > now)
        )
    )

    if parking_lot:
        query = query.filter(ParkingSpot.parking_lot == parking_lot)

    return query.all()

def mark_spot_free(spot_id):
    """
    "free" means is_occupied=False (real-time state).
    """
    spot = ParkingSpot.query.get(spot_id)
    if not spot:
        return None

    spot.is_occupied = False
    spot.occupied_by_email = None
    db.session.commit()
    return spot


def mark_spot_occupied(spot_id : int, user_email : str):
    spot = ParkingSpot.query.get(spot_id)
    if not spot:
        return None

    spot.is_occupied = True
    if user_email is not None:
        spot.occupied_by_email = user_email

    db.session.commit()
    return spot
