
from rest_framework import serializers

from apps.bookings.models import Booking
from apps.events.models import Event


class BookingEventSerializer(serializers.ModelSerializer):

    vendor_name = serializers.CharField(
        source="vendor.name",
        read_only=True,
    )

    class Meta:
        model = Event
        fields = [
            "id",
            "title",
            "vendor_name",
            "venue_name",
            "address",
            "start_datetime",
            "end_datetime",
            "ticket_price",
        ]
        read_only_fields = fields


class BookingUserSerializer(serializers.Serializer):
    """
    Minimal customer information included in staff booking responses.
    """

    id = serializers.IntegerField(read_only=True)
    email = serializers.EmailField(read_only=True)


class BookingCreateSerializer(serializers.Serializer):
    """
    Input serializer for creating a booking.

    The client only provides:
        - event_id
        - quantity

    Price and seat availability are handled by BookingService.
    """

    event_id = serializers.IntegerField(
        min_value=1,
    )

    quantity = serializers.IntegerField(
        min_value=1,
    )


class BookingListSerializer(serializers.ModelSerializer):
    """
    Booking response serializer.

    Used for:
        - customer booking history
        - customer upcoming bookings
        - staff booking list
    """

    event = BookingEventSerializer(
        read_only=True,
    )

    customer = BookingUserSerializer(
        source="user",
        read_only=True,
    )

    class Meta:
        model = Booking
        fields = [
            "id",
            "customer",
            "event",
            "quantity",
            "total_amount",
            "status",
            "booked_at",
            "cancelled_at",
            "updated_at",
        ]
        read_only_fields = fields


class BookingDetailSerializer(serializers.ModelSerializer):
    """
    Detailed booking response.

    Currently contains the same core information as the list
    serializer, but kept separate so the detail response can
    evolve independently later.
    """

    event = BookingEventSerializer(
        read_only=True,
    )

    customer = BookingUserSerializer(
        source="user",
        read_only=True,
    )

    class Meta:
        model = Booking
        fields = [
            "id",
            "customer",
            "event",
            "quantity",
            "total_amount",
            "status",
            "booked_at",
            "cancelled_at",
            "updated_at",
        ]
        read_only_fields = fields


class BookingCancelSerializer(serializers.Serializer):
    """
    Cancellation does not require any request body.

    This serializer exists so the API can have an explicit
    cancellation contract and can be extended later if needed.
    """

    pass




class BookingFilterSerializer(serializers.Serializer):
    """
    Query parameters for booking lists.

    Customers are restricted by BookingService to their own
    bookings. Staff can use the broader filters.
    """

    user_id = serializers.IntegerField(
        required=False,
        min_value=1,
    )

    event_id = serializers.IntegerField(
        required=False,
        min_value=1,
    )

    status = serializers.ChoiceField(
        required=False,
        choices=Booking.Status.choices,
    )

    start_datetime = serializers.DateTimeField(
        required=False,
    )

    end_datetime = serializers.DateTimeField(
        required=False,
    )

    search = serializers.CharField(
        required=False,
        allow_blank=True,
        trim_whitespace=True,
    )

    def validate(self, attrs):
        start_datetime = attrs.get("start_datetime")
        end_datetime = attrs.get("end_datetime")

        if (
            start_datetime is not None
            and end_datetime is not None
            and end_datetime < start_datetime
        ):
            raise serializers.ValidationError(
                {
                    "end_datetime": (
                        "end_datetime must be greater than "
                        "or equal to start_datetime."
                    )
                }
            )

        return attrs

