# from django.db import models


# # Create your models here.

# class userlist(models.Model):
#     # userid = models.IntegerField(primary_key=True),   #don't need auto increament cos django only need primary it will automatically auto increment
#     name = models.CharField(max_length=100)
#     email = models.EmailField(unique=True)
#     password = models.CharField(max_length=128)
#     # age = models.IntegerField()
#     # gender = models.CharField()
#     phone = models.CharField(max_length=20)

#      # link to Django's login User (used by the API)
#     user = models.OneToOneField(
#         settings.AUTH_USER_MODEL, null=True, blank=True,
#         on_delete=models.CASCADE, related_name="profile",
#     )
 

#     def __str__(self):                      #__str__() is defined so that when Django/Python needs to represent your object as a string, you decide what should be displayed.
#         return f"NAME: {self.name} - EMAIL: {self.email}"


# class RoomType(models.Model):
#     name = models.CharField(max_length=100)
#     description = models.TextField()
#     price = models.DecimalField(max_digits=10, decimal_places=2)

#     def __str__(self):
#         return str(self.name)


# class Room(models.Model):
#     room_number = models.IntegerField(unique=True)
#     room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE)
#     is_available = models.BooleanField(default=True)

#     def __str__(self):
#         return str(self.room_number)


# # class Booking(models.Model):
# #     user = models.ForeignKey(userlist, on_delete=models.CASCADE)
# #     room = models.ForeignKey(Room, on_delete=models.PROTECT)
    

# #     check_in = models.DateField()
# #     check_out = models.DateField()

# #     guests = models.PositiveIntegerField()

# #     status = models.CharField(
# #         max_length=20,
# #         default="pending"
# #     )

# #     created_at = models.DateTimeField(auto_now_add=True)


 
# # Staff is defined before Booking so Booking can reference it directly
# class Booking(models.Model):
#     user = models.ForeignKey(userlist, on_delete=models.CASCADE)    # the guest
#     room = models.ForeignKey(Room, on_delete=models.PROTECT)
#     handled_by = models.ForeignKey(                                 # staff who last changed the status
#         Staff, null=True, blank=True,
#         on_delete=models.SET_NULL, related_name="handled_bookings",
#     )
 
#     check_in = models.DateField()
#     check_out = models.DateField()
#     guests = models.PositiveIntegerField()
 
#     status = models.CharField(max_length=20, default="pending")
#     created_at = models.DateTimeField(auto_now_add=True)
 
#     def __str__(self):
#         return f"Booking #{self.pk} - room {self.room_id} ({self.status})"

        

# # class Staff(models.Model):
# #     ROLE_CHOICES = (
# #         ("admin", "Admin"),
# #         ("staff", "Staff"),
# #     )
# #     name = models.CharField(max_length=100)
# #     username = models.CharField(max_length=50, unique=True)
# #     password = models.CharField(max_length=128)
# #     role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="staff")
# #     active = models.BooleanField(default=True)

# #     def __str__(self):
# #         return f"{self.name} ({self.role})"



 
 
# class Staff(models.Model):
#     ROLE_CHOICES = (
#         ("admin", "Admin"),
#         ("staff", "Staff"),
#     )
#     name = models.CharField(max_length=100)
#     username = models.CharField(max_length=50, unique=True)
#     password = models.CharField(max_length=128)     # legacy; real passwords now live on the Django User
#     role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="staff")
#     active = models.BooleanField(default=True)
 
#     # link to Django's login User (used by the API)
#     user = models.OneToOneField(
#         settings.AUTH_USER_MODEL, null=True, blank=True,
#         on_delete=models.CASCADE, related_name="staff_profile",
#     )
 
#     def __str__(self):
#         return f"{self.name} ({self.role})"





from django.conf import settings
from django.db import models


class userlist(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)     # legacy; real passwords now live on the Django User
    phone = models.CharField(max_length=20)

    # link to Django's login User (used by the API)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.CASCADE, related_name="profile",
    )

    def __str__(self):
        return f"NAME: {self.name} - EMAIL: {self.email}"


class RoomType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return str(self.name)


class Room(models.Model):
    room_number = models.IntegerField(unique=True)
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return str(self.room_number)


class Staff(models.Model):
    ROLE_CHOICES = (
        ("admin", "Admin"),
        ("staff", "Staff"),
    )
    name = models.CharField(max_length=100)
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=128)     # legacy; real passwords now live on the Django User
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="staff")
    active = models.BooleanField(default=True)

    # link to Django's login User (used by the API)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.CASCADE, related_name="staff_profile",
    )

    def __str__(self):
        return f"{self.name} ({self.role})"


# Staff is defined before Booking so Booking can reference it directly
class Booking(models.Model):
    user = models.ForeignKey(userlist, on_delete=models.CASCADE)    # the guest
    room = models.ForeignKey(Room, on_delete=models.PROTECT)
    handled_by = models.ForeignKey(                                 # staff who last changed the status
        Staff, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="handled_bookings",
    )

    check_in = models.DateField()
    check_out = models.DateField()
    guests = models.PositiveIntegerField()

    status = models.CharField(max_length=20, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking #{self.pk} - room {self.room_id} ({self.status})"