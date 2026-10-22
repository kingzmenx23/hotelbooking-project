from django.shortcuts import render, redirect, get_object_or_404
from . import models
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils.text import slugify

User = get_user_model()


# ───────────── helpers ─────────────
def _authenticate_email_or_username(request, identifier, password):
    """Django checks the HASHED password. Tries the text as typed, then lowercased."""
    user = authenticate(request, username=identifier, password=password)
    if user is None and identifier != identifier.lower():
        user = authenticate(request, username=identifier.lower(), password=password)
    return user


def _start_staff_session(request, staff):
    request.session.cycle_key()          # new session id on login
    request.session['staff_id'] = staff.id
    request.session['staff_username'] = staff.username
    request.session['staff_role'] = staff.role
    request.session['staff_name'] = staff.name


# ───────────── guest register / login ─────────────
def userpage(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        phnnumb = request.POST.get("phn", "").strip()

        if not email or not password:
            return render(request, 'dailyapp/userpage.html',
                          {'error': 'Email and password are required.'})

        if User.objects.filter(username=email).exists() or \
                models.userlist.objects.filter(email__iexact=email).exists():
            return render(request, 'dailyapp/userpage.html',
                          {'error': 'This email is already registered.'})

        try:
            validate_password(password)
        except ValidationError as e:
            return render(request, 'dailyapp/userpage.html',
                          {'error': ' '.join(e.messages)})

        with transaction.atomic():
            auth_user = User.objects.create_user(
                username=email, email=email, password=password, first_name=name)
            profile = models.userlist.objects.create(
                user=auth_user, name=name, email=email,
                phone=phnnumb, password="!",     # real password is hashed on auth_user
            )

        request.session.cycle_key()
        request.session['username'] = profile.name
        request.session['user_id'] = profile.id
        return redirect('userpage')

    return render(request, 'dailyapp/userpage.html')


def logout_view(request):
    request.session.flush()
    return redirect('userpage')


def login(request):
    """Single login form for guests AND staff/admin (same as before)."""
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")

        user = _authenticate_email_or_username(request, email, password)

        if user is not None:
            staff = getattr(user, "staff_profile", None)
            if staff:
                if staff.active:
                    _start_staff_session(request, staff)
                    return redirect("admin" if staff.role == "admin" else "staff_dashboard")
            else:
                profile = getattr(user, "profile", None)
                if profile:
                    request.session.cycle_key()
                    request.session["username"] = profile.name
                    request.session["user_id"] = profile.id
                    return redirect("userpage")

        messages.error(request, "Invalid email or password.")
        return redirect("userpage")

    return redirect("userpage")


# ───────────── guest pages (unchanged) ─────────────
def availability(request):

    if not request.session.get('username'):
        messages.warning(request, "Login needed to check availability.")
        return redirect('userpage')

    rooms = models.RoomType.objects.all()

    check_in = request.GET.get('check_in')
    check_out = request.GET.get('check_out')
    guests = request.GET.get('guests')

    request.session['check_in'] = check_in
    request.session['check_out'] = check_out
    request.session['guests'] = guests

    available_ids = []
    if check_in and check_out:
        for room_type in rooms:
            room_ids = list(models.Room.objects.filter(room_type=room_type, is_available=True).values_list('id', flat=True))
            if room_ids:
                booked = models.Booking.objects.filter(
                    room_id__in=room_ids,
                    status__in=['pending', 'confirmed', 'checked_in'],
                    check_in__lt=check_out,
                    check_out__gt=check_in,
                ).values_list('room_id', flat=True)
                if set(room_ids) - set(booked):
                    available_ids.append(room_type.id)
    else:
        available_ids = list(rooms.values_list('id', flat=True))

    return render(request, 'dailyapp/availability.html', {
        'rooms': rooms, 'available_ids': available_ids,
        'check_in': check_in, 'check_out': check_out, 'guests': guests,
    })


def booking(request):

    if not request.session.get('username'):
        messages.warning(request, "Login needed.")
        return redirect('userpage')

    room_type_id = request.GET.get('room_type')

    if not room_type_id:
        messages.warning(request, "Please select a room type.")
        return redirect('availability')

    check_in = request.GET.get('check_in') or request.session.get('check_in')
    check_out = request.GET.get('check_out') or request.session.get('check_out')
    guests = request.GET.get('guests') or request.session.get('guests')

    room_type = models.RoomType.objects.get(id=room_type_id)

    rooms = models.Room.objects.filter(
        room_type=room_type,
        is_available=True
    )

    if check_in and check_out:
        booked_ids = models.Booking.objects.filter(
            room__room_type=room_type,
            status__in=['pending', 'confirmed', 'checked_in'],
            check_in__lt=check_out,
            check_out__gt=check_in
        ).values_list('room_id', flat=True)

        rooms = rooms.exclude(id__in=booked_ids)

    return render(
        request,
        'dailyapp/booking.html',
        {
            'check_in': check_in,
            'check_out': check_out,
            'guests': guests,
            'room_type': room_type,
            'rooms': rooms,
        }
    )


def room_detail(request, slug):
    room_type = None
    for item in models.RoomType.objects.all():
        if slugify(item.name) == slug:
            room_type = item
            break
    if room_type is None:
        fallback = {'deluxe': 'Deluxe', 'executive': 'Executive', 'grand-suite': 'Grand'}
        keyword = fallback.get(slug)
        if keyword:
            room_type = models.RoomType.objects.filter(name__icontains=keyword).first()
    if room_type is None:
        messages.warning(request, 'Room details are not available yet.')
        return redirect('availability')
    return render(request, 'dailyapp/room_detail.html', {'room_type': room_type})


def payment(request):
    if not request.session.get('username'):
        messages.warning(request, 'Login needed to continue.')
        return redirect('userpage')
    return render(request, 'dailyapp/payment.html', {
        'room_name': request.GET.get('room_name', 'Maison Royale'),
        'amount': request.GET.get('amount', '0'),
        'check_in': request.GET.get('check_in') or request.session.get('check_in'),
        'check_out': request.GET.get('check_out') or request.session.get('check_out'),
    })


# ───────────── staff / admin login ─────────────
def staff_login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = _authenticate_email_or_username(request, username, password)
        staff = getattr(user, "staff_profile", None) if user else None

        if staff and staff.active:
            _start_staff_session(request, staff)
            return redirect('admin_dashboard' if staff.role == 'admin' else 'staff_dashboard')
        messages.error(request, 'Invalid staff credentials.')
    return render(request, 'dailyapp/staff_login.html')


def staff_logout(request):
    request.session.pop("staff_id", None)
    request.session.pop("staff_username", None)
    request.session.pop("staff_role", None)
    request.session.pop("staff_name", None)

    return redirect("userpage")


def _staff_required(request, role=None):
    current = request.session.get('staff_role')
    return bool(current and (role is None or current == role))


def admin_login(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        user = _authenticate_email_or_username(request, email, password)
        staff = getattr(user, "staff_profile", None) if user else None

        if staff and staff.active and staff.role == 'admin':
            _start_staff_session(request, staff)
            return redirect('admin_dashboard')

        messages.error(request, 'Invalid admin credentials.')

    return render(request, 'dailyapp/admin.html')


# ───────────── dashboards ─────────────
def admin_dashboard(request):
    if not _staff_required(request, 'admin'):
        return redirect('staff_login')
    return render(request, 'dailyapp/admin_dashboard.html', {
        'rooms': models.Room.objects.select_related('room_type').all(),
        'room_types': models.RoomType.objects.all(),
        'bookings': models.Booking.objects.select_related('user', 'room', 'room__room_type').order_by('-created_at'),
        'users': models.userlist.objects.all(),
        'staff_members': models.Staff.objects.all(),
    })


def staff_dashboard(request):

    if not _staff_required(request, "staff"):
        return redirect("userpage")

    rooms = models.Room.objects.select_related("room_type").all()

    available_rooms = rooms.filter(is_available=True)

    bookings = models.Booking.objects.select_related(
        "user",
        "room",
        "room__room_type"
    ).order_by("-created_at")

    return render(
        request,
        "dailyapp/staff.html",
        {
            "rooms": rooms,
            "available_rooms": available_rooms,
            "bookings": bookings,
        }
    )


def room_manage(request, room_id=None):
    if not _staff_required(request):
        return redirect('staff_login')
    room = get_object_or_404(models.Room, id=room_id) if room_id else None
    if request.method == 'POST':
        room_number = request.POST.get('room_number')
        room_type_id = request.POST.get('room_type')
        available = request.POST.get('is_available') == 'on'
        if room:
            room.room_number = room_number
            room.room_type_id = room_type_id
            room.is_available = available
            room.save()
        else:
            models.Room.objects.create(room_number=room_number, room_type_id=room_type_id, is_available=available)
        return redirect('admin' if request.session.get('staff_role') == 'admin' else 'staff_dashboard')
    return render(request, 'dailyapp/room_form.html', {'room': room, 'room_types': models.RoomType.objects.all()})


def booking_status(request, booking_id):
    if not _staff_required(request):
        return redirect('staff_login')
    booking = get_object_or_404(models.Booking, id=booking_id)
    if request.method == 'POST':
        booking.status = request.POST.get('status', booking.status)
        booking.handled_by_id = request.session.get('staff_id')   # remember who changed it
        booking.save(update_fields=['status', 'handled_by'])
    return redirect('admin_dashboard' if request.session.get('staff_role') == 'admin' else 'staff_dashboard')


def delete_user(request, user_id):

    if not _staff_required(request, "admin"):
        return redirect("userpage")

    guest = get_object_or_404(models.userlist, pk=user_id)

    if request.method == "POST":
        login_account = guest.user
        guest.delete()
        if login_account:
            login_account.delete()      # remove the login too, so the email can't still sign in

    return redirect("admin")


def delete_staff(request, staff_id):
    if not _staff_required(request, 'admin'):
        return redirect('admin_login')

    staff = get_object_or_404(models.Staff, id=staff_id)

    if staff.id == request.session.get('staff_id'):
        messages.error(request, 'You cannot delete your own admin account.')
        return redirect('admin_dashboard')

    if request.method == 'POST':
        login_account = staff.user
        staff.delete()
        if login_account:
            login_account.delete()

    return redirect('admin_dashboard')


def admin(request):
    if not _staff_required(request, "admin"):
        return redirect("admin_login")

    return render(request, "dailyapp/admin.html", {
        "users": models.userlist.objects.all(),
        "staff_members": models.Staff.objects.all(),
        "rooms": models.Room.objects.select_related("room_type").all(),
        "bookings": models.Booking.objects.select_related(
            "user", "room", "room__room_type"
        ).order_by("-created_at"),
    })