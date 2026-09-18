
from rest_framework import serializers

from ..models import Vendor


class VendorListSerializer(serializers.ModelSerializer):
    """
    Serializer used when returning a list of vendors.
    """

    class Meta:
        model = Vendor
        fields = [
            "id",
            "name",
            "email",
            "phone",
            "address",
            "is_active",
            "created_at",
        ]

        read_only_fields = fields


class VendorDetailSerializer(serializers.ModelSerializer):
    """
    Serializer used when returning detailed vendor information.
    """

    created_by = serializers.IntegerField(
        source="created_by_id",
        read_only=True,
    )

    class Meta:
        model = Vendor
        fields = [
            "id",
            "name",
            "email",
            "phone",
            "address",
            "description",
            "is_active",
            "created_by",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "is_active",
            "created_by",
            "created_at",
        ]


class VendorCreateSerializer(serializers.Serializer):
    """
    Validate vendor creation input.

    Business rules such as staff authorization
    and persistence belong to VendorService.
    """

    name = serializers.CharField(
        required=True,
        max_length=200,
    )

    email = serializers.EmailField(
        required=False,
        allow_blank=True,
    )

    phone = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=20,
    )

    address = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    description = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    def validate_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Vendor name cannot be empty."
            )

        return value

    def validate_email(self, value):
        return value.strip().lower()

    def validate_phone(self, value):
        return value.strip()

    def validate_address(self, value):
        return value.strip()

    def validate_description(self, value):
        return value.strip()


class VendorUpdateSerializer(serializers.Serializer):
    """
    Validate partial vendor updates.

    Every field is optional because this serializer
    is intended for PATCH requests.
    """

    name = serializers.CharField(
        required=False,
        max_length=200,
    )

    email = serializers.EmailField(
        required=False,
        allow_blank=True,
    )

    phone = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=20,
    )

    address = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    description = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    def validate_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Vendor name cannot be empty."
            )

        return value

    def validate_email(self, value):
        return value.strip().lower()

    def validate_phone(self, value):
        return value.strip()

    def validate_address(self, value):
        return value.strip()

    def validate_description(self, value):
        return value.strip()

