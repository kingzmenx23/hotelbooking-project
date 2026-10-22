from django.db.models import ProtectedError
from rest_framework.response import Response
from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    """Booking.room is PROTECT, so deleting a room/room type that has bookings
    would otherwise return a 500. Return a clean 409 instead."""
    if isinstance(exc, ProtectedError):
        return Response(
            {"detail": "Cannot delete: this record is referenced by existing bookings."},
            status=409)
    return exception_handler(exc, context)