"""
Constante comune pentru status-uri și tipuri de locuri de parcare.
"""

# Role-uri pentru utilizatori
USER_ROLE_STUDENT = "student"
USER_ROLE_ADMIN = "admin"

USER_ROLES = [
    USER_ROLE_STUDENT,
    USER_ROLE_ADMIN,
]

# statusuri posibile pentru ParkingSpot.current_status
SPOT_STATUS_FREE = "free"
SPOT_STATUS_OCCUPIED = "occupied"
SPOT_STATUS_RESERVED = "reserved"

SPOT_STATUSES = [
    SPOT_STATUS_FREE,
    SPOT_STATUS_OCCUPIED,
    SPOT_STATUS_RESERVED
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
