"""
Constante comune pentru status-uri și tipuri de locuri de parcare.
"""

# statusuri posibile pentru ParkingSpot.current_status
SPOT_STATUS_FREE = "free"
SPOT_STATUS_OCCUPIED = "occupied"
SPOT_STATUS_RESERVED = "reserved"
SPOT_STATUS_OUT_OF_SERVICE = "out_of_service"

SPOT_STATUSES = [
    SPOT_STATUS_FREE,
    SPOT_STATUS_OCCUPIED,
    SPOT_STATUS_RESERVED,
    SPOT_STATUS_OUT_OF_SERVICE,
]

# statusuri posibile pentru Reservation.status
RESERVATION_STATUS_ACTIVE = "active"
RESERVATION_STATUS_CANCELLED = "cancelled"
RESERVATION_STATUS_FINISHED = "finished"

RESERVATION_STATUSES = [
    RESERVATION_STATUS_ACTIVE,
    RESERVATION_STATUS_CANCELLED,
    RESERVATION_STATUS_FINISHED,
]

# tipuri de locuri de parcare
# SPOT_TYPE_STUDENT = "student"
# SPOT_TYPE_STAFF = "staff"
SPOT_TYPE_DISABLED = "disabled"
SPOT_TYPE_VISITOR = "visitor"

SPOT_TYPES = [
#     SPOT_TYPE_STUDENT,
#     SPOT_TYPE_STAFF,
    SPOT_TYPE_DISABLED,
    SPOT_TYPE_VISITOR,
]
