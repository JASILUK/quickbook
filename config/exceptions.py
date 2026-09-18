from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


class ServiceError(Exception):
    """
    Base exception for expected business/service errors.
    """

    default_message = "A business error occurred."
    default_code = "SERVICE_ERROR"
    default_status = status.HTTP_400_BAD_REQUEST

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        status_code: int | None = None,
    ):
        self.message = (
            message
            if message is not None
            else self.default_message
        )

        self.code = (
            code
            if code is not None
            else self.default_code
        )

        self.status_code = (
            status_code
            if status_code is not None
            else self.default_status
        )

        super().__init__(self.message)


# ======================================================================
# AUTHENTICATION / ACCOUNT ERRORS
# ======================================================================


class AuthenticationServiceError(ServiceError):
    """
    Base error for authentication-related business failures.
    """

    default_code = "AUTHENTICATION_ERROR"
    default_status = status.HTTP_401_UNAUTHORIZED


class RegistrationError(AuthenticationServiceError):
    """
    Raised when customer registration fails.
    """

    default_code = "REGISTRATION_ERROR"
    default_status = status.HTTP_400_BAD_REQUEST


class LoginError(AuthenticationServiceError):
    """
    Raised when login fails.
    """

    default_code = "LOGIN_ERROR"
    default_status = status.HTTP_401_UNAUTHORIZED


# ======================================================================
# REFERRAL ERRORS
# ======================================================================


class ReferralServiceError(ServiceError):
    """
    Base error for referral-related business failures.
    """

    default_code = "REFERRAL_ERROR"
    default_status = status.HTTP_400_BAD_REQUEST


class ReferralPlacementError(ReferralServiceError):
    """
    Raised when a valid binary referral placement
    cannot be found.
    """

    default_code = "REFERRAL_PLACEMENT_ERROR"
    default_status = status.HTTP_400_BAD_REQUEST


# ======================================================================
# CUSTOMER ERRORS
# ======================================================================


class CustomerServiceError(ServiceError):
    """
    Base error for customer-management business failures.
    """

    default_code = "CUSTOMER_ERROR"
    default_status = status.HTTP_400_BAD_REQUEST


class CustomerNotFoundError(CustomerServiceError):
    """
    Raised when a requested customer does not exist.
    """

    default_code = "CUSTOMER_NOT_FOUND"
    default_status = status.HTTP_404_NOT_FOUND


# ======================================================================
# PERMISSION ERRORS
# ======================================================================


class PermissionServiceError(ServiceError):
    """
    Raised when a business operation is not permitted.
    """

    default_code = "PERMISSION_DENIED"
    default_status = status.HTTP_403_FORBIDDEN



class VendorServiceError(ServiceError):
    default_code = "VENDOR_ERROR"
    default_status = status.HTTP_400_BAD_REQUEST


class VendorNotFoundError(VendorServiceError):
    default_code = "VENDOR_NOT_FOUND"
    default_status = status.HTTP_404_NOT_FOUND



class EventServiceError(ServiceError):
    default_code = "EVENT_ERROR"
    default_status = status.HTTP_400_BAD_REQUEST


class EventNotFoundError(EventServiceError):
    default_code = "EVENT_NOT_FOUND"
    default_status = status.HTTP_404_NOT_FOUND




class BookingServiceError(ServiceError):
    default_code = "BOOKING_ERROR"
    default_status = status.HTTP_400_BAD_REQUEST


class BookingNotFoundError(BookingServiceError):
    default_code = "BOOKING_NOT_FOUND"
    default_status = status.HTTP_404_NOT_FOUND


class BookingAccessDeniedError(BookingServiceError):
    default_code = "BOOKING_ACCESS_DENIED"
    default_status = status.HTTP_403_FORBIDDEN



# ======================================================================
# CENTRAL DRF EXCEPTION HANDLER
# ======================================================================


def custom_exception_handler(exc, context):
    """
    Centralized exception handler for all DRF APIs.

    Handles:

        1. Custom service exceptions.
        2. Standard DRF exceptions.
        3. Unexpected exceptions.

    API error response format:

        {
            "success": false,
            "error": {
                "code": "...",
                "message": "...",
                "details": ...
            }
        }
    """

    # ------------------------------------------------------------------
    # CUSTOM SERVICE ERROR
    # ------------------------------------------------------------------

    if isinstance(exc, ServiceError):
        return Response(
            {
                "success": False,
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                },
            },
            status=exc.status_code,
        )

    # ------------------------------------------------------------------
    # STANDARD DRF ERROR
    # ------------------------------------------------------------------

    response = exception_handler(
        exc,
        context,
    )

    if response is not None:

        details = response.data

        if isinstance(details, dict):
            if "detail" in details:
                message = str(details["detail"])
            else:
                message = "Request validation failed."

        else:
            message = str(details)

        default_code = getattr(
            exc,
            "default_code",
            "api_error",
        )

        return Response(
            {
                "success": False,
                "error": {
                    "code": default_code.upper(),
                    "message": message,
                    "details": details,
                },
            },
            status=response.status_code,
            headers=response.headers,
        )

    # ------------------------------------------------------------------
    # UNEXPECTED ERROR
    # ------------------------------------------------------------------

    return Response(
        {
            "success": False,
            "error": {
                "code": "SERVER_ERROR",
                "message": "An unexpected error occurred.",
            },
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )