from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied


class EditPersonalProfileOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if not (
            request.user
            and request.user.is_authenticated
            and request.user.profile == obj
        ):
            raise PermissionDenied("This is not your profile")
        return True


