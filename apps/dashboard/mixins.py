from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect

from apps.accounts.authentication import CookieJWTAuthentication


class StaffDashboardRequiredMixin:
    """
    Allows only authenticated staff users to access
    the custom HTML dashboard using the same JWT
    access cookie used by the API.
    """

    def dispatch(self, request, *args, **kwargs):
        authentication = CookieJWTAuthentication()

        try:
            result = authentication.authenticate(request)

        except Exception:
            return HttpResponseRedirect(
                "/api/auth/login/"
            )

        if result is None:
            return HttpResponseRedirect(
                "/api/auth/login/"
            )

        user, _validated_token = result

        if (
            not user.is_authenticated
            or not user.is_active
            or user.role != user.Role.STAFF
        ):
            raise PermissionDenied(
                "Staff access is required."
            )

        # Make the authenticated user available to
        # Django templates as request.user.
        request.user = user

        return super().dispatch(
            request,
            *args,
            **kwargs,
        )