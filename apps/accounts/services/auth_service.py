from django.contrib.auth import authenticate
from django.db import transaction

from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from config.exceptions import (
AuthenticationServiceError,
LoginError,
ReferralPlacementError,
RegistrationError,
)

from apps.referrals.services import ReferralService

from ..models import User
from ..repositories import UserRepository



class AuthService:
    

    # ==================================================================
    # CUSTOMER REGISTRATION
    # ==================================================================

    @staticmethod
    @transaction.atomic
    def register_customer(
        *,
        email: str,
        password: str,
        first_name: str = "",
        last_name: str = "",
        referral_code: str | None = None,
    ) -> User:
        """
        Register a new customer and create their referral placement.

        Workflow:

            1. Normalize input.
            2. Check email uniqueness.
            3. Resolve referral sponsor.
            4. Create customer.
            5. Create binary referral placement.
            6. Create referral closure records.

        The complete workflow runs inside one database transaction.
        """

        # --------------------------------------------------------------
        # NORMALIZE INPUT
        # --------------------------------------------------------------

        email = email.strip().lower()
        first_name = first_name.strip()
        last_name = last_name.strip()

        if referral_code:
            referral_code = referral_code.strip().upper()

        # --------------------------------------------------------------
        # CHECK EMAIL
        # --------------------------------------------------------------

        existing_user = UserRepository.get_by_email(email)

        if existing_user:
            raise RegistrationError(
                "A user with this email already exists.",
                code="EMAIL_ALREADY_EXISTS",
                status_code=409,
            )

        # --------------------------------------------------------------
        # RESOLVE REFERRAL SPONSOR
        # --------------------------------------------------------------

        sponsor = None

        if referral_code:
            sponsor = UserRepository.get_by_referral_code(
                referral_code
            )

            if sponsor is None:
                raise RegistrationError(
                    "Invalid referral code.",
                    code="INVALID_REFERRAL_CODE",
                )

            if sponsor.role != User.Role.CUSTOMER:
                raise RegistrationError(
                    "The referral code does not belong to a customer.",
                    code="INVALID_REFERRAL_SPONSOR",
                )

            if not sponsor.is_active:
                raise RegistrationError(
                    "The referring customer is inactive.",
                    code="INACTIVE_REFERRAL_SPONSOR",
                )

        # --------------------------------------------------------------
        # CREATE CUSTOMER
        # --------------------------------------------------------------

        user = UserRepository.create_customer(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            referred_by=sponsor,
        )

        # --------------------------------------------------------------
        # CREATE BINARY REFERRAL PLACEMENT
        # --------------------------------------------------------------

        try:
            ReferralService.create_placement(
                user=user,
                sponsor=sponsor,
            )

        except ReferralPlacementError as exc:
            raise RegistrationError(
                str(exc),
                code="REFERRAL_PLACEMENT_ERROR",
            ) from exc

        return user

    # ==================================================================
    # LOGIN
    # ==================================================================

    @staticmethod
    def login(
        *,
        email: str,
        password: str,
    ) -> dict:
        """
        Authenticate a user and generate access and refresh tokens.

        Returns:

            {
                "user": User,
                "access_token": str,
                "refresh_token": str,
            }

        Cookie handling is performed by the View layer.
        """

        email = email.strip().lower()

        user = authenticate(
            username=email,
            password=password,
        )

        if user is None:
            raise LoginError(
                "Invalid email or password.",
                code="INVALID_CREDENTIALS",
            )

        if not user.is_active:
            raise LoginError(
                "This account is inactive.",
                code="INACTIVE_ACCOUNT",
            )

        refresh = RefreshToken.for_user(user)

        return {
            "user": user,
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
        }

    # ==================================================================
    # REFRESH
    # ==================================================================

    @staticmethod
    def refresh(
        *,
        refresh_token: str,
    ) -> dict:
        """
        Validate a refresh token and issue a new access/refresh pair.

        Workflow:

            1. Validate the existing refresh token.
            2. Resolve the user.
            3. Ensure the user is still active.
            4. Blacklist the old refresh token.
            5. Generate a new refresh token.
            6. Generate a new access token.

        Returns:

            {
                "user": User,
                "access_token": str,
                "refresh_token": str,
            }
        """

        try:
            old_refresh = RefreshToken(refresh_token)

            user_id = old_refresh.get("user_id")

            if not user_id:
                raise AuthenticationServiceError(
                    "Invalid refresh token.",
                    code="INVALID_REFRESH_TOKEN",
                    status_code=401,
                )

            user = UserRepository.get_by_id(
                user_id
            )

            if user is None:
                raise AuthenticationServiceError(
                    "User account was not found.",
                    code="USER_NOT_FOUND",
                    status_code=401,
                )

            if not user.is_active:
                raise AuthenticationServiceError(
                    "This account is inactive.",
                    code="INACTIVE_ACCOUNT",
                    status_code=401,
                )

            # Blacklist the old refresh token.
            old_refresh.blacklist()

            # Create a completely new refresh token.
            new_refresh = RefreshToken.for_user(user)

            return {
                "user": user,
                "access_token": str(
                    new_refresh.access_token
                ),
                "refresh_token": str(
                    new_refresh
                ),
            }

        except TokenError as exc:
            raise AuthenticationServiceError(
                "Invalid or expired refresh token.",
                code="INVALID_REFRESH_TOKEN",
                status_code=401,
            ) from exc

    # ==================================================================
    # LOGOUT
    # ==================================================================

    @staticmethod
    def logout(
        *,
        refresh_token: str,
    ) -> None:
        """
        Blacklist a refresh token.

        Important:

            Logging out does NOT immediately invalidate an already-issued
            access token.

            The access token remains valid until its normal expiration.

            Our access-token lifetime is intentionally short.
        """

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()

        except TokenError as exc:
            raise AuthenticationServiceError(
                "Invalid or already blacklisted refresh token.",
                code="INVALID_REFRESH_TOKEN",
                status_code=401,
            ) from exc
