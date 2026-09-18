
from django.db import transaction

from config.exceptions import (
    VendorNotFoundError,
    VendorServiceError,
)

from ..models import Vendor
from ..repositories import VendorRepository


class VendorService:
    """
    Business logic for Vendor management.

    Views:
        Handle HTTP requests and responses.

    Serializers:
        Handle input/output validation and representation.

    VendorService:
        Handle vendor business rules.

    VendorRepository:
        Handle database queries and persistence.
    """

    @staticmethod
    def list_vendors():
        """
        Return all vendors.
        """
        return VendorRepository.get_all()

    @staticmethod
    def get_vendor(
        *,
        vendor_id: int,
    ) -> Vendor:
        """
        Return a vendor by ID.

        Raises:
            VendorNotFoundError:
                If the vendor does not exist.
        """

        vendor = VendorRepository.get_by_id(
            vendor_id
        )

        if vendor is None:
            raise VendorNotFoundError(
                "Vendor not found.",
                code="VENDOR_NOT_FOUND",
            )

        return vendor

    @staticmethod
    def list_active_vendors():
        """
        Return only active vendors.
        """
        return VendorRepository.get_active()

    @staticmethod
    def search_vendors(
        *,
        search: str,
    ):
        """
        Search vendors by supported fields.
        """

        search = search.strip()

        queryset = VendorRepository.get_all()

        if not search:
            return queryset

        return VendorRepository.search(
            queryset=queryset,
            search=search,
        )

    @staticmethod
    @transaction.atomic
    def create_vendor(
        *,
        name: str,
        email: str = "",
        phone: str = "",
        address: str = "",
        description: str = "",
        created_by,
    ) -> Vendor:
        """
        Create a new vendor.

        The caller is expected to be an authenticated
        staff user. Staff authorization belongs to the
        permission layer.
        """

        name = name.strip()
        email = email.strip().lower()
        phone = phone.strip()
        address = address.strip()
        description = description.strip()

        if not name:
            raise VendorServiceError(
                "Vendor name is required.",
                code="VENDOR_NAME_REQUIRED",
            )

        if not created_by.is_active:
            raise VendorServiceError(
                "The creating staff account is inactive.",
                code="INACTIVE_CREATOR",
                status_code=403,
            )

        if created_by.role != created_by.Role.STAFF:
            raise VendorServiceError(
                "Only staff users can create vendors.",
                code="STAFF_REQUIRED",
                status_code=403,
            )

        return VendorRepository.create(
            name=name,
            email=email,
            phone=phone,
            address=address,
            description=description,
            created_by_id=created_by.id,
        )

    @staticmethod
    @transaction.atomic
    def update_vendor(
        *,
        vendor_id: int,
        name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        address: str | None = None,
        description: str | None = None,
    ) -> Vendor:
        """
        Update vendor information.

        Only fields explicitly provided by the caller
        are changed.
        """

        vendor = VendorService.get_vendor(
            vendor_id=vendor_id
        )

        if name is not None:
            name = name.strip()

            if not name:
                raise VendorServiceError(
                    "Vendor name cannot be empty.",
                    code="VENDOR_NAME_REQUIRED",
                )

        if email is not None:
            email = email.strip().lower()

        if phone is not None:
            phone = phone.strip()

        if address is not None:
            address = address.strip()

        if description is not None:
            description = description.strip()

        return VendorRepository.update(
            vendor,
            name=name,
            email=email,
            phone=phone,
            address=address,
            description=description,
        )

    @staticmethod
    @transaction.atomic
    def activate_vendor(
        *,
        vendor_id: int,
    ) -> Vendor:
        """
        Activate a vendor.
        """

        vendor = VendorService.get_vendor(
            vendor_id=vendor_id
        )

        if vendor.is_active:
            raise VendorServiceError(
                "Vendor is already active.",
                code="VENDOR_ALREADY_ACTIVE",
            )

        return VendorRepository.set_active(
            vendor,
            is_active=True,
        )

    @staticmethod
    @transaction.atomic
    def deactivate_vendor(
        *,
        vendor_id: int,
    ) -> Vendor:
        """
        Deactivate a vendor.

        This is the business-level replacement for hard
        deletion because vendors may have historical
        events and bookings.
        """

        vendor = VendorService.get_vendor(
            vendor_id=vendor_id
        )

        if not vendor.is_active:
            raise VendorServiceError(
                "Vendor is already inactive.",
                code="VENDOR_ALREADY_INACTIVE",
            )

        return VendorRepository.set_active(
            vendor,
            is_active=False,
        )

    @staticmethod
    @transaction.atomic
    def delete_vendor(
        *,
        vendor_id: int,
    ) -> Vendor:
        """
        Vendors are not hard-deleted.

        Use deactivate_vendor() instead.
        """

        raise VendorServiceError(
            "Vendors cannot be deleted. "
            "Deactivate the vendor instead.",
            code="VENDOR_DELETE_NOT_ALLOWED",
            status_code=409,
        )
