from rest_framework.permissions import SAFE_METHODS, BasePermission


def role_of(user):
    """Returns 'admin', 'staff', 'guest' or None (anonymous)."""
    if not (user and user.is_authenticated):
        return None
    sp = getattr(user, "staff_profile", None)  # OneToOne reverse; None if missing
    if sp and sp.active:
        return sp.role  # 'admin' or 'staff'
    return "guest"


def is_staff_user(user):
    return role_of(user) in ("staff", "admin")


class IsStaffRole(BasePermission):
    def has_permission(self, request, view):
        return is_staff_user(request.user)


class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        return role_of(request.user) == "admin"


class IsAdminOrReadOnly(BasePermission):
    """Anyone can read, only admins can write."""
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return role_of(request.user) == "admin"


class IsStaffOrReadOnly(BasePermission):
    """Anyone can read, only staff/admin can write."""
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return is_staff_user(request.user)