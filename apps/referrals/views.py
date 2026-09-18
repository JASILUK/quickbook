from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)

from apps.accounts.base_views import BaseAPIView
from apps.referrals.serializers import (
    ReferralRootSerializer,
    ReferralStatsSerializer,
    ReferralTreeSerializer,
)
from apps.referrals.services import ReferralService
from config.exceptions import PermissionServiceError


class ReferralAccessMixin:
    """
    Shared access control for referral endpoints.

    Customers can access only their own referral information.
    Staff can access any user's referral information.
    """

    def check_referral_access(self, request, user_id: int) -> None:
        # Staff can inspect any user's referral information.
        if request.user.role == request.user.Role.STAFF:
            return

        # Customers can only inspect their own referral information.
        if (
            request.user.role == request.user.Role.CUSTOMER
            and request.user.id == user_id
        ):
            return

        raise PermissionServiceError(
            "You do not have permission to access this referral information.",
            code="REFERRAL_ACCESS_DENIED",
            status_code=403,
        )


class ReferralTreeView(
    ReferralAccessMixin,
    BaseAPIView,
):
    """
    Return the complete binary subtree rooted at the requested user.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get referral tree",
        description=(
            "Returns the complete binary referral subtree rooted at "
            "the requested user. Customers can only view their own "
            "tree. Staff can view any user's tree."
        ),
        parameters=[
            OpenApiParameter(
                name="user_id",
                type=int,
                location=OpenApiParameter.PATH,
                description="ID of the user whose referral subtree is requested.",
                required=True,
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=ReferralTreeSerializer,
                description="Referral tree retrieved successfully.",
            ),
            401: OpenApiResponse(
                description="Authentication required.",
            ),
            403: OpenApiResponse(
                description="Referral access denied.",
            ),
            404: OpenApiResponse(
                description="Referral node not found.",
            ),
        },
    )
    def get(self, request, user_id):
        # -----------------------------------------
        # 1. Permission check
        # -----------------------------------------
        self.check_referral_access(
            request,
            user_id,
        )

        # -----------------------------------------
        # 2. Get tree through service
        # -----------------------------------------
        tree = ReferralService.get_tree(
            user_id=user_id,
        )

        # -----------------------------------------
        # 3. Serialize response
        # -----------------------------------------
        serializer = ReferralTreeSerializer(
            tree
        )

        return self.success_response(
            data=serializer.data,
            message="Referral tree retrieved successfully.",
        )


class ReferralRootView(
    ReferralAccessMixin,
    BaseAPIView,
):
    """
    Return the root user of the referral network
    containing the requested user.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get referral network root",
        description=(
            "Returns the root user of the referral network containing "
            "the requested user. Customers can only query their own "
            "root. Staff can query the root for any user."
        ),
        parameters=[
            OpenApiParameter(
                name="user_id",
                type=int,
                location=OpenApiParameter.PATH,
                description="ID of the user whose network root is requested.",
                required=True,
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=ReferralRootSerializer,
                description="Referral root retrieved successfully.",
            ),
            401: OpenApiResponse(
                description="Authentication required.",
            ),
            403: OpenApiResponse(
                description="Referral access denied.",
            ),
            404: OpenApiResponse(
                description="Referral node or root not found.",
            ),
        },
    )
    def get(self, request, user_id):
        # -----------------------------------------
        # 1. Permission check
        # -----------------------------------------
        self.check_referral_access(
            request,
            user_id,
        )

        # -----------------------------------------
        # 2. Get root through service
        # -----------------------------------------
        root = ReferralService.get_root(
            user_id=user_id,
        )

        # -----------------------------------------
        # 3. Serialize response
        # -----------------------------------------
        serializer = ReferralRootSerializer(
            root,
        )

        return self.success_response(
            data=serializer.data,
            message="Referral root retrieved successfully.",
        )


class ReferralStatsView(
    ReferralAccessMixin,
    BaseAPIView,
):
    """
    Return binary referral statistics for the requested user.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get referral statistics",
        description=(
            "Returns left-team, right-team, total-team, and direct "
            "binary-child counts for the requested user. Customers "
            "can only view their own statistics. Staff can view "
            "statistics for any user."
        ),
        parameters=[
            OpenApiParameter(
                name="user_id",
                type=int,
                location=OpenApiParameter.PATH,
                description="ID of the user whose referral statistics are requested.",
                required=True,
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=ReferralStatsSerializer,
                description="Referral statistics retrieved successfully.",
            ),
            401: OpenApiResponse(
                description="Authentication required.",
            ),
            403: OpenApiResponse(
                description="Referral access denied.",
            ),
            404: OpenApiResponse(
                description="Referral node not found.",
            ),
        },
    )
    def get(self, request, user_id):
        # -----------------------------------------
        # 1. Permission check
        # -----------------------------------------
        self.check_referral_access(
            request,
            user_id,
        )

        # -----------------------------------------
        # 2. Get stats through service
        # -----------------------------------------
        stats = ReferralService.get_stats(
            user_id=user_id,
        )

        # -----------------------------------------
        # 3. Serialize response
        # -----------------------------------------
        serializer = ReferralStatsSerializer(
            stats,
        )

        return self.success_response(
            data=serializer.data,
            message="Referral statistics retrieved successfully.",
        )

