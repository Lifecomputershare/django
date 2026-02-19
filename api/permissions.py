from rest_framework import permissions

from .models import UserProfile


def _get_role(request):
    user = request.user
    if not user or not user.is_authenticated:
        return None
    profile = getattr(user, "profile", None)
    if not profile:
        return None
    return profile.role


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return _get_role(request) == UserProfile.ROLE_ADMIN


class IsRecruiter(permissions.BasePermission):
    def has_permission(self, request, view):
        return _get_role(request) == UserProfile.ROLE_RECRUITER


class IsCandidate(permissions.BasePermission):
    def has_permission(self, request, view):
        return _get_role(request) == UserProfile.ROLE_CANDIDATE


class IsAdminOrRecruiter(permissions.BasePermission):
    def has_permission(self, request, view):
        role = _get_role(request)
        return role in {UserProfile.ROLE_ADMIN, UserProfile.ROLE_RECRUITER}

