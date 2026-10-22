from . import models

# Bookings in these states block the room (same list your template views use)
ACTIVE_STATUSES = ["pending", "confirmed", "checked_in"]
# Booking.status has no choices in your model, so the API enforces this list
BOOKING_STATUSES = ["pending", "confirmed", "checked_in", "checked_out", "cancelled"]


def overlapping_bookings(check_in, check_out):
    """Bookings that clash with [check_in, check_out)."""
    return models.Booking.objects.filter(
        status__in=ACTIVE_STATUSES,
        check_in__lt=check_out,
        check_out__gt=check_in,
    )


def free_rooms(check_in, check_out, room_type=None):
    qs = models.Room.objects.filter(is_available=True)
    if room_type is not None:
        qs = qs.filter(room_type=room_type)
    booked = overlapping_bookings(check_in, check_out).values("room_id")
    return qs.exclude(id__in=booked)