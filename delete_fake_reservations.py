from app import create_app
from app.extensions import db
from app.models import Reservation, ParkingSpot

# Dacă vrei să ștergi DOAR pentru anumite parcări, setează LOTS = [...]
# Dacă vrei „orice ar fi” (global), lasă LOTS = None
LOTS = None  # ex: ["Parcare Precis", "Parcare Rectorat"]

app = create_app("development")

with app.app_context():
    # 1) șterge toate rezervările (sau doar pentru loturile alese)
    if LOTS is None:
        deleted_res = Reservation.query.delete(synchronize_session=False)
        print(f"[OK] Deleted {deleted_res} rows from reservations (ALL).")
    else:
        spot_ids = [
            s.id for s in ParkingSpot.query.filter(ParkingSpot.parking_lot.in_(LOTS)).all()
        ]
        if not spot_ids:
            deleted_res = 0
        else:
            deleted_res = (
                Reservation.query
                .filter(Reservation.spot_id.in_(spot_ids))
                .delete(synchronize_session=False)
            )
        print(f"[OK] Deleted {deleted_res} rows from reservations for lots={LOTS}.")

    # 2) curăță rezervarea „snapshot” de pe ParkingSpot (galbenul)
    spot_q = ParkingSpot.query
    if LOTS is not None:
        spot_q = spot_q.filter(ParkingSpot.parking_lot.in_(LOTS))

    updated = spot_q.update(
        {
            ParkingSpot.reservation_start_time: None,
            ParkingSpot.reservation_end_time: None,
            ParkingSpot.is_occupied: False,          # IMPORTANT: resetează roșu
            ParkingSpot.occupied_by_email: None,     # dacă există câmpul în modelul tău
        },
        synchronize_session=False
    )

    db.session.commit()
    print(f"[OK] Cleared reservation_start/end + reset occupied for {updated} parking spots.")
