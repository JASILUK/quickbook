from decimal import Decimal
from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.events.models import Event
from apps.events.repositories import EventRepository, VendorRepository
from config.exceptions import (
    EventNotFoundError,
    EventServiceError,
    PermissionServiceError,
    VendorNotFoundError,
)


class EventService:
    """
    Business logic related to Events.

    Responsibilities:
        - Event validation
        - Customer event browsing
        - Staff event management
        - Capacity management
        - Event activation/deactivation

    Database queries belong in repositories.
    HTTP concerns belong in views.
    """

    # ============================================================
    # INTERNAL VALIDATION HELPERS
    # ============================================================

    @staticmethod
    def _validate_staff_user(user: User) -> None:
        """
        Ensure the current user is an active staff member.
        """

        if not (
            user
            and user.is_authenticated
            and user.is_active
            and user.role == User.Role.STAFF
        ):
            raise PermissionServiceError(
                message="Staff access is required.",
            )

    @staticmethod
    def _get_event(event_id: int) -> Event:
        """
        Return an event or raise a service-level 404 error.
        """

        event = EventRepository.get_by_id(event_id)

        if event is None:
            raise EventNotFoundError(
                message="Event not found.",
            )

        return event

    @staticmethod
    def _get_event_for_update(event_id: int) -> Event:
        """
        Return an event using the locking repository method.

        Must be called inside transaction.atomic().
        """

        event = EventRepository.get_for_update(event_id)

        if event is None:
            raise EventNotFoundError(
                message="Event not found.",
            )

        return event

    @staticmethod
    def _get_vendor(vendor_id: int):
        """
        Return vendor or raise a service-level 404 error.
        """

        vendor = VendorRepository.get_by_id(vendor_id)

        if vendor is None:
            raise VendorNotFoundError(
                message="Vendor not found.",
            )

        return vendor

    @staticmethod
    def _validate_vendor_for_event(vendor_id: int) -> None:
        """
        Events can only belong to active vendors.
        """

        vendor = EventService._get_vendor(vendor_id)

        if not vendor.is_active:
            raise EventServiceError(
                message="Cannot create or assign an event to an inactive vendor.",
                code="INACTIVE_VENDOR",
            )

    @staticmethod
    def _validate_title(title: str) -> str:
        """
        Validate and normalize event title.
        """

        title = title.strip()

        if not title:
            raise EventServiceError(
                message="Event title cannot be empty.",
                code="INVALID_TITLE",
            )

        return title

    @staticmethod
    def _validate_venue_name(venue_name: str) -> str:
        """
        Validate and normalize venue name.
        """

        venue_name = venue_name.strip()

        if not venue_name:
            raise EventServiceError(
                message="Venue name cannot be empty.",
                code="INVALID_VENUE_NAME",
            )

        return venue_name

    @staticmethod
    def _validate_address(address: str) -> str:
        """
        Validate and normalize event address.
        """

        address = address.strip()

        if not address:
            raise EventServiceError(
                message="Event address cannot be empty.",
                code="INVALID_ADDRESS",
            )

        return address

    @staticmethod
    def _validate_datetime_range(
        start_datetime,
        end_datetime,
    ) -> None:
        """
        Validate event start/end datetime.
        """

        if start_datetime is None or end_datetime is None:
            raise EventServiceError(
                message="Start and end datetime are required.",
                code="INVALID_DATETIME",
            )

        if end_datetime <= start_datetime:
            raise EventServiceError(
                message="Event end time must be after start time.",
                code="INVALID_DATETIME_RANGE",
            )

    @staticmethod
    def _validate_coordinates(
        latitude,
        longitude,
    ) -> None:
        """
        Validate latitude and longitude.

        Coordinates are optional, but if one is provided,
        the other must also be provided.
        """

        if (latitude is None) != (longitude is None):
            raise EventServiceError(
                message="Latitude and longitude must be provided together.",
                code="INVALID_COORDINATES",
            )

        if latitude is None and longitude is None:
            return

        if not (-90 <= latitude <= 90):
            raise EventServiceError(
                message="Latitude must be between -90 and 90.",
                code="INVALID_LATITUDE",
            )

        if not (-180 <= longitude <= 180):
            raise EventServiceError(
                message="Longitude must be between -180 and 180.",
                code="INVALID_LONGITUDE",
            )

    @staticmethod
    def _validate_seats(total_seats: int) -> None:
        """
        Validate event capacity.
        """

        if total_seats <= 0:
            raise EventServiceError(
                message="Total seats must be greater than zero.",
                code="INVALID_TOTAL_SEATS",
            )

    @staticmethod
    def _validate_price(ticket_price: Decimal) -> None:
        """
        Validate ticket price.
        """

        if ticket_price < 0:
            raise EventServiceError(
                message="Ticket price cannot be negative.",
                code="INVALID_TICKET_PRICE",
            )

    # ============================================================
    # CUSTOMER EVENT LISTING
    # ============================================================

    @staticmethod
    def list_customer_events(
        *,
        search: str | None = None,
        vendor_id: int | None = None,
        start_datetime=None,
        end_datetime=None,
        min_price=None,
        max_price=None,
    ):
        """
        Return events available for customer browsing.

        Customers see only:
            - active events
            - active vendors
            - upcoming events

        Optional filters:
            - search
            - vendor
            - date range
            - price range
        """

        queryset = EventRepository.get_upcoming()

        if search:
            queryset = EventRepository.search(
                queryset=queryset,
                search=search.strip(),
            )

        if vendor_id is not None:
            queryset = EventRepository.filter_by_vendor(
                queryset=queryset,
                vendor_id=vendor_id,
            )

        queryset = EventRepository.filter_by_date_range(
            queryset=queryset,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
        )

        queryset = EventRepository.filter_by_price_range(
            queryset=queryset,
            min_price=min_price,
            max_price=max_price,
        )

        return queryset

    # ============================================================
    # STAFF EVENT LISTING
    # ============================================================

    @staticmethod
    def list_staff_events(
        *,
        staff_user: User,
        search: str | None = None,
        vendor_id: int | None = None,
        start_datetime=None,
        end_datetime=None,
        min_price=None,
        max_price=None,
    ):
        """
        Return all events for staff management.

        Staff can see:
            - active events
            - inactive events
            - upcoming events
            - past events
        """

        EventService._validate_staff_user(staff_user)

        queryset = EventRepository.get_all()

        if search:
            queryset = EventRepository.search(
                queryset=queryset,
                search=search.strip(),
            )

        if vendor_id is not None:
            queryset = EventRepository.filter_by_vendor(
                queryset=queryset,
                vendor_id=vendor_id,
            )

        queryset = EventRepository.filter_by_date_range(
            queryset=queryset,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
        )

        queryset = EventRepository.filter_by_price_range(
            queryset=queryset,
            min_price=min_price,
            max_price=max_price,
        )

        return queryset

    # ============================================================
    # GET EVENT DETAIL
    # ============================================================

    @staticmethod
    def get_event(
        *,
        event_id: int,
        staff_user: User | None = None,
    ) -> Event:
        """
        Return an event.

        If staff_user is provided, staff can access any event.

        Otherwise this method returns only an event that is
        currently visible to customers.
        """

        event = EventService._get_event(event_id)

        if staff_user is not None:
            EventService._validate_staff_user(staff_user)
            return event

        if not event.is_active:
            raise EventNotFoundError(
                message="Event not found.",
            )

        if not event.vendor.is_active:
            raise EventNotFoundError(
                message="Event not found.",
            )

        if event.start_datetime < timezone.now():
            raise EventNotFoundError(
                message="Event not found.",
            )

        return event

    # ============================================================
    # CREATE EVENT
    # ============================================================

    @staticmethod
    def create_event(
        *,
        staff_user: User,
        vendor_id: int,
        title: str,
        description: str = "",
        venue_name: str,
        address: str,
        latitude=None,
        longitude=None,
        start_datetime,
        end_datetime,
        total_seats: int,
        ticket_price,
    ) -> Event:
        """
        Create an event.

        Only active staff can create events.

        available_seats is initialized to total_seats.
        """

        EventService._validate_staff_user(staff_user)

        EventService._validate_vendor_for_event(vendor_id)

        title = EventService._validate_title(title)
        venue_name = EventService._validate_venue_name(venue_name)
        address = EventService._validate_address(address)

        EventService._validate_datetime_range(
            start_datetime,
            end_datetime,
        )

        EventService._validate_seats(total_seats)

        EventService._validate_price(ticket_price)

        EventService._validate_coordinates(
            latitude,
            longitude,
        )

        return EventRepository.create(
            vendor_id=vendor_id,
            title=title,
            description=description.strip(),
            venue_name=venue_name,
            address=address,
            latitude=latitude,
            longitude=longitude,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            total_seats=total_seats,
            available_seats=total_seats,
            ticket_price=ticket_price,
            created_by_id=staff_user.id,
        )

    # ============================================================
    # UPDATE EVENT
    # ============================================================

    @staticmethod
    @transaction.atomic
    def update_event(
        *,
        staff_user: User,
        event_id: int,
        vendor_id: int | None = None,
        title: str | None = None,
        description: str | None = None,
        venue_name: str | None = None,
        address: str | None = None,
        latitude=None,
        longitude=None,
        start_datetime=None,
        end_datetime=None,
        total_seats: int | None = None,
        ticket_price=None,
    ) -> Event:
        """
        Update an event.

        Capacity changes are handled carefully so already-booked
        seats are never lost.

        Example:

            total_seats = 100
            available_seats = 20

            booked = 80

            new total = 120

            new available = 120 - 80 = 40
        """

        EventService._validate_staff_user(staff_user)

        event = EventService._get_event_for_update(event_id)

        # --------------------------------------------------------
        # Validate vendor
        # --------------------------------------------------------

        if vendor_id is not None:
            EventService._validate_vendor_for_event(vendor_id)

        # --------------------------------------------------------
        # Determine final values
        # --------------------------------------------------------

        final_title = (
            EventService._validate_title(title)
            if title is not None
            else event.title
        )

        final_venue_name = (
            EventService._validate_venue_name(venue_name)
            if venue_name is not None
            else event.venue_name
        )

        final_address = (
            EventService._validate_address(address)
            if address is not None
            else event.address
        )

        final_start_datetime = (
            start_datetime
            if start_datetime is not None
            else event.start_datetime
        )

        final_end_datetime = (
            end_datetime
            if end_datetime is not None
            else event.end_datetime
        )

        EventService._validate_datetime_range(
            final_start_datetime,
            final_end_datetime,
        )

        final_latitude = (
            latitude
            if latitude is not None
            else event.latitude
        )

        final_longitude = (
            longitude
            if longitude is not None
            else event.longitude
        )

        EventService._validate_coordinates(
            final_latitude,
            final_longitude,
        )

        final_ticket_price = (
            ticket_price
            if ticket_price is not None
            else event.ticket_price
        )

        EventService._validate_price(
            final_ticket_price,
        )

        # --------------------------------------------------------
        # Capacity calculation
        # --------------------------------------------------------

        new_available_seats = None

        if total_seats is not None:

            EventService._validate_seats(total_seats)

            booked_seats = (
                event.total_seats
                - event.available_seats
            )

            if total_seats < booked_seats:
                raise EventServiceError(
                    message=(
                        f"Total seats cannot be reduced below "
                        f"the number of already booked seats ({booked_seats})."
                    ),
                    code="CAPACITY_BELOW_BOOKED_SEATS",
                    status_code=409,
                )

            new_available_seats = (
                total_seats
                - booked_seats
            )

        # --------------------------------------------------------
        # Update
        # --------------------------------------------------------

        return EventRepository.update(
            event,
            vendor_id=vendor_id,
            title=final_title,
            description=(
                description.strip()
                if description is not None
                else None
            ),
            venue_name=final_venue_name,
            address=final_address,
            latitude=latitude,
            longitude=longitude,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            total_seats=total_seats,
            available_seats=new_available_seats,
            ticket_price=ticket_price,
        )

    # ============================================================
    # ACTIVATE EVENT
    # ============================================================

    @staticmethod
    def activate_event(
        *,
        staff_user: User,
        event_id: int,
    ) -> Event:
        """
        Activate an event.

        An event cannot be activated if its vendor is inactive.
        """

        EventService._validate_staff_user(staff_user)

        event = EventService._get_event(event_id)

        if not event.vendor.is_active:
            raise EventServiceError(
                message="Cannot activate an event belonging to an inactive vendor.",
                code="INACTIVE_VENDOR",
            )

        if event.is_active:
            raise EventServiceError(
                message="Event is already active.",
                code="EVENT_ALREADY_ACTIVE",
                status_code=409,
            )

        return EventRepository.set_active(
            event,
            is_active=True,
        )

    # ============================================================
    # DEACTIVATE EVENT
    # ============================================================

    @staticmethod
    def deactivate_event(
        *,
        staff_user: User,
        event_id: int,
    ) -> Event:
        """
        Deactivate an event.

        Existing bookings are not deleted or modified here.
        """

        EventService._validate_staff_user(staff_user)

        event = EventService._get_event(event_id)

        if not event.is_active:
            raise EventServiceError(
                message="Event is already inactive.",
                code="EVENT_ALREADY_INACTIVE",
                status_code=409,
            )

        return EventRepository.set_active(
            event,
            is_active=False,
        )