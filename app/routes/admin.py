"""
Endpoint-uri pentru administrator.

TODO (Task 11):
- Vizualizare statistici: numar locuri libere/ocupate, numar rezervări etc.
"""

from flask import Blueprint, render_template
from flask_login import login_required, current_user

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/parking", methods=["GET"])
@login_required
def admin_parking():
    """
    Pagina de admin pentru gestionare locuri de parcare.
    """
    return render_template("admin_parking.html")

@admin_bp.route('/lots', methods=['POST'])
def create_parking_lot():
    """
    Creeaza un ParkingLot dintr-un set de colturi (4), total_spots si layout (1 sau 2 coloane).
    """
    from flask import request, jsonify
    from app.extensions import db
    from app.models.parking_lot import ParkingLot
    from app.models.parking_spot import ParkingSpot
    import math

    if not current_user or getattr(current_user, 'role', None) != 'admin':
        return jsonify({"error": "FORBIDDEN", "message": "Doar un admin poate crea un Parking Lot."}), 403

    data = request.get_json() or {}
    name = data.get('name')
    corners = data.get('corners')
    total_spots = int(data.get('total_spots') or 0)
    columns = int(data.get('columns') or 1)

    if not name or not corners or len(corners) < 4 or total_spots <= 0 or columns not in (1, 2):
        return jsonify({"error": "INVALID_DATA", "message": "Trebuie introduse: nume, colturi, numar de locuri si de coloane."}), 400

    # Definim o functie de calcul distanta
    def distance(p1, p2):
        return math.sqrt((p2['lat'] - p1['lat'])**2 + (p2['lng'] - p1['lng'])**2)

    # Luam primele 4 colturi
    p0, p1, p2, p3 = corners[:4]

    # Lungimile laturilor
    d01 = distance(p0, p1)
    d12 = distance(p1, p2)
    d23 = distance(p2, p3)
    d30 = distance(p3, p0)

    # Determinam care e lungimea si care e latimea
    if d01 >= d12 and d01 >= d23 and d01 >= d30:
        v_long = (p1['lat'] - p0['lat'], p1['lng'] - p0['lng'])
        v_short = (p3['lat'] - p0['lat'], p3['lng'] - p0['lng'])
        origin = p0
    elif d12 >= d01 and d12 >= d23 and d12 >= d30:
        v_long = (p2['lat'] - p1['lat'], p2['lng'] - p1['lng'])
        v_short = (p0['lat'] - p1['lat'], p0['lng'] - p1['lng'])
        origin = p1
    elif d23 >= d01 and d23 >= d12 and d23 >= d30:
        v_long = (p3['lat'] - p2['lat'], p3['lng'] - p2['lng'])
        v_short = (p1['lat'] - p2['lat'], p1['lng'] - p2['lng'])
        origin = p2
    else:
        v_long = (p0['lat'] - p3['lat'], p0['lng'] - p3['lng'])
        v_short = (p2['lat'] - p3['lat'], p2['lng'] - p3['lng'])
        origin = p3

    len_long = math.sqrt(v_long[0]**2 + v_long[1]**2)
    len_short = math.sqrt(v_short[0]**2 + v_short[1]**2)

    v_long_unit = (v_long[0]/len_long, v_long[1]/len_long)
    v_short_unit = (v_short[0]/len_short, v_short[1]/len_short)

    # Centru aproximativ
    lat_center = sum([p['lat'] for p in corners[:4]]) / 4
    lng_center = sum([p['lng'] for p in corners[:4]]) / 4

    polygon_geojson = {
        "type": "Polygon",
        "coordinates": [[
            [p['lng'], p['lat']] for p in corners[:4]
        ] + [[corners[0]['lng'], corners[0]['lat']]]
        ]
    }

    lot_kwargs = {
        'name': name,
        'lat_center': lat_center,
        'lng_center': lng_center,
        'total_spots': total_spots,
        'polygon_geojson': str(polygon_geojson)
    }

    try:
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        existing_cols = [c['name'] for c in inspector.get_columns('parking_lots')]
        if 'columns' in existing_cols:
            lot_kwargs['columns'] = columns
    except Exception:
        pass

    lot = ParkingLot(**lot_kwargs)
    db.session.add(lot)
    db.session.commit()

    created = 0
    rows = math.ceil(total_spots / columns)

    spots = []
    for idx in range(total_spots):
        r = idx // columns  # pe lungime
        c = idx % columns   # pe latime

        u = (r + 0.5) / rows
        v = (c + 0.5) / columns

        # Pozitia punctului in coordonate geografice
        lat = origin['lat'] + v_long_unit[0] * u * len_long + v_short_unit[0] * v * len_short
        lng = origin['lng'] + v_long_unit[1] * u * len_long + v_short_unit[1] * v * len_short

        # Dimensiunile spotului
        spot_length = len_long / rows
        spot_width = len_short / columns

        half_length = spot_length / 2
        half_width = spot_width / 2

        # Colturile dreptunghiului spotului (SW, SE, NE, NW)
        sw_lat = lat - v_long_unit[0]*half_length - v_short_unit[0]*half_width
        sw_lng = lng - v_long_unit[1]*half_length - v_short_unit[1]*half_width

        se_lat = lat - v_long_unit[0]*half_length + v_short_unit[0]*half_width
        se_lng = lng - v_long_unit[1]*half_length + v_short_unit[1]*half_width

        ne_lat = lat + v_long_unit[0]*half_length + v_short_unit[0]*half_width
        ne_lng = lng + v_long_unit[1]*half_length + v_short_unit[1]*half_width

        nw_lat = lat + v_long_unit[0]*half_length - v_short_unit[0]*half_width
        nw_lng = lng + v_long_unit[1]*half_length - v_short_unit[1]*half_width

        spot_polygon = {
            "type": "Polygon",
            "coordinates": [[
                [sw_lng, sw_lat],
                [se_lng, se_lat],
                [ne_lng, ne_lat],
                [nw_lng, nw_lat],
                [sw_lng, sw_lat]
            ]]
        }

        spot = ParkingSpot(
            lot_id = lot.id, # ne rugam sa nu crape
            parking_lot=lot.name,
            spot_number=str(idx + 1),
            latitude=lat,
            longitude=lng,
            is_occupied=False,
            polygon_geojson=str(spot_polygon)
        )
        spots.append(spot)
        db.session.add(spot)
        created += 1

    db.session.commit()

    return jsonify({"success": True, "lot_id": lot.id, "created_spots": created}), 201


@admin_bp.route("/stats", methods=["GET"])
def stats():
    """
    TODO (Task 11): Statistici pentru admin.

    Răspuns 200 (exemplu):
    {
      "total_spots": 120,
      "free_spots": 40,
      "occupied_spots": 60,
      "reserved_spots": 15,
      "out_of_service_spots": 5,
      "active_reservations": 10,
      "finished_reservations": 120,
      "cancelled_reservations": 8
    }
    """
    return {"message": "stats – TODO Task 11"}, 501
