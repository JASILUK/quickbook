from rest_framework.permissions import BasePermission


class IsStaffUser(BasePermission):
    """
    Allow access only to authenticated,
    active QuickBook staff users.
    """

    message = "Staff access is required."

    def has_permission(
        self,
        request,
        view,
    ):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and request.user.role
            == request.user.Role.STAFF
        )