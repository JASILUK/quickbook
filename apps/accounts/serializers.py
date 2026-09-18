from rest_framework import serializers


# ======================================================================
# AUTHENTICATION REQUEST SERIALIZERS
# ======================================================================


class RegisterSerializer(serializers.Serializer):
    """
    Validate customer registration input.

    Business rules such as:
        - email uniqueness
        - referral code existence
        - sponsor activity
        - binary placement

    belong to AuthService / ReferralService.
    """

    email = serializers.EmailField(
        required=True,
    )

    password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=8,
        style={
            "input_type": "password",
        },
    )

    password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={
            "input_type": "password",
        },
    )

    first_name = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=150,
    )

    last_name = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=150,
    )

    referral_code = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=12,
    )

    def validate_email(self, value):
        return value.strip().lower()

    def validate_first_name(self, value):
        return value.strip()

    def validate_last_name(self, value):
        return value.strip()

    def validate_referral_code(self, value):
        if not value:
            return None

        return value.strip().upper()

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {
                    "password_confirm": (
                        "Passwords do not match."
                    )
                }
            )

        attrs.pop("password_confirm")

        return attrs


class LoginSerializer(serializers.Serializer):
    """
    Validate login credentials.
    """

    email = serializers.EmailField(
        required=True,
    )

    password = serializers.CharField(
        required=True,
        write_only=True,
        style={
            "input_type": "password",
        },
    )

    def validate_email(self, value):
        return value.strip().lower()


# ======================================================================
# AUTHENTICATION RESPONSE SERIALIZERS
# ======================================================================


class AuthUserSerializer(serializers.Serializer):
    """
    User data returned by authentication endpoints.
    """

    id = serializers.IntegerField()

    email = serializers.EmailField()

    first_name = serializers.CharField()

    last_name = serializers.CharField()

    role = serializers.CharField()


class AuthUserDataSerializer(serializers.Serializer):
    """
    Data payload returned by authentication endpoints.
    """

    user = AuthUserSerializer()


# ======================================================================
# CUSTOMER SERIALIZERS
# ======================================================================


class CustomerListSerializer(serializers.ModelSerializer):
    """
    Serializer used when displaying customers in the
    staff dashboard/API.
    """

    class Meta:
        from .models import User

        model = User

        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "referral_code",
            "created_at",
        ]

        read_only_fields = fields


class CustomerDetailSerializer(serializers.ModelSerializer):
    """
    Serializer used for detailed customer information.
    """

    class Meta:
        from .models import User

        model = User

        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "referral_code",
            "referred_by",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "referral_code",
            "referred_by",
            "created_at",
            "is_active",
        ]


class CustomerUpdateSerializer(serializers.Serializer):
    """
    Validate staff customer update input.

    Only profile information can be changed.

    Referral relationships and account status are handled
    by dedicated service methods.
    """

    email = serializers.EmailField(
        required=False,
    )

    first_name = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=150,
    )

    last_name = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=150,
    )

    def validate_email(self, value):
        return value.strip().lower()

    def validate_first_name(self, value):
        return value.strip()

    def validate_last_name(self, value):
        return value.strip()


class CustomerStatusSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying the result of an
    activate/deactivate operation.
    """

    class Meta:
        from .models import User

        model = User

        fields = [
            "id",
            "email",
            "is_active",
        ]

        read_only_fields = fields



class MeSerializer(serializers.ModelSerializer):
    """
    Serializer for the currently authenticated user.

    The user is obtained from request.user.
    All fields are read-only because this endpoint only
    returns the current user's profile.
    """

    class Meta:
        from .models import User
        
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "referral_code",
            "is_active",
            "created_at",
        ]
        read_only_fields = fields

