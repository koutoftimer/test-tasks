from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied


class IsOwnProfile(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.profile != obj:
            raise PermissionDenied("This is not your profile")
        return True
