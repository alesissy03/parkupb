# TODO:
# filtrează locuri libere/ocupate
# returnează parcări disponibile

from app.extensions import db
from app.models import ParkingSpot, Reservation, User
from datetime import datetime, timedelta

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

def get_parking_stats(parking_lot: str | None):
    """
    Returnează statistici pentru o parcare sau pentru toate parcările.
    Dacă parking_lot este None -> statistici globale.
    """

    all_spots = get_all_spots(parking_lot)
    occupied = get_occupied_spots(parking_lot)
    reserved = get_reserved_spots(parking_lot)
    free = get_free_spots(parking_lot)

    total = len(all_spots)

    return {
        "total_spots": total,
        "free_spots": len(free),
        "occupied_spots": len(occupied),
        "reserved_spots": len(reserved),
        "availability_percent": round((len(free) / total) * 100, 1) if total > 0 else 0,
        "updated_at": _now().isoformat()
    }

def get_hourly_occupancy_probability(parking_lot: str | None, days: int = 7):
    """
    Calculează p(spot rezervat la ora H) pentru H=0..23, în ultimele `days` zile.

    p(H) = (minute_rezervate_in_ora_H) / (nr_spoturi * 60 * days)
    """
    now = _now()
    start_window = now - timedelta(days=days)

    # spoturile relevante
    spot_q = ParkingSpot.query
    if parking_lot:
        spot_q = spot_q.filter(ParkingSpot.parking_lot == parking_lot)

    spot_ids = [s.id for s in spot_q.all()]
    total_spots = len(spot_ids)

    # dacă nu avem spoturi, întoarcem 0
    if total_spots == 0:
        return [{"hour": h, "p": 0.0, "percent": 0.0} for h in range(24)]

    # rezervări relevante (exclude cancelled)
    res_q = Reservation.query.filter(
        Reservation.spot_id.in_(spot_ids),
        Reservation.end_time > start_window,
        Reservation.start_time < now,
        Reservation.status != "cancelled",
    )
    reservations = res_q.all()

    minutes_per_hour = [0] * 24

    for r in reservations:
        # clamp la fereastra de analiză
        a = max(r.start_time, start_window)
        b = min(r.end_time, now)
        if a >= b:
            continue

        # parcurge orele atinse de interval
        cur = a
        while cur < b:
            hour_start = cur.replace(minute=0, second=0, microsecond=0)
            hour_end = hour_start + timedelta(hours=1)

            seg_start = max(cur, hour_start)
            seg_end = min(b, hour_end)

            if seg_start < seg_end:
                mins = int((seg_end - seg_start).total_seconds() // 60)
                minutes_per_hour[hour_start.hour] += mins

            cur = hour_end

    denom = total_spots * 60 * days
    out = []
    for h in range(24):
        p = minutes_per_hour[h] / denom
        out.append({"hour": h, "p": round(p, 6), "percent": round(p * 100, 2)})
    return out
