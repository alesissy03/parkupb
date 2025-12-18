"""
Endpoint-uri pentru rezervări.

TODO (Task 9):
- Creare rezervare (POST /)
- Anulare rezervare (DELETE /<id>)
TODO (Task 10):
- Vizualizare rezervări anterioare pentru user (GET /my)
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models import Reservation
from app.services.reservation_service import (
    create_reservation as create_reservation_service,
    cancel_reservation as cancel_reservation_service,
    get_user_reservations,
)
from app.services.reservation_service import finalize_expired_reservations, cancel_no_show_reservations


reservation_bp = Blueprint("reservation", __name__)

@reservation_bp.route("/", methods=["POST"])
@login_required
def create_reservation():
    """
    TODO (Task 9): Creează o rezervare pentru un loc de parcare.

    Request JSON:
    {
      "spot_id": 10,
      "start_time": "2025-11-24T10:00:00",
      "end_time": "2025-11-24T12:00:00"
    }

    Răspuns 201 (exemplu):
    {
      "id": 5,
      "user_id": 1,
      "spot_id": 10,
      "start_time": "2025-11-24T10:00:00",
      "end_time": "2025-11-24T12:00:00",
      "status": "active"
    }

    Erori:
    - 400: interval invalid (start >= end etc.)
    - 409: loc deja rezervat / ocupat în interval
    """
    # return {"message": "create_reservation – TODO Task 9"}, 501
    data = request.get_json() or {}
    spot_id = data.get("spot_id")
    start_time = data.get("start_time")
    end_time = data.get("end_time")

    if spot_id is None or not start_time or not end_time:
        return jsonify({"error": "INVALID_DATA", "message": "spot_id, start_time, end_time required"}), 400

    try:
        from app.services.reservation_service import finalize_expired_reservations, cancel_no_show_reservations

        r = create_reservation_service(current_user, int(spot_id), start_time, end_time)
        return jsonify({
            "id": r.id,
            "user_id": r.user_id,
            "spot_id": r.spot_id,
            "start_time": r.start_time.isoformat(),
            "end_time": r.end_time.isoformat(),
            "status": r.status,
        }), 201

    except ValueError as e:
        code = str(e)

        if code in ("INVALID_DATETIME", "INVALID_TIMEFRAME"):
            return jsonify({"error": code}), 400

        if code == "SPOT_NOT_FOUND":
            return jsonify({"error": "NOT_FOUND"}), 404

        if code in ("SPOT_OCCUPIED", "SPOT_OVERLAP", "EXISTING_RESERVATION_OVERLAP"):
            return jsonify({"error": code}), 409

        return jsonify({"error": "BAD_REQUEST"}), 400

@reservation_bp.route("/<int:reservation_id>", methods=["DELETE"])
@login_required
def cancel_reservation(reservation_id):
    """
    TODO (Task 9): Anulează o rezervare existentă.

    Răspuns 200 (exemplu):
    {
      "success": true
    }

    Erori:
    - 404: rezervare inexistentă
    - 403: user-ul nu are dreptul să anuleze această rezervare
    """
    # return {"message": "cancel_reservation – TODO Task 9"}, 501
    try:
        cancel_reservation_service(reservation_id, current_user)
        return jsonify({"success": True}), 200

    except ValueError as e:
        code = str(e)

        if code == "NOT_FOUND":
            return jsonify({"error": "NOT_FOUND"}), 404

        if code == "FORBIDDEN":
            return jsonify({"error": "FORBIDDEN"}), 403

        return jsonify({"error": "BAD_REQUEST"}), 400

@reservation_bp.route("/my", methods=["GET"])
@login_required
def my_reservations():
    """
    TODO (Task 10): Returnează rezervările utilizatorului curent (istoric).

    Răspuns 200 (exemplu):
    [
      {
        "id": 5,
        "spot_id": 10,
        "lot_id": 1,
        "start_time": "...",
        "end_time": "...",
        "status": "finished"
      },
      ...
    ]
    """
    finalize_expired_reservations()
    cancel_no_show_reservations()

    # return {"message": "my_reservations – TODO Task 10"}, 501
    reservations = get_user_reservations(current_user.id)

    # Full history response (active/cancelled/finished)
    return jsonify([
        {
            "id": r.id,
            "spot_id": r.spot_id,
            "start_time": r.start_time.isoformat(),
            "end_time": r.end_time.isoformat(),
            "status": r.status,
        }
        for r in reservations
    ]), 200
