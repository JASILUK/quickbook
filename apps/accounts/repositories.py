from django.contrib.auth import get_user_model
from django.db.models import QuerySet

User = get_user_model()


class UserRepository:
    """
    Handles database queries related to User.
    Business rules belong in services.py.
    """

    @staticmethod
    def get_by_id(user_id: int) -> User | None:
        return (
            User.objects
            .filter(id=user_id)
            .first()
        )

    @staticmethod
    def get_by_email(email: str) -> User | None:
        return (
            User.objects
            .filter(email__iexact=email)
            .first()
        )

    @staticmethod
    def get_by_referral_code(
        referral_code: str,
    ) -> User | None:
        return (
            User.objects
            .filter(referral_code=referral_code)
            .first()
        )

    @staticmethod
    def get_active_by_email(
        email: str,
    ) -> User | None:
        return (
            User.objects
            .filter(
                email__iexact=email,
                is_active=True,
            )
            .first()
        )

    @staticmethod
    def get_customers() -> QuerySet[User]:
        return User.objects.filter(
            role=User.Role.CUSTOMER
        )

    @staticmethod
    def get_staff_users() -> QuerySet[User]:
        return User.objects.filter(
            role=User.Role.STAFF
        )

    @staticmethod
    def get_referred_users(
        user: User,
    ) -> QuerySet[User]:
        return (
            User.objects
            .filter(referred_by=user)
            .order_by("-created_at")
        )

    @staticmethod
    def create_customer(
        *,
        email: str,
        password: str,
        first_name: str = "",
        last_name: str = "",
        referred_by: User | None = None,
    ) -> User:

        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=User.Role.CUSTOMER,
            referred_by=referred_by,
        )

        user.set_password(password)
        user.save()

        return user

    @staticmethod
    def update_customer(
        user: User,
        *,
        email: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> User:

        if email is not None:
            user.email = email

        if first_name is not None:
            user.first_name = first_name

        if last_name is not None:
            user.last_name = last_name

        user.save(
            update_fields=[
                "email",
                "first_name",
                "last_name",
            ]
        )

        return user

    @staticmethod
    def set_active(
        user: User,
        is_active: bool,
    ) -> User:

        user.is_active = is_active
        user.save(update_fields=["is_active"])

        return user

    @staticmethod
    def count_customers() -> int:
        return User.objects.filter(
            role=User.Role.CUSTOMER
        ).count()

    @staticmethod
    def count_staff() -> int:
        return User.objects.filter(
            role=User.Role.STAFF
        ).count()