from rest_framework import serializers

from apps.events.models import Event
from apps.events.models import Vendor


class EventVendorSerializer(serializers.ModelSerializer):
    """
    Limited vendor information exposed through Event APIs.

    Customers should not need access to staff-only Vendor
    management endpoints just to see who provides an event.
    """

    class Meta:
        model = Vendor
        fields = [
            "id",
            "name",
            "description",
        ]
        read_only_fields = fields


class EventListSerializer(serializers.ModelSerializer):
    """
    Serializer used when listing events.

    Suitable for both customer browsing and staff event lists.
    """

    vendor = EventVendorSerializer(read_only=True)

    class Meta:
        model = Event
        fields = [
            "id",
            "vendor",
            "title",
            "venue_name",
            "address",
            "start_datetime",
            "end_datetime",
            "total_seats",
            "available_seats",
            "ticket_price",
            "is_active",
        ]
        read_only_fields = fields


class EventDetailSerializer(serializers.ModelSerializer):
    """
    Detailed read-only representation of an event.
    """

    vendor = EventVendorSerializer(read_only=True)

    class Meta:
        model = Event
        fields = [
            "id",
            "vendor",
            "title",
            "description",
            "venue_name",
            "address",
            "latitude",
            "longitude",
            "start_datetime",
            "end_datetime",
            "total_seats",
            "available_seats",
            "ticket_price",
            "is_active",
            "created_by",
            "created_at",
        ]
        read_only_fields = fields


class EventCreateSerializer(serializers.Serializer):
    """
    Input serializer for staff event creation.

    available_seats is intentionally NOT accepted from the client.
    It is initialized by EventService to total_seats.
    """

    vendor_id = serializers.IntegerField(
        min_value=1,
    )

    title = serializers.CharField(
        max_length=200,
    )

    description = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )

    venue_name = serializers.CharField(
        max_length=200,
    )

    address = serializers.CharField()

    latitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        allow_null=True,
    )

    longitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        allow_null=True,
    )

    start_datetime = serializers.DateTimeField()

    end_datetime = serializers.DateTimeField()

    total_seats = serializers.IntegerField(
        min_value=1,
    )

    ticket_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
    )

    def validate(self, attrs):
        """
        Validate relationships between fields.

        Detailed business rules remain in EventService.
        """

        latitude = attrs.get("latitude")
        longitude = attrs.get("longitude")

        if (latitude is None) != (longitude is None):
            raise serializers.ValidationError(
                "Latitude and longitude must be provided together."
            )

        return attrs


class EventUpdateSerializer(serializers.Serializer):
    """
    Input serializer for staff partial event updates.

    All fields are optional because the API uses PATCH.

    available_seats is intentionally NOT accepted from the client.
    EventService calculates it when total_seats changes.
    """

    vendor_id = serializers.IntegerField(
        min_value=1,
        required=False,
    )

    title = serializers.CharField(
        max_length=200,
        required=False,
    )

    description = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    venue_name = serializers.CharField(
        max_length=200,
        required=False,
    )

    address = serializers.CharField(
        required=False,
    )

    latitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        allow_null=True,
    )

    longitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        allow_null=True,
    )

    start_datetime = serializers.DateTimeField(
        required=False,
    )

    end_datetime = serializers.DateTimeField(
        required=False,
    )

    total_seats = serializers.IntegerField(
        min_value=1,
        required=False,
    )

    ticket_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
        required=False,
    )

    def validate(self, attrs):
        """
        Validate coordinate pairing when both coordinates
        are explicitly supplied.

        EventService performs final validation using existing
        coordinates for PATCH requests.
        """

        if "latitude" in attrs and "longitude" in attrs:
            latitude = attrs["latitude"]
            longitude = attrs["longitude"]

            if (latitude is None) != (longitude is None):
                raise serializers.ValidationError(
                    "Latitude and longitude must be provided together."
                )

        return attrs




class EventFilterSerializer(serializers.Serializer):
    """
    Validate query parameters used for event filtering.
    """

    search = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    vendor_id = serializers.IntegerField(
        required=False,
        min_value=1,
    )

    start_datetime = serializers.DateTimeField(
        required=False,
    )

    end_datetime = serializers.DateTimeField(
        required=False,
    )

    min_price = serializers.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        min_value=0,
    )

    max_price = serializers.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        min_value=0,
    )

    def validate(self, attrs):
        """
        Validate relationships between filter values.
        """

        start_datetime = attrs.get("start_datetime")
        end_datetime = attrs.get("end_datetime")

        if (
            start_datetime is not None
            and end_datetime is not None
            and end_datetime < start_datetime
        ):
            raise serializers.ValidationError({
                "end_datetime": (
                    "end_datetime must be greater than or equal "
                    "to start_datetime."
                )
            })

        min_price = attrs.get("min_price")
        max_price = attrs.get("max_price")

        if (
            min_price is not None
            and max_price is not None
            and max_price < min_price
        ):
            raise serializers.ValidationError({
                "max_price": (
                    "max_price must be greater than or equal "
                    "to min_price."
                )
            })

        return attrs