# TODO:
# verifică dacă locul este liber în interval
# creează rezervarea
# marchează locul ca “reserved”
# finalizează rezervările expirate

from app.extensions import db
from app.models import Reservation, ParkingSpot
from datetime import datetime
from sqlalchemy import and_

def is_valid_timeframe(start, end):
    """Check if timeframe is logical."""
    return start < end
    
def overlaps(spot_id, start, end):
    """Check if the requested time interval overlaps with existing reservations."""
    overlap = (
        Reservation.query
        .filter(
            Reservation.spot_id == spot_id,
            Reservation.status == "active",
            Reservation.end_time > start,
            Reservation.start_time < end,
        )
        .first()
    )
    return overlap is None

def create_reservation(user, spot, start, end):
    """Create reservation with full validation."""
    # 1. Time check
    if start >= end:
        raise ValueError("Start time must be before end time.")

    # 2. Check overlapping reservations
    if Reservation.overlaps(spot.id, start, end):
        raise ValueError("Spot is already reserved in this timeframe.")

    # 3. Create and save
    reservation = Reservation(
        user_id=user.id,
        spot_id=spot.id,
        start_time=start,
        end_time=end,
        status="active"
    )

    db.session.add(reservation)
    spot = ParkingSpot.query.get(spot.id)
    spot.current_status = "reserved"
    db.session.commit()
    return reservation

def cancel(reservation_id, user):
    """Cancel a reservation."""
    reservation = Reservation.query.get(reservation_id)
    if not reservation:
        raise ValueError("Reservation is already canceled.")

    reservation.status = "cancelled"
    db.session.commit()
    return reservation

def get_user_reservations(user_id):
    """Return all reservations of an user."""
    return Reservation.query.filter_by(user_id=user_id).order_by(Reservation.start_time.desc()).all()

def get_spot_reservations(spot_id):
    """Return all reservations for a parking spot."""
    return Reservation.query.filter_by(spot_id=spot_id).order_by(Reservation.start_time.desc()).all()