"""
Endpoint-uri pentru parcări și locuri de parcare.

TODO (Task 8):
- Filtrare după numele parking lot / număr locuri libere.
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.models import ParkingSpot, ParkingLot, Reservation
from app.extensions import db
from app.services.reservation_service import finalize_expired_reservations, cancel_no_show_reservations
from datetime import datetime

parking_bp = Blueprint("parking", __name__)

@parking_bp.route("/lots", methods=["GET"])
def get_lots():
    try:
        lots = ParkingLot.query.all()
        result = []
        for lot in lots:
            # attempt to parse polygon json if stored as string
            try:
                import ast
                poly = ast.literal_eval(lot.polygon_geojson) if lot.polygon_geojson else None
            except Exception:
                poly = lot.polygon_geojson

            result.append({
                'id': lot.id,
                'name': lot.name,
                'campus_zone': lot.campus_zone,
                'lat_center': lot.lat_center,
                'lng_center': lot.lng_center,
                'total_spots': lot.total_spots,
                'columns': getattr(lot, 'columns', None),
                'polygon_geojson': poly
            })
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@parking_bp.route('/lots/<int:lot_id>', methods=['PUT', 'DELETE'])
@login_required
def modify_lot(lot_id):
    # Doar un admin poate sterge un Parking Lot
    if not current_user or getattr(current_user, 'role', None) != 'admin':
        return jsonify({'error': 'FORBIDDEN'}), 403

    lot = ParkingLot.query.get(lot_id)
    if not lot:
        return jsonify({'error': 'NOT_FOUND'}), 404

    if request.method == 'DELETE':
        try:
            ParkingSpot.query.filter_by(parking_lot=lot.name).delete()
            db.session.delete(lot)
            db.session.commit()
            return jsonify({'success': True}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    data = request.get_json() or {}
    name = data.get('name')
    total_spots = data.get('total_spots')
    columns = data.get('columns')
    corners = data.get('corners')

    try:
        regen = False
        old_name = lot.name

        if name:
            lot.name = name
            regen = True

        if total_spots is not None:
            lot.total_spots = int(total_spots)
            regen = True

        if columns is not None:
            try:
                from sqlalchemy import inspect
                inspector = inspect(db.engine)
                existing_cols = [c['name'] for c in inspector.get_columns('parking_lots')]
                if 'columns' in existing_cols:
                    lot.columns = int(columns)
                    regen = True
                else:
                    regen = True
            except Exception:
                try:
                    lot.columns = int(columns)
                    regen = True
                except Exception:
                    regen = True

        if corners and len(corners) >= 4:
            lats = [float(c['lat']) for c in corners[:4]]
            lngs = [float(c['lng']) for c in corners[:4]]
            min_lat, max_lat = min(lats), max(lats)
            min_lng, max_lng = min(lngs), max(lngs)
            polygon_geojson = {
                "type": "Polygon",
                "coordinates": [[
                    [min_lng, min_lat],
                    [max_lng, min_lat],
                    [max_lng, max_lat],
                    [min_lng, max_lat],
                    [min_lng, min_lat]
                ]]
            }
            lot.polygon_geojson = str(polygon_geojson)
            lot.lat_center = (min_lat + max_lat) / 2.0
            lot.lng_center = (min_lng + max_lng) / 2.0
            regen = True

        db.session.commit()

        if regen:
            ParkingSpot.query.filter_by(parking_lot=old_name).delete()
            db.session.commit()

            import math
            min_lat, max_lat = None, None
            try:
                import ast
                poly = ast.literal_eval(lot.polygon_geojson) if lot.polygon_geojson else None
                if poly and 'coordinates' in poly and poly['coordinates']:
                    coords = poly['coordinates'][0]
                    lngs = [c[0] for c in coords]
                    lats = [c[1] for c in coords]
                    min_lat, max_lat = min(lats), max(lats)
                    min_lng, max_lng = min(lngs), max(lngs)
            except Exception:
                pass

            if min_lat is None:
                min_lat = lot.lat_center - 0.0005
                max_lat = lot.lat_center + 0.0005
                min_lng = lot.lng_center - 0.001
                max_lng = lot.lng_center + 0.001

            columns_val = int(lot.columns or 1)
            rows = math.ceil(int(lot.total_spots) / columns_val)
            created = 0
            for idx in range(int(lot.total_spots)):
                r = idx // columns_val
                c = idx % columns_val
                u = (c + 0.5) / columns_val
                v = (r + 0.5) / rows
                lat = max_lat + v * (min_lat - max_lat)
                lng = min_lng + u * (max_lng - min_lng)
                
                # Calculeaza cele 4 colturi ale dreptunghiului pentru acest spot
                spot_width = (max_lng - min_lng) / columns_val
                spot_height = (max_lat - min_lat) / rows
                
                spot_left = min_lng + c * spot_width
                spot_right = spot_left + spot_width
                spot_top = max_lat - r * spot_height
                spot_bottom = spot_top - spot_height

                # GeoJSON Polygon
                spot_polygon = {
                    "type": "Polygon",
                    "coordinates": [[
                        [spot_left, spot_bottom],
                        [spot_right, spot_bottom],
                        [spot_right, spot_top],
                        [spot_left, spot_top],
                        [spot_left, spot_bottom]
                    ]]
                }
                
                sp = ParkingSpot(
                    parking_lot=lot.name,
                    spot_number=str(idx + 1),
                    latitude=lat,
                    longitude=lng,
                    is_occupied=False,
                    polygon_geojson=str(spot_polygon)
                )
                db.session.add(sp)
                created += 1
            db.session.commit()

        if name and not regen:
            ParkingSpot.query.filter_by(parking_lot=old_name).update({'parking_lot': name})
            db.session.commit()

        return jsonify({'success': True, 'lot_id': lot.id}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@parking_bp.route("/spots", methods=["GET", "POST"])
def manage_spots():
    """
    GET: Returnează lista de locuri de parcare (parking spots).
    
    POST: Adaugă un nou loc de parcare.
    """
    if request.method == "GET":
        try:
            finalize_expired_reservations()
            cancel_no_show_reservations()
            spots = ParkingSpot.query.all()
            return jsonify([spot.to_dict() for spot in spots]), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    elif request.method == "POST":
        try:
            data = request.get_json()
            
            # Validare date
            if not data.get("parking_lot") or data.get("latitude") is None or data.get("longitude") is None:
                return jsonify({"error": "Nu au fost introduse toate câmpurile"}), 400
            
            # Creaza nou loc de parcare
            new_spot = ParkingSpot(
                parking_lot=data.get("parking_lot"),
                latitude=float(data.get("latitude")),
                longitude=float(data.get("longitude")),
                is_occupied=data.get("is_occupied", False)
            )
            
            db.session.add(new_spot)
            db.session.commit()
            
            return jsonify({
                "message": "Loc de parcare creat cu succes.",
                "spot": new_spot.to_dict()
            }), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500


@parking_bp.route('/spots/<int:spot_id>', methods=['PUT', 'DELETE'])
@login_required
def modify_spot(spot_id):
    if not current_user or getattr(current_user, 'role', None) != 'admin':
        return jsonify({'error': 'FORBIDDEN'}), 403

    spot = ParkingSpot.query.get(spot_id)
    if not spot:
        return jsonify({'error': 'NOT_FOUND'}), 404

    if request.method == 'DELETE':
        try:
            db.session.delete(spot)
            db.session.commit()
            return jsonify({'success': True}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    data = request.get_json() or {}
    try:
        if 'parking_lot' in data:
            spot.parking_lot = data.get('parking_lot')
        if 'spot_number' in data:
            spot.spot_number = str(data.get('spot_number'))
        if 'latitude' in data:
            spot.latitude = float(data.get('latitude'))
        if 'longitude' in data:
            spot.longitude = float(data.get('longitude'))
        if 'is_occupied' in data:
            spot.is_occupied = bool(data.get('is_occupied'))

        db.session.commit()
        return jsonify({'success': True, 'spot': spot.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
    
@parking_bp.route('/spots/<int:spot_id>/toggle', methods=['POST'])
@login_required
def toggle_spot_occupancy(spot_id):
    """
    Toggle ocupare loc de parcare.
    - Dacă e liber, utilizatorul curent îl ocupă (doar dacă nu ocupă deja alt loc)
    - Dacă e ocupat de el, îl eliberează
    - Dacă e ocupat de altcineva, eroare 403
    """
    spot = ParkingSpot.query.get_or_404(spot_id)

    finalize_expired_reservations()
    cancel_no_show_reservations()

    now = datetime.now()

    # Daca locul e liber, il poate ocupa oricine
    if not spot.is_occupied:
        # Verifica daca utilizatorul ocupa deja alt loc
        # occupied_spots = ParkingSpot.query.filter_by(
        #     occupied_by_email=current_user.email,
        #     is_occupied=True
        # ).first()
        
        # if occupied_spots:
        #     return jsonify({
        #         'error': f'Ocupi deja locul {occupied_spots.parking_lot} #{occupied_spots.spot_number}. Eliberează-l înainte de a ocupa altul!'
        #     }), 409
        
        # spot.is_occupied = True
        # spot.occupied_by_email = current_user.email
        active_res = (
            Reservation.query
            .filter(
                Reservation.spot_id == spot.id,
                Reservation.status == "active",
                Reservation.start_time <= now,
                Reservation.end_time > now,
            )
            .order_by(Reservation.start_time.asc())
            .first()
        )

        if active_res and active_res.user_id != current_user.id and getattr(current_user, "role", None) != "admin":
            return jsonify({
                "error": "RESERVED_FOR_ANOTHER_USER",
                "message": "Loc rezervat: doar persoana care a făcut rezervarea poate parca acum.",
                "reservation": {
                    "start_time": active_res.start_time.isoformat(),
                    "end_time": active_res.end_time.isoformat(),
                }
            }), 403

        # daca urmeaza o rezervare, permite altui user sa parcheze, dar primeste un warning
        upcoming_res = (
            Reservation.query
            .filter(
                Reservation.spot_id == spot.id,
                Reservation.status == "active",
                Reservation.start_time > now,
            )
            .order_by(Reservation.start_time.asc())
            .first()
        )

        # existing “one occupied spot per user” check
        occupied_spots = ParkingSpot.query.filter_by(
            occupied_by_email=current_user.email,
            is_occupied=True
        ).first()
        if occupied_spots:
            return jsonify({
                'error': f'Ocupi deja locul {occupied_spots.parking_lot} #{occupied_spots.spot_number}. Eliberează-l înainte de a ocupa altul!'
            }), 409

        spot.is_occupied = True
        spot.occupied_by_email = current_user.email
        db.session.commit()

        payload = {
            'success': True,
            'spot_id': spot.id,
            'is_occupied': spot.is_occupied,
            'occupied_by_email': spot.occupied_by_email
        }

        if upcoming_res:
            payload["warning"] = {
                "type": "UPCOMING_RESERVATION",
                "message": f"Acest loc are o rezervare la {upcoming_res.start_time.isoformat()}. Te rugăm să eliberezi înainte de start.",
                "must_leave_before": upcoming_res.start_time.isoformat(),
                "reservation_end": upcoming_res.end_time.isoformat(),
            }

        return jsonify(payload), 200

    else:
        # Daca e ocupat, doar ocupantul poate elibera
        if spot.occupied_by_email != current_user.email:
            return jsonify({'error': 'Spot already occupied by another user'}), 403
        spot.is_occupied = False
        spot.occupied_by_email = None

    db.session.commit()
    return jsonify({
        'success': True,
        'spot_id': spot.id,
        'is_occupied': spot.is_occupied,
        'occupied_by_email': spot.occupied_by_email
    }), 200
