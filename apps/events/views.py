
from rest_framework import status

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes



from apps.accounts.base_views import BaseAPIView
from apps.accounts.permissions import IsStaffUser
from apps.accounts.schemas import response_schema

from .serializers import (
    VendorCreateSerializer,
    VendorDetailSerializer,
    VendorListSerializer,
    VendorUpdateSerializer,
)
from .services.vendor_service import VendorService


from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.events.serializers.event_serializers import (
    EventCreateSerializer,
    EventDetailSerializer,
    EventListSerializer,
    EventUpdateSerializer,
    EventFilterSerializer
)
from apps.events.services.event_service import EventService



# ======================================================================
# VENDOR LIST / CREATE
# ======================================================================
@extend_schema(
    parameters=[
        OpenApiParameter(
            name="search",
            type=str,
            required=False,
            description=(
                "Search by vendor name, email, "
                "phone, or address."
            ),
        ),
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
            description="Number of vendors per page. Maximum 100.",
        ),
    ],
    request=VendorCreateSerializer,
    responses={
        status.HTTP_200_OK: response_schema(
            data_serializer=VendorListSerializer,
            many=True,
        ),
        status.HTTP_201_CREATED: response_schema(
            data_serializer=VendorDetailSerializer,
        ),
    },
    description=(
        "List vendors or create a new vendor. "
        "Staff access required."
    ),
)
class VendorListCreateView(BaseAPIView):
    """
    Staff-only vendor list and creation.
    """

    permission_classes = [IsStaffUser]

    def get(self, request):
        search = request.query_params.get(
            "search",
            "",
        )

        vendors = VendorService.search_vendors(
            search=search,
        )

        paginator, page = self.paginate_queryset(vendors)

        if page is not None:
            serializer = VendorListSerializer(
                page,
                many=True,
            )

            return self.paginated_success_response(
                paginator=paginator,
                data=serializer.data,
                message="Vendors retrieved successfully.",
                status_code=status.HTTP_200_OK,
            )

        serializer = VendorListSerializer(
            vendors,
            many=True,
        )

        return self.success_response(
            data=serializer.data,
            message="Vendors retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )

    def post(self, request):
        serializer = VendorCreateSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        vendor = VendorService.create_vendor(
            created_by=request.user,
            **serializer.validated_data,
        )

        response_serializer = VendorDetailSerializer(
            vendor,
        )

        return self.success_response(
            message="Vendor created successfully.",
            data=response_serializer.data,
            status_code=status.HTTP_201_CREATED,
        )


# ======================================================================
# VENDOR DETAIL / UPDATE
# ======================================================================


@extend_schema(
    responses={
        status.HTTP_200_OK: response_schema(
            data_serializer=VendorDetailSerializer,
        ),
    },
    description=(
        "Retrieve detailed vendor information. "
        "Staff access required."
    ),
)
class VendorDetailView(BaseAPIView):
    """
    Staff-only vendor detail and partial update.
    """

    permission_classes = [IsStaffUser]

    def get(
        self,
        request,
        vendor_id,
    ):
        vendor = VendorService.get_vendor(
            vendor_id=vendor_id,
        )

        serializer = VendorDetailSerializer(
            vendor,
        )

        return self.success_response(
            data=serializer.data,
            status_code=status.HTTP_200_OK,
        )

    @extend_schema(
        request=VendorUpdateSerializer,
        responses={
            status.HTTP_200_OK: response_schema(
                data_serializer=VendorDetailSerializer,
            ),
        },
        description=(
            "Partially update vendor information. "
            "Staff access required."
        ),
    )
    def patch(
        self,
        request,
        vendor_id,
    ):
        serializer = VendorUpdateSerializer(
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        vendor = VendorService.update_vendor(
            vendor_id=vendor_id,
            **serializer.validated_data,
        )

        response_serializer = VendorDetailSerializer(
            vendor,
        )

        return self.success_response(
            message="Vendor updated successfully.",
            data=response_serializer.data,
            status_code=status.HTTP_200_OK,
        )


# ======================================================================
# VENDOR ACTIVATE
# ======================================================================


@extend_schema(
    request=None,
    responses={
        status.HTTP_200_OK: response_schema(
            data_serializer=VendorDetailSerializer,
        ),
    },
    description=(
        "Activate a vendor. "
        "Staff access required."
    ),
)
class VendorActivateView(BaseAPIView):
    """
    Staff-only vendor activation.
    """

    permission_classes = [IsStaffUser]

    def post(
        self,
        request,
        vendor_id,
    ):
        vendor = VendorService.activate_vendor(
            vendor_id=vendor_id,
        )

        serializer = VendorDetailSerializer(
            vendor,
        )

        return self.success_response(
            message="Vendor activated successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
        )


# ======================================================================
# VENDOR DEACTIVATE
# ======================================================================


@extend_schema(
    request=None,
    responses={
        status.HTTP_200_OK: response_schema(
            data_serializer=VendorDetailSerializer,
        ),
    },
    description=(
        "Deactivate a vendor. "
        "Staff access required."
    ),
)
class VendorDeactivateView(BaseAPIView):
    """
    Staff-only vendor deactivation.
    """

    permission_classes = [IsStaffUser]

    def post(
        self,
        request,
        vendor_id,
    ):
        vendor = VendorService.deactivate_vendor(
            vendor_id=vendor_id,
        )

        serializer = VendorDetailSerializer(
            vendor,
        )

        return self.success_response(
            message="Vendor deactivated successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
        )




# ======================================================================
# EVENT LIST / CREATE
# ======================================================================


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="search",
            type=OpenApiTypes.STR,
            required=False,
            description=(
                "Search by event title, description, venue, "
                "address, or vendor name."
            ),
        ),
        OpenApiParameter(
            name="vendor_id",
            type=OpenApiTypes.INT,
            required=False,
            description="Filter events by vendor ID.",
        ),
        OpenApiParameter(
            name="start_datetime",
            type=OpenApiTypes.DATETIME,
            required=False,
            description=(
                "Return events starting on or after this datetime."
            ),
        ),
        OpenApiParameter(
            name="end_datetime",
            type=OpenApiTypes.DATETIME,
            required=False,
            description=(
                "Return events ending on or before this datetime."
            ),
        ),
        OpenApiParameter(
            name="min_price",
            type=OpenApiTypes.DECIMAL,
            required=False,
            description="Minimum ticket price.",
        ),
        OpenApiParameter(
            name="max_price",
            type=OpenApiTypes.DECIMAL,
            required=False,
            description="Maximum ticket price.",
        ),
        OpenApiParameter(
            name="page",
            type=int,
            location=OpenApiParameter.QUERY,
            description="Page number.",
            required=False,
        ),
        OpenApiParameter(
            name="page_size",
            type=int,
            location=OpenApiParameter.QUERY,
            description="Number of results per page. Maximum 100.",
            required=False,
        ),
    ],
    request={
        "POST": EventCreateSerializer,
    },
    responses={
        status.HTTP_200_OK: response_schema(
            data_serializer=EventListSerializer,
            many=True,
        ),
        status.HTTP_201_CREATED: response_schema(
            data_serializer=EventDetailSerializer,
        ),
    },
    description=(
        "List events or create a new event. "
        "Customers can browse events. "
        "Staff can create events."
    ),
)
class EventListCreateView(BaseAPIView):
    """
    Event listing and creation.

    GET:
        Customer → active, upcoming events
        Staff    → all events

    POST:
        Staff only
    """

    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsStaffUser()]

        return super().get_permissions()


    def get(self, request):
        """
        List events with optional filters.

        Supported query parameters:

            search
            vendor_id
            start_datetime
            end_datetime
            min_price
            max_price
            page
            page_size
        """

        filter_serializer = EventFilterSerializer(
            data=request.query_params,
        )

        filter_serializer.is_valid(
            raise_exception=True,
        )

        filters = filter_serializer.validated_data

        if request.user.role == request.user.Role.STAFF:
            events = EventService.list_staff_events(
                staff_user=request.user,
                **filters,
            )
        else:
            events = EventService.list_customer_events(
                **filters,
            )

        paginator, page = self.paginate_queryset(events)

        if page is not None:
            serializer = EventListSerializer(
                page,
                many=True,
            )

            return self.paginated_success_response(
                paginator=paginator,
                data=serializer.data,
                message="Events retrieved successfully.",
                status_code=status.HTTP_200_OK,
            )

        serializer = EventListSerializer(
            events,
            many=True,
        )

        return self.success_response(
            data=serializer.data,
            message="Events retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )

    def post(self, request):
        """
        Create an event.

        Staff only.
        """

        serializer = EventCreateSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        event = EventService.create_event(
            staff_user=request.user,
            **serializer.validated_data,
        )

        response_serializer = EventDetailSerializer(
            event,
        )

        return self.success_response(
            message="Event created successfully.",
            data=response_serializer.data,
            status_code=status.HTTP_201_CREATED,
        )


# ======================================================================
# EVENT DETAIL / UPDATE
# ======================================================================


@extend_schema(
    responses={
        status.HTTP_200_OK: response_schema(
            data_serializer=EventDetailSerializer,
        ),
    },
    description=(
        "Retrieve detailed event information. "
        "Customers can retrieve publicly visible events. "
        "Staff can retrieve any event."
    ),
)
class EventDetailView(BaseAPIView):
    """
    Retrieve or partially update an event.

    GET:
        Customer → publicly visible events
        Staff    → any event

    PATCH:
        Staff only
    """

    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method == "PATCH":
            return [IsStaffUser()]

        return super().get_permissions()

    def get(self, request, event_id):
        """
        Retrieve event detail.
        """

        if request.user.role == request.user.Role.STAFF:
            event = EventService.get_event(
                event_id=event_id,
                staff_user=request.user,
            )
        else:
            event = EventService.get_event(
                event_id=event_id,
            )

        serializer = EventDetailSerializer(
            event,
        )

        return self.success_response(
            data=serializer.data,
            status_code=status.HTTP_200_OK,
        )

    @extend_schema(
        request=EventUpdateSerializer,
        responses={
            status.HTTP_200_OK: response_schema(
                data_serializer=EventDetailSerializer,
            ),
        },
        description=(
            "Partially update an event. "
            "Staff access required."
        ),
    )
    def patch(self, request, event_id):
        """
        Partially update an event.

        Staff only.
        """

        serializer = EventUpdateSerializer(
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        event = EventService.update_event(
            staff_user=request.user,
            event_id=event_id,
            **serializer.validated_data,
        )

        response_serializer = EventDetailSerializer(
            event,
        )

        return self.success_response(
            message="Event updated successfully.",
            data=response_serializer.data,
            status_code=status.HTTP_200_OK,
        )


# ======================================================================
# EVENT ACTIVATE
# ======================================================================


@extend_schema(
    request=None,
    responses={
        status.HTTP_200_OK: response_schema(
            data_serializer=EventDetailSerializer,
        ),
    },
    description=(
        "Activate an event. "
        "Staff access required."
    ),
)
class EventActivateView(BaseAPIView):
    """
    Staff-only event activation.
    """

    permission_classes = [IsStaffUser]

    def post(self, request, event_id):
        event = EventService.activate_event(
            staff_user=request.user,
            event_id=event_id,
        )

        serializer = EventDetailSerializer(
            event,
        )

        return self.success_response(
            message="Event activated successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
        )


# ======================================================================
# EVENT DEACTIVATE
# ======================================================================


@extend_schema(
    request=None,
    responses={
        status.HTTP_200_OK: response_schema(
            data_serializer=EventDetailSerializer,
        ),
    },
    description=(
        "Deactivate an event. "
        "Staff access required."
    ),
)
class EventDeactivateView(BaseAPIView):
    """
    Staff-only event deactivation.
    """

    permission_classes = [IsStaffUser]

    def post(self, request, event_id):
        event = EventService.deactivate_event(
            staff_user=request.user,
            event_id=event_id,
        )

        serializer = EventDetailSerializer(
            event,
        )

        return self.success_response(
            message="Event deactivated successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
        )