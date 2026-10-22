from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from . import models, services
from .permissions import role_of

User = get_user_model()


# ───────────── Auth / users ─────────────
class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    phone = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_email(self, value):
        value = value.lower()
        if User.objects.filter(username=value).exists() or \
                models.userlist.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value

    def validate_password(self, value):
        validate_password(value)  # Django's built-in strength rules
        return value

    @transaction.atomic
    def create(self, d):
        user = User.objects.create_user(
            username=d["email"], email=d["email"],
            password=d["password"], first_name=d["name"],
        )
        # password="!" because the real (hashed) password now lives on the User
        models.userlist.objects.create(
            user=user, name=d["name"], email=d["email"],
            phone=d["phone"], password="!",
        )
        return user


class MeSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="first_name")
    phone = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "name", "phone", "role"]

    def get_phone(self, obj):
        p = getattr(obj, "profile", None)
        return p.phone if p else None

    def get_role(self, obj):
        return role_of(obj)


class MeUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100, required=False)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)


class GuestSerializer(serializers.ModelSerializer):
    """Admin view of guests. Never exposes the password field."""
    class Meta:
        model = models.userlist
        fields = ["id", "name", "email", "phone"]


class StaffSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = models.Staff
        fields = ["id", "name", "username", "role", "active", "password"]

    def validate_password(self, value):
        validate_password(value)
        return value

    @transaction.atomic
    def create(self, d):
        pw = d.pop("password", None)
        if not pw:
            raise serializers.ValidationError({"password": "This field is required."})
        user = User.objects.create_user(username=d["username"], password=pw, is_staff=True)
        return models.Staff.objects.create(user=user, password="!", **d)

    @transaction.atomic
    def update(self, instance, d):
        pw = d.pop("password", None)
        instance = super().update(instance, d)
        if pw and instance.user:
            instance.user.set_password(pw)
            instance.user.save()
        return instance


# ───────────── Rooms ─────────────
class RoomTypeSerializer(serializers.ModelSerializer):
    # filled only when the queryset is annotated (see AvailabilityView)
    available_rooms = serializers.IntegerField(read_only=True)

    class Meta:
        model = models.RoomType
        fields = "__all__"


class RoomSerializer(serializers.ModelSerializer):
    room_type_name = serializers.CharField(source="room_type.name", read_only=True)

    class Meta:
        model = models.Room
        fields = ["id", "room_number", "room_type", "room_type_name", "is_available"]


class AvailabilityQuerySerializer(serializers.Serializer):
    check_in = serializers.DateField()
    check_out = serializers.DateField()
    guests = serializers.IntegerField(required=False, min_value=1)

    def validate(self, a):
        if a["check_out"] <= a["check_in"]:
            raise serializers.ValidationError("check_out must be after check_in.")
        if a["check_in"] < timezone.localdate():
            raise serializers.ValidationError("check_in cannot be in the past.")
        return a


# ───────────── Bookings ─────────────
class BookingSerializer(serializers.ModelSerializer):
    room_detail = RoomSerializer(source="room", read_only=True)
    guest = serializers.CharField(source="user.name", read_only=True)
    handled_by_name = serializers.CharField(
        source="handled_by.name", read_only=True, default=None)
    nights = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = models.Booking
        fields = ["id", "room", "room_detail", "guest", "guests",
                  "check_in", "check_out", "nights", "total_price",
                  "status", "handled_by_name", "created_at"]
        read_only_fields = ["status", "created_at"]

    def get_nights(self, obj):
        return (obj.check_out - obj.check_in).days

    def get_total_price(self, obj):
        return str(self.get_nights(obj) * obj.room.room_type.price)

    def validate(self, a):
        if a["check_out"] <= a["check_in"]:
            raise serializers.ValidationError("check_out must be after check_in.")
        if a["check_in"] < timezone.localdate():
            raise serializers.ValidationError("check_in cannot be in the past.")
        if not a["room"].is_available:
            raise serializers.ValidationError({"room": "This room is not available."})
        return a

    def create(self, d):
        # Lock the room row so two people can't book it at the same moment
        # (the lock is a no-op on SQLite, effective on PostgreSQL/MySQL).
        with transaction.atomic():
            room = models.Room.objects.select_for_update().get(pk=d["room"].pk)
            clash = services.overlapping_bookings(d["check_in"], d["check_out"]).filter(room=room)
            if clash.exists():
                raise serializers.ValidationError(
                    {"room": "Room already booked for these dates."})
            d["room"] = room
            return models.Booking.objects.create(status="pending", **d)


class BookingStatusSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=services.BOOKING_STATUSES)

    class Meta:
        model = models.Booking
        fields = ["status"]