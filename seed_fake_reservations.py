import sys
import random
from datetime import datetime, timedelta, time

from app import create_app
from app.extensions import db
from app.models import ParkingSpot, Reservation, User

DAYS = 7
START_HOUR = 8
END_HOUR = 20
DURATIONS_H = [2, 4, 6, 8]

# Peak hours: 10–16 (mai ocupat)
PEAK_START_HOURS = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]
PEAK_WEIGHTS     = [4, 5, 4, 6, 8, 8, 8,  7,  4,  2,  1]

def daterange_days(n_days: int):
    today = datetime.now().date()
    for i in range(n_days):
        yield today - timedelta(days=i)

def overlaps(a_start, a_end, b_start, b_end):
    return max(a_start, b_start) < min(a_end, b_end)

def pick_intervals_for_day():
    """
    Generează intervale 8–20 cu durate 2/4/6/8h, cu trafic mai mare între 10–16.
    Întoarce listă de (start_hour, end_hour).
    """
    intervals = []

    # număr de "valuri" pe zi (mai multe în general, ca să se vadă statistici)
    waves = random.choice([2, 3, 3, 4])

    for _ in range(waves):
        start_h = random.choices(PEAK_START_HOURS, weights=PEAK_WEIGHTS, k=1)[0]
        dur = random.choice(DURATIONS_H)

        # Ajustăm durata ca să nu depășească END_HOUR
        if start_h + dur > END_HOUR:
            dur = max(2, END_HOUR - start_h)
        if start_h < START_HOUR or start_h >= END_HOUR or dur <= 0:
            continue

        end_h = start_h + dur
        if end_h <= END_HOUR and start_h < end_h:
            intervals.append((start_h, end_h))

    # Un interval mic extra uneori (densitate mai realistă)
    if random.random() < 0.45:
        start_h = random.choices(PEAK_START_HOURS, weights=PEAK_WEIGHTS, k=1)[0]
        dur = random.choice([2, 4])
        if start_h + dur <= END_HOUR:
            intervals.append((start_h, start_h + dur))

    # Curățăm duplicate și sortăm
    intervals = list(set(intervals))
    intervals.sort(key=lambda x: x[0])
    return intervals

def main():
    if len(sys.argv) < 2:
        print('Usage: python scripts/seed_fake_reservations.py "Parcare Precis"')
        sys.exit(1)

    lot_name = sys.argv[1].strip()

    app = create_app("development")
    with app.app_context():
        spots = ParkingSpot.query.filter(ParkingSpot.parking_lot == lot_name).all()
        if not spots:
            print(f"[ERR] Nu există spoturi pentru: {lot_name}. Creează spoturi înainte.")
            sys.exit(2)

        users = User.query.all()
        if not users:
            print("[ERR] Nu există utilizatori în tabela users. Creează măcar un user înainte.")
            sys.exit(3)

        user_ids = [u.id for u in users]

        created = 0
        used = {}  # (spot_id, date) -> list[(start_dt, end_dt)]

        for day in daterange_days(DAYS):
            intervals = pick_intervals_for_day()

            for start_h, end_h in intervals:
                start_dt = datetime.combine(day, time(start_h, 0))
                end_dt = datetime.combine(day, time(end_h, 0))

                if 8 <= start_h < 16:
                    fraction = random.uniform(0.70, 0.95)

                else:
                    fraction = random.uniform(0.40, 0.60)


                k = max(1, int(len(spots) * fraction))
                k = min(k, len(spots))

                # amestecăm ca să nu apară pattern-uri vizuale
                spots_copy = spots[:]
                random.shuffle(spots_copy)
                chosen_spots = spots_copy[:k]

                for sp in chosen_spots:
                    key = (sp.id, day)
                    day_list = used.setdefault(key, [])

                    if any(overlaps(start_dt, end_dt, s, e) for s, e in day_list):
                        continue

                    res = Reservation(
                        user_id=random.choice(user_ids),
                        spot_id=sp.id,
                        start_time=start_dt,
                        end_time=end_dt,
                        status="finished" if end_dt < datetime.now() else "active",
                    )
                    db.session.add(res)
                    day_list.append((start_dt, end_dt))
                    created += 1

        db.session.commit()
        print(f"[OK] Created {created} fake reservations for '{lot_name}' over last {DAYS} days.")

        # IMPORTANT: marchează locurile ca 'occupied' ACUM dacă au rezervare activă acum
        now = datetime.now()
        spot_ids = [s.id for s in spots]

        active_reserved_ids = (
            db.session.query(Reservation.spot_id)
            .filter(
                Reservation.spot_id.in_(spot_ids),
                Reservation.status == "active",
                Reservation.start_time <= now,
                Reservation.end_time > now,
            )
            .distinct()
            .all()
        )
        active_reserved_ids = {sid for (sid,) in active_reserved_ids}

        updated_count = 0
        for s in spots:
            new_val = (s.id in active_reserved_ids)
            if s.is_occupied != new_val:
                s.is_occupied = new_val
                updated_count += 1

        db.session.commit()
        print(f"[OK] Updated is_occupied for {updated_count} spots in '{lot_name}' (based on active reservations now).")

if __name__ == "__main__":
    random.seed(42)
    main()
