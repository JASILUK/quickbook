from django.db.models import Q, QuerySet
from django.utils import timezone

from apps.bookings.models import Booking


class BookingRepository:
    """
    Database operations related to Booking.

    Business rules belong in BookingService.

    Responsibilities:
        - Query bookings
        - Filter bookings
        - Create bookings
        - Lock booking rows when they will be modified
        - Update booking status
    """

    # ============================================================
    # NORMAL READS
    # ============================================================

    @staticmethod
    def get_by_id(
        booking_id: int,
    ) -> Booking | None:
        """
        Return a booking by ID.

        Related user, event, and vendor are loaded using JOINs
        to avoid N+1 queries.
        """

        return (
            Booking.objects
            .select_related(
                "user",
                "event",
                "event__vendor",
            )
            .filter(
                id=booking_id,
            )
            .first()
        )

    @staticmethod
    def get_all() -> QuerySet[Booking]:
        """
        Return all bookings.

        Includes:
            - confirmed bookings
            - cancelled bookings
            - upcoming event bookings
            - past event bookings

        Mainly intended for staff management.
        """

        return (
            Booking.objects
            .select_related(
                "user",
                "event",
                "event__vendor",
            )
            .order_by(
                "-booked_at",
            )
        )

    @staticmethod
    def get_for_update(
        booking_id: int,
    ) -> Booking | None:
        """
        Return a booking using a locking query.

        Must be called inside transaction.atomic().

        Used when modifying booking state, for example:
            - cancelling a booking
        """

        return (
            Booking.objects
            .select_for_update()
            .select_related(
                "user",
                "event",
                "event__vendor",
            )
            .filter(
                id=booking_id,
            )
            .first()
        )

    # ============================================================
    # CUSTOMER BOOKINGS
    # ============================================================

    @staticmethod
    def get_user_bookings(
        user_id: int,
    ) -> QuerySet[Booking]:
        """
        Return all bookings belonging to one customer.

        Includes:
            - confirmed bookings
            - cancelled bookings
            - past bookings
            - upcoming bookings
        """

        return (
            Booking.objects
            .select_related(
                "user",
                "event",
                "event__vendor",
            )
            .filter(
                user_id=user_id,
            )
            .order_by(
                "-booked_at",
            )
        )

    @staticmethod
    def get_upcoming_user_bookings(
        user_id: int,
    ) -> QuerySet[Booking]:
        """
        Return confirmed bookings for events that have not started yet.
        """

        return (
            Booking.objects
            .select_related(
                "user",
                "event",
                "event__vendor",
            )
            .filter(
                user_id=user_id,
                status=Booking.Status.CONFIRMED,
                event__start_datetime__gte=timezone.now(),
            )
            .order_by(
                "event__start_datetime",
            )
        )

    # ============================================================
    # EVENT BOOKINGS
    # ============================================================

    @staticmethod
    def get_event_bookings(
        event_id: int,
    ) -> QuerySet[Booking]:
        """
        Return all bookings for a specific event.

        Includes:
            - confirmed bookings
            - cancelled bookings
        """

        return (
            Booking.objects
            .select_related(
                "user",
                "event",
                "event__vendor",
            )
            .filter(
                event_id=event_id,
            )
            .order_by(
                "-booked_at",
            )
        )

    @staticmethod
    def get_confirmed_event_bookings(
        event_id: int,
    ) -> QuerySet[Booking]:
        """
        Return only confirmed bookings for an event.
        """

        return (
            Booking.objects
            .select_related(
                "user",
                "event",
                "event__vendor",
            )
            .filter(
                event_id=event_id,
                status=Booking.Status.CONFIRMED,
            )
            .order_by(
                "-booked_at",
            )
        )

    # ============================================================
    # FILTERING
    # ============================================================

    @staticmethod
    def filter_by_user(
        *,
        queryset: QuerySet[Booking],
        user_id: int,
    ) -> QuerySet[Booking]:
        """
        Filter bookings by customer/user.
        """

        return queryset.filter(
            user_id=user_id,
        )

    @staticmethod
    def filter_by_event(
        *,
        queryset: QuerySet[Booking],
        event_id: int,
    ) -> QuerySet[Booking]:
        """
        Filter bookings by event.
        """

        return queryset.filter(
            event_id=event_id,
        )

    @staticmethod
    def filter_by_status(
        *,
        queryset: QuerySet[Booking],
        booking_status: str,
    ) -> QuerySet[Booking]:
        """
        Filter bookings by status.
        """

        return queryset.filter(
            status=booking_status,
        )

    @staticmethod
    def filter_by_event_date_range(
        *,
        queryset: QuerySet[Booking],
        start_datetime=None,
        end_datetime=None,
    ) -> QuerySet[Booking]:
        """
        Filter bookings based on the event's datetime.
        """

        if start_datetime is not None:
            queryset = queryset.filter(
                event__start_datetime__gte=start_datetime,
            )

        if end_datetime is not None:
            queryset = queryset.filter(
                event__start_datetime__lte=end_datetime,
            )

        return queryset

    @staticmethod
    def search(
        *,
        queryset: QuerySet[Booking],
        search: str,
    ) -> QuerySet[Booking]:
        """
        Search bookings by customer or event information.

        Searches:
            - customer email
            - customer first name
            - customer last name
            - event title
            - venue name
        """

        return queryset.filter(
            Q(user__email__icontains=search)
            | Q(user__first_name__icontains=search)
            | Q(user__last_name__icontains=search)
            | Q(event__title__icontains=search)
            | Q(event__venue_name__icontains=search)
        )

    # ============================================================
    # CREATE
    # ============================================================

    @staticmethod
    def create(
        *,
        user_id: int,
        event_id: int,
        quantity: int,
        total_amount,
    ) -> Booking:
        """
        Create a confirmed booking.

        Seat availability must already have been validated and
        updated transactionally by BookingService before calling
        this method.
        """

        return Booking.objects.create(
            user_id=user_id,
            event_id=event_id,
            quantity=quantity,
            total_amount=total_amount,
            status=Booking.Status.CONFIRMED,
        )

    # ============================================================
    # CANCEL
    # ============================================================

    @staticmethod
    def cancel(
        booking: Booking,
        *,
        cancelled_at=None,
    ) -> Booking:
        """
        Mark a booking as cancelled.

        Business rules determining whether cancellation is allowed
        belong in BookingService.
        """

        if cancelled_at is None:
            cancelled_at = timezone.now()

        booking.status = Booking.Status.CANCELLED
        booking.cancelled_at = cancelled_at

        booking.save(
            update_fields=[
                "status",
                "cancelled_at",
                "updated_at",
            ],
        )

        return booking

    # ============================================================
    # COUNTS
    # ============================================================

    @staticmethod
    def count() -> int:
        """
        Return total booking count.
        """

        return Booking.objects.count()

    @staticmethod
    def count_confirmed() -> int:
        """
        Return total confirmed booking count.
        """

        return Booking.objects.filter(
            status=Booking.Status.CONFIRMED,
        ).count()

    @staticmethod
    def count_for_event(
        event_id: int,
    ) -> int:
        """
        Return number of confirmed bookings for an event.
        """

        return Booking.objects.filter(
            event_id=event_id,
            status=Booking.Status.CONFIRMED,
        ).count()

    @staticmethod
    def count_tickets_for_event(
        event_id: int,
    ) -> int:
        """
        Return total number of confirmed tickets booked
        for an event.
        """

        from django.db.models import Sum

        result = (
            Booking.objects
            .filter(
                event_id=event_id,
                status=Booking.Status.CONFIRMED,
            )
            .aggregate(
                total=Sum("quantity"),
            )
        )

        return result["total"] or 0

    @staticmethod
    def get_recent(limit: int = 10) -> QuerySet[Booking]:
        return (
            Booking.objects
            .select_related(
                "user",
                "event",
                "event__vendor",
            )
            .order_by("-booked_at")[:limit]
        )