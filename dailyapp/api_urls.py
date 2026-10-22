from django.urls import include, path
from drf_spectacular.views import (SpectacularAPIView, SpectacularRedocView,
                                   SpectacularSwaggerView)
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from . import api_views as v

router = DefaultRouter()
router.register("room-types", v.RoomTypeViewSet, basename="roomtype")
router.register("rooms", v.RoomViewSet, basename="room")
router.register("bookings", v.BookingViewSet, basename="booking")
router.register("admin/guests", v.GuestViewSet, basename="admin-guest")
router.register("admin/staff", v.StaffViewSet, basename="admin-staff")

urlpatterns = [
    # auth
    path("auth/register/", v.RegisterView.as_view()),
    path("auth/login/", v.LoginView.as_view()),
    path("auth/refresh/", TokenRefreshView.as_view()),
    path("auth/logout/", v.LogoutView.as_view()),
    path("auth/google/", v.GoogleLoginView.as_view()),
    path("auth/me/", v.MeView.as_view()),
    # rooms / bookings
    path("availability/", v.AvailabilityView.as_view()),
    path("admin/stats/", v.StatsView.as_view()),
    # auto-generated docs
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema")),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema")),
    path("", include(router.urls)),
]