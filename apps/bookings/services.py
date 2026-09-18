
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.bookings.models import Booking
from apps.bookings.repositories import BookingRepository
from apps.events.repositories import EventRepository
from config.exceptions import (
    BookingServiceError,
)


class BookingService:

    CANCELLATION_DEADLINE_HOURS = 2

    # =========================================================
    # Internal helpers
    # =========================================================

    @staticmethod
    def _get_event_for_update(event_id: int):
        event = EventRepository.get_for_update(event_id)

        if event is None:
            raise BookingServiceError(
                "Event not found.",
                code="EVENT_NOT_FOUND",
                status_code=404,
            )

        return event

    @staticmethod
    def _get_booking_for_update(booking_id: int):
        booking = BookingRepository.get_for_update(booking_id)

        if booking is None:
            raise BookingServiceError(
                "Booking not found.",
                code="BOOKING_NOT_FOUND",
                status_code=404,
            )

        return booking

    @staticmethod
    def _validate_customer(user: User):
        if not user.is_authenticated:
            raise BookingServiceError(
                "Authentication is required.",
                code="AUTHENTICATION_REQUIRED",
                status_code=401,
            )

        if not user.is_active:
            raise BookingServiceError(
                "Your account is inactive.",
                code="ACCOUNT_INACTIVE",
                status_code=403,
            )

        if user.role != User.Role.CUSTOMER:
            raise BookingServiceError(
                "Only customers can create bookings.",
                code="CUSTOMER_REQUIRED",
                status_code=403,
            )

    @staticmethod
    def _validate_quantity(quantity: int):
        if quantity <= 0:
            raise BookingServiceError(
                "Quantity must be greater than zero.",
                code="INVALID_QUANTITY",
                status_code=400,
            )

    @staticmethod
    def _validate_event_for_booking(event):
        if not event.is_active:
            raise BookingServiceError(
                "This event is not available for booking.",
                code="EVENT_INACTIVE",
                status_code=400,
            )

        if not event.vendor.is_active:
            raise BookingServiceError(
                "This event's vendor is inactive.",
                code="VENDOR_INACTIVE",
                status_code=400,
            )

        if event.start_datetime <= timezone.now():
            raise BookingServiceError(
                "This event has already started or is no longer bookable.",
                code="EVENT_NOT_BOOKABLE",
                status_code=400,
            )

    @staticmethod
    def _validate_cancellation_deadline(booking):
        cancellation_deadline = (
            booking.event.start_datetime
            - timezone.timedelta(
                hours=BookingService.CANCELLATION_DEADLINE_HOURS
            )
        )

        if timezone.now() >= cancellation_deadline:
            raise BookingServiceError(
                "Bookings cannot be cancelled within 2 hours of the event.",
                code="CANCELLATION_DEADLINE_PASSED",
                status_code=400,
            )

    # =========================================================
    # Create booking
    # =========================================================

    @staticmethod
    @transaction.atomic
    def create_booking(
        *,
        user: User,
        event_id: int,
        quantity: int,
    ) -> Booking:

        # 1. Validate customer
        BookingService._validate_customer(user)

        # 2. Validate quantity
        BookingService._validate_quantity(quantity)

        # 3. Lock event
        #
        # IMPORTANT:
        # The availability check happens AFTER the lock.
        #
        # This prevents two concurrent requests from both
        # reading the same available_seats value.
        event = BookingService._get_event_for_update(event_id)

        # 4. Validate event
        BookingService._validate_event_for_booking(event)

        # 5. Check seat availability
        if event.available_seats < quantity:
            raise BookingServiceError(
                f"Only {event.available_seats} seat(s) are available.",
                code="INSUFFICIENT_SEATS",
                status_code=409,
            )

        # 6. Calculate total amount
        total_amount = event.ticket_price * quantity

        # 7. Reduce available seats
        event.available_seats -= quantity

        event.save(
            update_fields=["available_seats"]
        )

        # 8. Create booking
        booking = BookingRepository.create(
            user_id=user.id,
            event_id=event.id,
            quantity=quantity,
            total_amount=total_amount,
        )

        return booking

    # =========================================================
    # Get booking
    # =========================================================

    @staticmethod
    def get_booking(
        *,
        booking_id: int,
        user: User,
    ) -> Booking:

        booking = BookingRepository.get_by_id(booking_id)

        if booking is None:
            raise BookingServiceError(
                "Booking not found.",
                code="BOOKING_NOT_FOUND",
                status_code=404,
            )

        # Customers can only see their own bookings.
        if user.role == User.Role.CUSTOMER:
            if booking.user_id != user.id:
                raise BookingServiceError(
                    "You do not have access to this booking.",
                    code="BOOKING_ACCESS_DENIED",
                    status_code=403,
                )

        # Staff can view all bookings.
        elif user.role != User.Role.STAFF:
            raise BookingServiceError(
                "You do not have permission to view bookings.",
                code="BOOKING_ACCESS_DENIED",
                status_code=403,
            )

        return booking

    # =========================================================
    # List bookings
    # =========================================================

    @staticmethod
    def list_bookings(
        *,
        user: User,
        user_id: int | None = None,
        event_id: int | None = None,
        booking_status: str | None = None,
        start_datetime=None,
        end_datetime=None,
        search: str | None = None,
    ):
        """
        Customers:
            Can only see their own bookings.

        Staff:
            Can see all bookings and use filters.
        """

        if user.role == User.Role.CUSTOMER:

            queryset = BookingRepository.get_user_bookings(
                user.id
            )

        elif user.role == User.Role.STAFF:

            queryset = BookingRepository.get_all()

            if user_id is not None:
                queryset = BookingRepository.filter_by_user(
                    queryset=queryset,
                    user_id=user_id,
                )

        else:
            raise BookingServiceError(
                "You do not have permission to view bookings.",
                code="BOOKING_ACCESS_DENIED",
                status_code=403,
            )

        # Common filters
        if event_id is not None:
            queryset = BookingRepository.filter_by_event(
                queryset=queryset,
                event_id=event_id,
            )

        if booking_status is not None:
            queryset = BookingRepository.filter_by_status(
                queryset=queryset,
                booking_status=booking_status,
            )

        if start_datetime is not None or end_datetime is not None:
            queryset = BookingRepository.filter_by_event_date_range(
                queryset=queryset,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
            )

        if search:
            queryset = BookingRepository.search(
                queryset=queryset,
                search=search,
            )

        return queryset

    # =========================================================
    # Cancel booking
    # =========================================================

    @staticmethod
    @transaction.atomic
    def cancel_booking(
        *,
        booking_id: int,
        user: User,
    ) -> Booking:

        # 1. Lock booking
        booking = BookingService._get_booking_for_update(
            booking_id
        )

        # 2. Permission check
        is_customer_owner = (
            user.role == User.Role.CUSTOMER
            and booking.user_id == user.id
        )

        is_staff = user.role == User.Role.STAFF

        if not is_customer_owner and not is_staff:
            raise BookingServiceError(
                "You do not have permission to cancel this booking.",
                code="BOOKING_CANCEL_ACCESS_DENIED",
                status_code=403,
            )

        # 3. Booking must still be confirmed
        if booking.status != Booking.Status.CONFIRMED:
            raise BookingServiceError(
                "Only confirmed bookings can be cancelled.",
                code="BOOKING_ALREADY_CANCELLED",
                status_code=400,
            )

        # 4. Check cancellation deadline
        BookingService._validate_cancellation_deadline(
            booking
        )

        # 5. Lock the event
        #
        # We lock the Event before restoring seats so that
        # booking and cancellation cannot modify availability
        # at the same time.
        event = BookingService._get_event_for_update(
            booking.event_id
        )

        # 6. Restore seats
        event.available_seats += booking.quantity

        # Safety check: never allow availability above capacity.
        if event.available_seats > event.total_seats:
            raise BookingServiceError(
                "Event seat availability is inconsistent.",
                code="SEAT_AVAILABILITY_ERROR",
                status_code=409,
            )

        event.save(
            update_fields=["available_seats"]
        )

        # 7. Mark booking as cancelled
        booking = BookingRepository.cancel(
            booking=booking,
            cancelled_at=timezone.now(),
        )

        return booking

    # =========================================================
    # Booking history
    # =========================================================

    @staticmethod
    def get_booking_history(*, user: User):
        """
        Returns all bookings belonging to the customer,
        including confirmed and cancelled bookings.
        """

        BookingService._validate_customer(user)

        return BookingRepository.get_user_bookings(
            user.id
        )

    # =========================================================
    # Upcoming bookings
    # =========================================================

    @staticmethod
    def get_upcoming_bookings(*, user: User):
        """
        Returns confirmed bookings for future events.
        """

        BookingService._validate_customer(user)

        return BookingRepository.get_upcoming_user_bookings(
            user.id
        )
