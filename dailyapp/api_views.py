# from django.urls import include, path
# from drf_spectacular.views import (SpectacularAPIView, SpectacularRedocView,
#                                    SpectacularSwaggerView)
# from rest_framework.routers import DefaultRouter
# from rest_framework_simplejwt.views import TokenRefreshView

# from . import api_views as v

# router = DefaultRouter()
# router.register("room-types", v.RoomTypeViewSet, basename="roomtype")
# router.register("rooms", v.RoomViewSet, basename="room")
# router.register("bookings", v.BookingViewSet, basename="booking")
# router.register("admin/guests", v.GuestViewSet, basename="admin-guest")
# router.register("admin/staff", v.StaffViewSet, basename="admin-staff")

# urlpatterns = [
#     # auth
#     path("auth/register/", v.RegisterView.as_view()),
#     path("auth/login/", v.LoginView.as_view()),
#     path("auth/refresh/", TokenRefreshView.as_view()),
#     path("auth/logout/", v.LogoutView.as_view()),
#     path("auth/google/", v.GoogleLoginView.as_view()),
#     path("auth/me/", v.MeView.as_view()),
#     # rooms / bookings
#     path("availability/", v.AvailabilityView.as_view()),
#     path("admin/stats/", v.StatsView.as_view()),
#     # auto-generated docs
#     path("schema/", SpectacularAPIView.as_view(), name="schema"),
#     path("docs/", SpectacularSwaggerView.as_view(url_name="schema")),
#     path("redoc/", SpectacularRedocView.as_view(url_name="schema")),
#     path("", include(router.urls)),
# ]




from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from google.auth.transport import requests as g_requests
from google.oauth2 import id_token
from rest_framework import generics, mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from . import models, services
from . import serializers as s
from .permissions import (IsAdminOrReadOnly, IsAdminRole, IsStaffOrReadOnly,
                          IsStaffRole, is_staff_user)

User = get_user_model()


def tokens_for(user):
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


# ═════════════ BASIC: auth ═════════════
class LoginView(TokenObtainPairView):
    """POST {"username": <email>, "password": ...} → access + refresh."""
    throttle_scope = "auth"


class RegisterView(generics.CreateAPIView):
    serializer_class = s.RegisterSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_scope = "auth"

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        return Response({"user": s.MeSerializer(user).data, **tokens_for(user)}, status=201)


class LogoutView(APIView):
    """POST {"refresh": ...} → blacklists the refresh token."""
    def post(self, request):
        try:
            RefreshToken(request.data.get("refresh")).blacklist()
        except TokenError:
            raise ValidationError({"refresh": "Invalid or expired token."})
        return Response(status=204)


class MeView(APIView):
    def get(self, request):
        return Response(s.MeSerializer(request.user).data)

    def patch(self, request):
        ser = s.MeUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d, user = ser.validated_data, request.user
        with transaction.atomic():
            if "name" in d:
                user.first_name = d["name"]
                user.save(update_fields=["first_name"])
                if hasattr(user, "profile"):
                    user.profile.name = d["name"]
            if "phone" in d and hasattr(user, "profile"):
                user.profile.phone = d["phone"]
            if hasattr(user, "profile"):
                user.profile.save()
        return Response(s.MeSerializer(user).data)


class GoogleLoginView(APIView):
    """POST {"id_token": <Google credential>} → our own JWTs."""
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_scope = "auth"

    def post(self, request):
        token = request.data.get("id_token")
        if not token:
            raise ValidationError({"id_token": "This field is required."})
        try:
            info = id_token.verify_oauth2_token(
                token, g_requests.Request(), settings.GOOGLE_CLIENT_ID)
        except ValueError:
            return Response({"detail": "Invalid Google token."}, status=401)
        if not info.get("email_verified"):
            return Response({"detail": "Google email is not verified."}, status=401)

        email = info["email"].lower()
        name = info.get("name") or info.get("given_name") or email
        with transaction.atomic():
            user, created = User.objects.get_or_create(
                username=email, defaults={"email": email, "first_name": name})
            if created:
                user.set_unusable_password()
                user.save()
            if not hasattr(user, "staff_profile"):
                profile, _ = models.userlist.objects.get_or_create(
                    email=email,
                    defaults={"user": user, "name": name, "phone": "", "password": "!"})
                if profile.user_id is None:   # guest registered the old way
                    profile.user = user
                    profile.save(update_fields=["user"])
        return Response({"user": s.MeSerializer(user).data, **tokens_for(user)})


# ═════════════ INTERMEDIATE: rooms & availability ═════════════
class RoomTypeViewSet(viewsets.ModelViewSet):
    queryset = models.RoomType.objects.all()
    serializer_class = s.RoomTypeSerializer
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ["name"]


class RoomViewSet(viewsets.ModelViewSet):
    queryset = models.Room.objects.select_related("room_type")
    serializer_class = s.RoomSerializer
    permission_classes = [IsStaffOrReadOnly]
    filterset_fields = ["room_type", "is_available"]
    search_fields = ["room_number"]


class AvailabilityView(APIView):
    """GET /availability/?check_in=2026-11-01&check_out=2026-11-04&guests=2"""
    permission_classes = [AllowAny]

    def get(self, request):
        q = s.AvailabilityQuerySerializer(data=request.query_params)
        q.is_valid(raise_exception=True)
        ci, co = q.validated_data["check_in"], q.validated_data["check_out"]

        booked = services.overlapping_bookings(ci, co).values("room_id")
        # NOTE: "room" is the default reverse name for Room.room_type.
        # If you set related_name on that FK, change it here.
        types = models.RoomType.objects.annotate(
            available_rooms=Count(
                "room", filter=Q(room__is_available=True) & ~Q(room__id__in=booked))
        )
        data = s.RoomTypeSerializer(types, many=True).data
        return Response({"check_in": ci, "check_out": co, "room_types": data})


# ═════════════ ADVANCED: bookings ═════════════
class BookingViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
                     mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    Guests: create, list and view THEIR bookings, cancel their own.
    Staff/admin: see every booking and change its status.
    """
    serializer_class = s.BookingSerializer
    filterset_fields = ["status", "room", "check_in", "check_out"]
    search_fields = ["user__name", "user__email", "room__room_number"]
    ordering_fields = ["created_at", "check_in"]
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = models.Booking.objects.select_related(
            "user", "room", "room__room_type", "handled_by")
        if is_staff_user(self.request.user):
            return qs
        return qs.filter(user__user=self.request.user)  # object-level security

    def perform_create(self, serializer):
        profile = getattr(self.request.user, "profile", None)
        if profile is None:
            raise PermissionDenied("Only guest accounts can make bookings.")
        serializer.save(user=profile)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        booking = self.get_object()  # 404 if it isn't yours
        if booking.status not in ("pending", "confirmed"):
            raise ValidationError("Only pending or confirmed bookings can be cancelled.")
        booking.status = "cancelled"  # make sure this value exists in your status choices
        booking.save(update_fields=["status"])
        return Response(self.get_serializer(booking).data)

    @action(detail=True, methods=["patch"], url_path="status",
            permission_classes=[IsStaffRole])
    def set_status(self, request, pk=None):
        booking = self.get_object()
        ser = s.BookingStatusSerializer(booking, data=request.data)
        ser.is_valid(raise_exception=True)
        # record which staff member made the change
        ser.save(handled_by=request.user.staff_profile)
        return Response(self.get_serializer(booking).data)


# ═════════════ ADVANCED: admin area ═════════════
class GuestViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                   mixins.DestroyModelMixin, viewsets.GenericViewSet):
    queryset = models.userlist.objects.all().order_by("-id")
    serializer_class = s.GuestSerializer
    permission_classes = [IsAdminRole]
    search_fields = ["name", "email", "phone"]

    def perform_destroy(self, instance):
        user = instance.user
        instance.delete()
        if user:
            user.delete()  # remove the login too


class StaffViewSet(viewsets.ModelViewSet):
    queryset = models.Staff.objects.all().order_by("id")
    serializer_class = s.StaffSerializer
    permission_classes = [IsAdminRole]
    search_fields = ["name", "username"]

    def perform_destroy(self, instance):
        if instance.user_id == self.request.user.id:
            raise ValidationError("You cannot delete your own admin account.")
        user = instance.user
        instance.delete()
        if user:
            user.delete()


class StatsView(APIView):
    permission_classes = [IsStaffRole]

    def get(self, request):
        today = timezone.localdate()
        b = models.Booking.objects
        return Response({
            "rooms_total": models.Room.objects.count(),
            "rooms_available": models.Room.objects.filter(is_available=True).count(),
            "guests": models.userlist.objects.count(),
            "bookings_by_status": {
                r["status"]: r["n"] for r in b.values("status").annotate(n=Count("id"))
            },
            "arrivals_today": b.filter(check_in=today, status__in=["pending", "confirmed"]).count(),
            "in_house": b.filter(status="checked_in").count(),
        })