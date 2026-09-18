from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)

from apps.accounts.permissions import IsStaffUser
from apps.bookings.serializers import (
    BookingCreateSerializer,
    BookingDetailSerializer,
    BookingFilterSerializer,
    BookingListSerializer,
)
from apps.bookings.services import BookingService
from apps.accounts.base_views import BaseAPIView


@extend_schema_view(
    get=extend_schema(
        summary="List bookings",
        description=(
            "Customers can view their own booking history. "
            "Staff can view all bookings and apply filters."
        ),
        parameters=[
        OpenApiParameter(
            name="page",
            type=int,
            required=False,
            description="Page number.",
        ),
        OpenApiParameter(
            name="page_size",
            type=int,
            required=False,
            description="Number of bookings per page. Maximum 100.",
        ),
        OpenApiParameter(
            name="user_id",
            type=int,
            required=False,
            description="Filter bookings by customer ID. Staff only.",
        ),
        OpenApiParameter(
            name="event_id",
            type=int,
            required=False,
            description="Filter bookings by event ID.",
        ),
        OpenApiParameter(
            name="status",
            type=str,
            required=False,
            enum=["CONFIRMED", "CANCELLED"],
            description="Filter bookings by status.",
        ),
        OpenApiParameter(
            name="start_datetime",
            type=str,
            required=False,
            description=(
                "Filter bookings whose event starts at or after "
                "this datetime."
            ),
        ),
        OpenApiParameter(
            name="end_datetime",
            type=str,
            required=False,
            description=(
                "Filter bookings whose event starts at or before "
                "this datetime."
            ),
        ),
        OpenApiParameter(
            name="search",
            type=str,
            required=False,
            description=(
                "Search by customer information, event title, "
                "or venue."
            ),
        ),
    ],
    ),
)
class BookingListCreateView(BaseAPIView):
    """
    GET:
        Customer -> own bookings
        Staff    -> all bookings with filters

    POST:
        Customer -> create booking
        Staff    -> not allowed
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # -----------------------------------------
        # 1. Validate query parameters
        # -----------------------------------------
        filter_serializer = BookingFilterSerializer(
            data=request.query_params
        )
        filter_serializer.is_valid(raise_exception=True)

        filters = filter_serializer.validated_data

        # -----------------------------------------
        # 2. Get bookings through service
        # -----------------------------------------
        bookings = BookingService.list_bookings(
            user=request.user,
            user_id=filters.get("user_id"),
            event_id=filters.get("event_id"),
            booking_status=filters.get("status"),
            start_datetime=filters.get("start_datetime"),
            end_datetime=filters.get("end_datetime"),
            search=filters.get("search"),
        )

        # -----------------------------------------
        # 3. Paginate
        # -----------------------------------------
        paginator, page = self.paginate_queryset(bookings)

        if page is not None:
            serializer = BookingListSerializer(
                page,
                many=True,
            )

            return self.paginated_success_response(
                paginator=paginator,
                data=serializer.data,
                message="Bookings retrieved successfully.",
            )

        # -----------------------------------------
        # 4. Non-paginated fallback
        # -----------------------------------------
        serializer = BookingListSerializer(
            bookings,
            many=True,
        )

        return self.success_response(
            data=serializer.data,
            message="Bookings retrieved successfully.",
        )

    def post(self, request):
        # -----------------------------------------
        # Staff cannot create customer bookings
        # -----------------------------------------
        if (
            not request.user.is_active
            or request.user.role != request.user.Role.CUSTOMER
        ):
            from config.exceptions import BookingServiceError

            raise BookingServiceError(
                "Only customers can create bookings.",
                code="CUSTOMER_REQUIRED",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        # -----------------------------------------
        # 1. Validate request
        # -----------------------------------------
        serializer = BookingCreateSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        # -----------------------------------------
        # 2. Business logic
        # -----------------------------------------
        booking = BookingService.create_booking(
            user=request.user,
            event_id=serializer.validated_data["event_id"],
            quantity=serializer.validated_data["quantity"],
        )

        # -----------------------------------------
        # 3. Serialize created booking
        # -----------------------------------------
        response_serializer = BookingDetailSerializer(
            booking
        )

        return self.success_response(
            data=response_serializer.data,
            message="Booking created successfully.",
            status_code=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    get=extend_schema(
        summary="Get booking details",
        description=(
            "Customers can view their own booking. "
            "Staff can view any booking."
        ),
        responses={
            200: OpenApiResponse(
                response=BookingDetailSerializer,
                description="Booking retrieved successfully.",
            ),
            401: OpenApiResponse(
                description="Authentication required.",
            ),
            403: OpenApiResponse(
                description="You do not have access to this booking.",
            ),
            404: OpenApiResponse(
                description="Booking not found.",
            ),
        },
    ),
)
class BookingDetailView(BaseAPIView):
    """
    Retrieve a single booking.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, booking_id):
        booking = BookingService.get_booking(
            booking_id=booking_id,
            user=request.user,
        )

        serializer = BookingDetailSerializer(
            booking
        )

        return self.success_response(
            data=serializer.data,
            message="Booking retrieved successfully.",
        )


@extend_schema(
    summary="Cancel booking",
    description=(
        "Cancel a confirmed booking. "
        "Customers can cancel their own bookings and staff can "
        "cancel bookings. Cancellation is allowed only more than "
        "2 hours before the event starts. Cancelled bookings remain "
        "in booking history."
    ),
    request=None,
    responses={
        200: OpenApiResponse(
            response=BookingDetailSerializer,
            description="Booking cancelled successfully.",
        ),
        400: OpenApiResponse(
            description=(
                "Booking is already cancelled or the "
                "2-hour cancellation deadline has passed."
            ),
        ),
        401: OpenApiResponse(
            description="Authentication required.",
        ),
        403: OpenApiResponse(
            description="You do not have permission to cancel this booking.",
        ),
        404: OpenApiResponse(
            description="Booking not found.",
        ),
        409: OpenApiResponse(
            description="Seat availability inconsistency.",
        ),
    },
)
class BookingCancelView(BaseAPIView):
    """
    Cancel an existing booking.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        booking = BookingService.cancel_booking(
            booking_id=booking_id,
            user=request.user,
        )

        serializer = BookingDetailSerializer(
            booking
        )

        return self.success_response(
            data=serializer.data,
            message="Booking cancelled successfully.",
        )