from django.urls import path,include
from . import views


urlpatterns = [
    path('',views.userpage,name='userpage'),
    path('logout/', views.logout_view, name='logout'),
    # path('index/',views.index,name='index'),
    # path('register/',views.registerform,name='register'),
    path('login/',views.login,name='login'),
    path('availability/', views.availability, name='availability'),
    path('booking/',views.booking,name='booking'),
    path('rooms/<slug:slug>/', views.room_detail, name='room_detail'),
    path('payment/', views.payment, name='payment'),
    path('staff/', views.staff_login, name='staff_login'),
    path('staff/logout/', views.staff_logout, name='staff_logout'),
    path('staff/dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('staff/rooms/add/', views.room_manage, name='room_add'),
    path('staff/rooms/<int:room_id>/edit/', views.room_manage, name='room_edit'),
    path('staff/bookings/<int:booking_id>/status/', views.booking_status, name='booking_status'),
    path('admin/login/', views.admin_login, name='admin_login'),
    path('admin_panel/users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    path('admin_panel/staff/<int:staff_id>/delete/', views.delete_staff, name='delete_staff'),
    path("admin_panel/", views.admin, name="admin"),

]

