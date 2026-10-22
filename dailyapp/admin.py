from django.contrib import admin
from .models import userlist, RoomType, Room, Booking, Staff

admin.site.register(userlist)
admin.site.register(RoomType)
admin.site.register(Room)
admin.site.register(Booking)
admin.site.register(Staff)
