# TODO:
# verifică dacă locul este liber în interval
# creează rezervarea
# marchează locul ca “reserved”
# finalizează rezervările expirate

from app.extensions import db
from app.models import Reservation, ParkingSpot
from datetime import datetime, timedelta
from sqlalchemy import and_

TIME_LIMIT = 15

def _now():
    return datetime.now()

def parse_iso(dt_str: str) -> datetime:
    """
    Parse ISO datetime strings like:
      "2025-11-24T10:00:00"
    If frontend sends "...Z", just strip it to keep naive datetime.
    """
    if not dt_str:
        raise ValueError("INVALID_DATETIME")

    s = dt_str.strip()
    if s.endswith("Z"):
        s = s[:-1]
    return datetime.fromisoformat(s)

def is_valid_timeframe(start : datetime, end : datetime):
    """Check if timeframe is logical."""
    return start < end
    
def spot_overlaps(spot_id, start, end):
    """Check if the requested time interval overlaps with existing reservations."""
    return (
        Reservation.query
        .filter(
            Reservation.spot_id == spot_id,
            Reservation.status == "active",
            Reservation.end_time > start,
            Reservation.start_time < end,
        )
        .first()
        is not None
    )

def user_old_reservation_overlaps(user_id, start, end):
    existing_spot = (
        Reservation.query
        .filter(
            Reservation.user_id == user_id,
            Reservation.status == "active",
            Reservation.end_time >= start,
            Reservation.start_time < end,
        )
        .first()
    )
    return existing_spot is not None

def refresh_spot_reservation_window(spot_id: int) -> None:
    """
    Updates ParkingSpot.reservation_start_time/end_time to reflect:
    - the current active reservation (if one is active now),
    - else the next upcoming active reservation,
    - else clears both fields.
    """
    spot = ParkingSpot.query.get(spot_id)
    if not spot:
        return

    now = _now()

    # 1) Active now
    current = (
        Reservation.query
        .filter(
            Reservation.spot_id == spot_id,
            Reservation.status == "active",
            Reservation.start_time <= now,
            Reservation.end_time > now,
        )
        .order_by(Reservation.start_time.asc())
        .first()
    )

    if current:
        spot.reservation_start_time = current.start_time
        spot.reservation_end_time = current.end_time
        db.session.commit()
        return

    # 2) Next upcoming
    upcoming = (
        Reservation.query
        .filter(
            Reservation.spot_id == spot_id,
            Reservation.status == "active",
            Reservation.start_time > now,
        )
        .order_by(Reservation.start_time.asc())
        .first()
    )

    if upcoming:
        spot.reservation_start_time = upcoming.start_time
        spot.reservation_end_time = upcoming.end_time
    else:
        spot.reservation_start_time = None
        spot.reservation_end_time = None

    db.session.commit()

def finalize_expired_reservations() -> int:
    """
    Marks expired ACTIVE reservations as FINISHED.
    Returns how many were finalized.
    """
    now = _now()
    expired = (
        Reservation.query
        .filter(Reservation.status == "active", Reservation.end_time <= now)
        .all()
    )

    if not expired:
        return 0

    affected_spots = set()
    for r in expired:
        r.status = "finished"
        affected_spots.add(r.spot_id)

    db.session.commit()

    # update cached reservation windows for those spots
    for sid in affected_spots:
        refresh_spot_reservation_window(sid)

    return len(expired)

def create_reservation(user, spot_id, start_time, end_time):
    """
    Create reservation with validation.
    Raises ValueError with codes:
      - INVALID_TIMEFRAME
      - SPOT_NOT_FOUND
      - SPOT_OCCUPIED
      - OVERLAP
    """

    finalize_expired_reservations()
    cancel_no_show_reservations()

    start = parse_iso(start_time)
    end = parse_iso(end_time)

    # 1. Time check
    if start >= end:
        raise ValueError("INVALID_TIMEFRAME")
    
    # 2. Existing spot
    spot = ParkingSpot.query.get(spot_id)
    if not spot:
        raise ValueError("SPOT_NOT_FOUND")
    
    # 3. Check if someone is already parked there
    if spot.is_occupied and spot.occupied_by_email != user.email:
        raise ValueError("SPOT_OCCUPIED")

    # 4. Check overlapping reservations(by spot)
    if spot_overlaps(spot_id, start, end):
        raise ValueError("SPOT_OVERLAP")
    
    # 5. Check overlapping reservations(by previous reservations)
    if user_old_reservation_overlaps(user.id, start, end):
        raise ValueError("EXISTING_RESERVATION_OVERLAP")

    # 6. Create and save
    reservation = Reservation(
        user_id=user.id,
        spot_id=spot_id,
        start_time=start,
        end_time=end,
        status="active",
        created_at=_now(),
    )

    db.session.add(reservation)
    db.session.commit()

    # Keep spot "reservation window" in sync for Leaflet display
    refresh_spot_reservation_window(spot_id)

    return reservation

def cancel_reservation(reservation_id, user):
    """
    Cancel a reservation (owner or admin).
    Raises ValueError:
      - NOT_FOUND
      - FORBIDDEN
    """

    reservation = Reservation.query.get(reservation_id)
    if not reservation:
        raise ValueError("NOT_FOUND")

    if reservation.user_id != user.id and getattr(user, "role", None) != "admin":
        raise ValueError("FORBIDDEN")

    reservation.status = "cancelled"
    db.session.commit()

    refresh_spot_reservation_window(reservation.spot_id)
    return reservation

def get_user_reservations(user_id):
    """Return all reservations of an user."""
    finalize_expired_reservations()
    cancel_no_show_reservations()
    return (
        Reservation.query
        .filter_by(user_id=user_id)
        .order_by(Reservation.start_time.desc())
        .all()
    )

def get_spot_reservations(spot_id):
    """Return all reservations for a parking spot."""
    finalize_expired_reservations()
    return (
        Reservation.query
        .filter_by(spot_id=spot_id)
        .order_by(Reservation.start_time.desc())
        .all()
    )

def cancel_no_show_reservations() -> int:
    """
    If 15 minutes pass after start_time and the user didn't occupy the spot,
    cancel the reservation and make the spot available again.
    """
    t = _now()
    cutoff = t - timedelta(minutes=TIME_LIMIT)

    # reservations that started at least 15 min ago and are still active
    candidates = (
        Reservation.query
        .filter(
            Reservation.status == "active",
            Reservation.start_time <= cutoff,
        )
        .all()
    )

    if not candidates:
        return 0

    affected_spots = set()
    cancelled = 0

    for r in candidates:
        spot = ParkingSpot.query.get(r.spot_id)
        if not spot:
            continue

        # user who made the reservation
        # this uses the relationship Reservation.user you already have
        reserver_email = getattr(r.user, "email", None)

        # If the spot is occupied by the reserver -> OK, keep reservation
        if spot.is_occupied and reserver_email and spot.occupied_by_email == reserver_email:
            continue

        # Otherwise it's a no-show (or occupied by someone else)
        r.status = "cancelled"
        cancelled += 1
        affected_spots.add(r.spot_id)

    db.session.commit()

    # clear/update spot reservation window used by frontend coloring
    for sid in affected_spots:
        refresh_spot_reservation_window(sid)

    return cancelled