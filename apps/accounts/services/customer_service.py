from django.db import transaction

from config.exceptions import (
    CustomerNotFoundError,
    CustomerServiceError,
)

from ..models import User
from ..repositories import UserRepository


class CustomerService:
    """
    Business logic for customer management.

    Used by the staff dashboard and staff APIs.

    Repository:
        Handles database queries.

    CustomerService:
        Handles business rules and workflows.

    Views:
        Handle HTTP requests and responses.
    """

    # ==================================================================
    # LIST CUSTOMERS
    # ==================================================================

    @staticmethod
    def list_customers():
        """
        Return all customer users.

        Filtering, searching, and pagination can be applied
        by the API/dashboard layer as needed.
        """

        return UserRepository.get_customers()

    # ==================================================================
    # GET CUSTOMER
    # ==================================================================

    @staticmethod
    def get_customer(
        *,
        user_id: int,
    ) -> User:
        """
        Return a single customer.

        Raises:
            CustomerNotFoundError:
                If the user does not exist or is not a customer.
        """

        user = UserRepository.get_by_id(user_id)

        if user is None:
            raise CustomerNotFoundError(
                "Customer not found.",
                code="CUSTOMER_NOT_FOUND",
            )

        if user.role != User.Role.CUSTOMER:
            raise CustomerNotFoundError(
                "Customer not found.",
                code="CUSTOMER_NOT_FOUND",
            )

        return user

    # ==================================================================
    # UPDATE CUSTOMER
    # ==================================================================

    @staticmethod
    @transaction.atomic
    def update_customer(
        *,
        user_id: int,
        email: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> User:
        """
        Update customer profile information.

        Referral information is intentionally not changed here.

        A customer's referral sponsor and binary placement should
        remain stable after registration.
        """

        customer = CustomerService.get_customer(
            user_id=user_id
        )

        # --------------------------------------------------------------
        # NORMALIZE INPUT
        # --------------------------------------------------------------

        if email is not None:
            email = email.strip().lower()

        if first_name is not None:
            first_name = first_name.strip()

        if last_name is not None:
            last_name = last_name.strip()

        # --------------------------------------------------------------
        # CHECK EMAIL CHANGE
        # --------------------------------------------------------------

        if email is not None and email != customer.email:

            existing_user = (
                UserRepository.get_by_email(email)
            )

            if (
                existing_user is not None
                and existing_user.id != customer.id
            ):
                raise CustomerServiceError(
                    "A user with this email already exists.",
                    code="EMAIL_ALREADY_EXISTS",
                    status_code=409,
                )

        # --------------------------------------------------------------
        # UPDATE CUSTOMER
        # --------------------------------------------------------------

        return UserRepository.update_customer(
            customer,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )

    # ==================================================================
    # ACTIVATE CUSTOMER
    # ==================================================================

    @staticmethod
    @transaction.atomic
    def activate_customer(
        *,
        user_id: int,
    ) -> User:
        """
        Activate a customer account.
        """

        customer = CustomerService.get_customer(
            user_id=user_id
        )

        if customer.is_active:
            raise CustomerServiceError(
                "Customer is already active.",
                code="CUSTOMER_ALREADY_ACTIVE",
            )

        return UserRepository.set_active(
            customer,
            True,
        )

    # ==================================================================
    # DEACTIVATE CUSTOMER
    # ==================================================================

    @staticmethod
    @transaction.atomic
    def deactivate_customer(
        *,
        user_id: int,
    ) -> User:
        """
        Deactivate a customer account.

        The customer is not deleted.

        Existing bookings and referral relationships remain intact.
        """

        customer = CustomerService.get_customer(
            user_id=user_id
        )

        if not customer.is_active:
            raise CustomerServiceError(
                "Customer is already inactive.",
                code="CUSTOMER_ALREADY_INACTIVE",
            )

        return UserRepository.set_active(
            customer,
            False,
        )