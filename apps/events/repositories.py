
from django.db.models import QuerySet, Q

from .models import Event, Vendor

from django.utils import timezone


class VendorRepository:
    """
    Database operations related to Vendor.

    Business rules belong in the service layer.
    """

    @staticmethod
    def get_by_id(vendor_id: int) -> Vendor | None:
        """
        Return a vendor by ID.
        """
        return (
            Vendor.objects
            .select_related("created_by")
            .filter(id=vendor_id)
            .first()
        )

    @staticmethod
    def get_all() -> QuerySet[Vendor]:
        """
        Return all vendors with the creator loaded.

        select_related("created_by") prevents an N+1 query
        when the creator information is accessed.
        """
        return (
            Vendor.objects
            .select_related("created_by")
            .order_by("-created_at")
        )

    @staticmethod
    def get_active() -> QuerySet[Vendor]:
        """
        Return active vendors.
        """
        return (
            Vendor.objects
            .select_related("created_by")
            .filter(is_active=True)
            .order_by("name")
        )

    @staticmethod
    def search(
        *,
        queryset: QuerySet[Vendor],
        search: str,
    ) -> QuerySet[Vendor]:
        """
        Search vendors by name, email, phone, or address.
        """
        return queryset.filter(
            Q(name__icontains=search)
            | Q(email__icontains=search)
            | Q(phone__icontains=search)
            | Q(address__icontains=search)
        )

    @staticmethod
    def create(
        *,
        name: str,
        email: str = "",
        phone: str = "",
        address: str = "",
        description: str = "",
        created_by_id: int,
    ) -> Vendor:
        """
        Create a vendor.
        """
        return Vendor.objects.create(
            name=name,
            email=email,
            phone=phone,
            address=address,
            description=description,
            created_by_id=created_by_id,
        )

    @staticmethod
    def update(
        vendor: Vendor,
        *,
        name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        address: str | None = None,
        description: str | None = None,
    ) -> Vendor:
        """
        Update vendor fields that were provided.
        """

        update_fields = []

        if name is not None:
            vendor.name = name
            update_fields.append("name")

        if email is not None:
            vendor.email = email
            update_fields.append("email")

        if phone is not None:
            vendor.phone = phone
            update_fields.append("phone")

        if address is not None:
            vendor.address = address
            update_fields.append("address")

        if description is not None:
            vendor.description = description
            update_fields.append("description")

        if update_fields:
            vendor.save(
                update_fields=update_fields
            )

        return vendor

    @staticmethod
    def set_active(
        vendor: Vendor,
        *,
        is_active: bool,
    ) -> Vendor:
        """
        Activate or deactivate a vendor.
        """
        vendor.is_active = is_active

        vendor.save(
            update_fields=["is_active"]
        )

        return vendor

    @staticmethod
    def count() -> int:
        """
        Return total vendor count.
        """
        return Vendor.objects.count()

    @staticmethod
    def count_active() -> int:
        """
        Return active vendor count.
        """
        return Vendor.objects.filter(
            is_active=True
        ).count()



class EventRepository:
    """
    Database operations related to Event.

    Business rules belong in the service layer.
    """

    @staticmethod
    def get_by_id(
        event_id: int,
    ) -> Event | None:
        """
        Return an event by ID.

        Used for normal read operations.

        vendor and created_by are loaded using JOINs
        to avoid N+1 queries.
        """
        return (
            Event.objects
            .select_related(
                "vendor",
                "created_by",
            )
            .filter(id=event_id)
            .first()
        )

    @staticmethod
    def get_for_update(
        event_id: int,
    ) -> Event | None:
        """
        Return an event for an operation that will modify
        its state.

        Intended for use inside transaction.atomic().

        Used for:
            - changing event capacity
            - booking tickets
            - cancelling tickets

        select_for_update() provides row-level locking on
        databases that support it. SQLite does not provide
        true row-level SELECT FOR UPDATE locking, but keeping
        this repository method makes the service layer
        database-portable.
        """
        return (
            Event.objects
            .select_for_update()
            .select_related(
                "vendor",
                "created_by",
            )
            .filter(id=event_id)
            .first()
        )

    @staticmethod
    def get_all() -> QuerySet[Event]:
        """
        Return all events.

        Intended mainly for staff management.

        Includes:
            - active events
            - inactive events
            - upcoming events
            - past events
        """
        return (
            Event.objects
            .select_related(
                "vendor",
                "created_by",
            )
            .order_by("start_datetime")
        )

    @staticmethod
    def get_upcoming() -> QuerySet[Event]:
        """
        Return events available for customer browsing.

        Only:
            - active events
            - active vendors
            - upcoming events

        Past events are excluded by default.
        """
        return (
            Event.objects
            .select_related(
                "vendor",
                "created_by",
            )
            .filter(
                is_active=True,
                vendor__is_active=True,
                start_datetime__gte=timezone.now(),
            )
            .order_by("start_datetime")
        )

    @staticmethod
    def search(
        *,
        queryset: QuerySet[Event],
        search: str,
    ) -> QuerySet[Event]:
        """
        Search events by:
            - title
            - description
            - venue
            - address
            - vendor name
        """
        return queryset.filter(
            Q(title__icontains=search)
            | Q(description__icontains=search)
            | Q(venue_name__icontains=search)
            | Q(address__icontains=search)
            | Q(vendor__name__icontains=search)
        )

    @staticmethod
    def filter_by_vendor(
        *,
        queryset: QuerySet[Event],
        vendor_id: int,
    ) -> QuerySet[Event]:
        """
        Filter events belonging to a specific vendor.
        """
        return queryset.filter(
            vendor_id=vendor_id,
        )

    @staticmethod
    def filter_by_date_range(
        *,
        queryset: QuerySet[Event],
        start_datetime=None,
        end_datetime=None,
    ) -> QuerySet[Event]:
        """
        Filter events by their start/end datetime.

        If start_datetime is provided:
            event start must be >= start_datetime.

        If end_datetime is provided:
            event end must be <= end_datetime.
        """
        if start_datetime is not None:
            queryset = queryset.filter(
                start_datetime__gte=start_datetime,
            )

        if end_datetime is not None:
            queryset = queryset.filter(
                end_datetime__lte=end_datetime,
            )

        return queryset

    @staticmethod
    def filter_by_price_range(
        *,
        queryset: QuerySet[Event],
        min_price=None,
        max_price=None,
    ) -> QuerySet[Event]:
        """
        Filter events by ticket price.
        """
        if min_price is not None:
            queryset = queryset.filter(
                ticket_price__gte=min_price,
            )

        if max_price is not None:
            queryset = queryset.filter(
                ticket_price__lte=max_price,
            )

        return queryset

    @staticmethod
    def create(
        *,
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
        available_seats: int,
        ticket_price,
        created_by_id: int,
    ) -> Event:
        """
        Create an event.
        """
        return Event.objects.create(
            vendor_id=vendor_id,
            title=title,
            description=description,
            venue_name=venue_name,
            address=address,
            latitude=latitude,
            longitude=longitude,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            total_seats=total_seats,
            available_seats=available_seats,
            ticket_price=ticket_price,
            created_by_id=created_by_id,
        )

    @staticmethod
    def update(
        event: Event,
        *,
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
        available_seats: int | None = None,
        ticket_price=None,
    ) -> Event:
        """
        Update event configuration.

        Seat availability is calculated by EventService when
        event capacity changes and persisted here.

        BookingService remains responsible for transactional
        availability changes caused by bookings/cancellations.
        """
        update_fields = []

        if vendor_id is not None:
            event.vendor_id = vendor_id
            update_fields.append("vendor")

        if title is not None:
            event.title = title
            update_fields.append("title")

        if description is not None:
            event.description = description
            update_fields.append("description")

        if venue_name is not None:
            event.venue_name = venue_name
            update_fields.append("venue_name")

        if address is not None:
            event.address = address
            update_fields.append("address")

        if latitude is not None:
            event.latitude = latitude
            update_fields.append("latitude")

        if longitude is not None:
            event.longitude = longitude
            update_fields.append("longitude")

        if start_datetime is not None:
            event.start_datetime = start_datetime
            update_fields.append("start_datetime")

        if end_datetime is not None:
            event.end_datetime = end_datetime
            update_fields.append("end_datetime")

        if total_seats is not None:
            event.total_seats = total_seats
            update_fields.append("total_seats")

        if available_seats is not None:
            event.available_seats = available_seats
            update_fields.append("available_seats")

        if ticket_price is not None:
            event.ticket_price = ticket_price
            update_fields.append("ticket_price")

        if update_fields:
            event.save(
                update_fields=update_fields,
            )

        return event

    @staticmethod
    def set_active(
        event: Event,
        *,
        is_active: bool,
    ) -> Event:
        """
        Activate or deactivate an event.
        """
        event.is_active = is_active

        event.save(
            update_fields=["is_active"],
        )

        return event

    @staticmethod
    def count() -> int:
        """
        Return total event count.
        """
        return Event.objects.count()

    @staticmethod
    def count_active() -> int:
        """
        Return total active event count.
        """
        return Event.objects.filter(
            is_active=True,
        ).count()