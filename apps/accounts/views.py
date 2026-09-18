from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated

from drf_spectacular.utils import extend_schema, OpenApiResponse ,OpenApiParameter

from config.exceptions import AuthenticationServiceError

from .base_views import BaseAPIView
from .cookies import (
    REFRESH_TOKEN_COOKIE,
    clear_auth_cookies,
    set_auth_cookies,
)
from .permissions import IsStaffUser
from .schemas import response_schema
from .serializers import (
    AuthUserDataSerializer,
    CustomerDetailSerializer,
    CustomerListSerializer,
    CustomerStatusSerializer,
    CustomerUpdateSerializer,
    LoginSerializer,
    RegisterSerializer,
    MeSerializer
)
from .services.auth_service import AuthService
from .services.customer_service import CustomerService


# ======================================================================
# AUTHENTICATION
# ======================================================================


@extend_schema(
    request=RegisterSerializer,
    responses={
        status.HTTP_201_CREATED: response_schema(
            data_serializer=AuthUserDataSerializer,
        ),
    },
    description="Register a new customer account.",
)
class RegisterView(BaseAPIView):
    """
    Register a new customer account.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        user = AuthService.register_customer(
            **serializer.validated_data
        )

        return self.success_response(
            message="Registration successful.",
            data={
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "role": user.role,
                }
            },
            status_code=status.HTTP_201_CREATED,
        )


@extend_schema(
    request=LoginSerializer,
    responses={
        status.HTTP_200_OK: response_schema(
            data_serializer=AuthUserDataSerializer,
        ),
    },
    description=(
        "Authenticate a user and set JWT authentication cookies."
    ),
)
class LoginView(BaseAPIView):
    """
    Authenticate a user and set JWT authentication cookies.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        result = AuthService.login(
            **serializer.validated_data
        )

        user = result["user"]

        response = self.success_response(
            message="Login successful.",
            data={
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "role": user.role,
                }
            },
            status_code=status.HTTP_200_OK,
        )

        set_auth_cookies(
            response,
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
        )

        return response


@extend_schema(
    request=None,
    responses={
        status.HTTP_200_OK: response_schema(
            data_serializer=AuthUserDataSerializer,
        ),
    },
    description=(
        "Refresh the access and refresh JWT cookies. "
        "The refresh token is read from the HttpOnly cookie."
    ),
)
class RefreshView(BaseAPIView):
    """
    Refresh the access and refresh JWT cookies.

    The refresh token is read from the HttpOnly cookie.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get(
            REFRESH_TOKEN_COOKIE
        )

        if not refresh_token:
            raise AuthenticationServiceError(
                "Refresh token is required.",
                code="REFRESH_TOKEN_REQUIRED",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        result = AuthService.refresh(
            refresh_token=refresh_token
        )

        response = self.success_response(
            message="Token refreshed successfully.",
            data={
                "user": {
                    "id": result["user"].id,
                    "email": result["user"].email,
                    "first_name": result["user"].first_name,
                    "last_name": result["user"].last_name,
                    "role": result["user"].role,
                }
            },
            status_code=status.HTTP_200_OK,
        )

        set_auth_cookies(
            response,
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
        )

        return response


@extend_schema(
    request=None,
    responses={
        status.HTTP_200_OK: response_schema(
            data_serializer=None,
        ),
    },
    description=(
        "Logout the current user by blacklisting the "
        "refresh token and clearing authentication cookies."
    ),
)
class LogoutView(BaseAPIView):
    """
    Logout the current user.

    The refresh token is read from the HttpOnly cookie,
    blacklisted by AuthService, and then both authentication
    cookies are removed.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.COOKIES.get(
            REFRESH_TOKEN_COOKIE
        )

        if not refresh_token:
            raise AuthenticationServiceError(
                "Refresh token is required.",
                code="REFRESH_TOKEN_REQUIRED",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        AuthService.logout(
            refresh_token=refresh_token
        )

        response = self.success_response(
            message="Logout successful.",
            status_code=status.HTTP_200_OK,
        )

        clear_auth_cookies(response)

        return response


# ======================================================================
# CUSTOMER MANAGEMENT
# ======================================================================


@extend_schema(
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
            description="Number of customers per page. Maximum 100.",
        ),
    ],
    responses={
        status.HTTP_200_OK: response_schema(
            data_serializer=CustomerListSerializer,
            many=True,
        ),
    },
    description="Return the list of customers. Staff access required.",
)
class CustomerListView(BaseAPIView):
    """
    Staff-only customer list.
    """

    permission_classes = [IsStaffUser]

    def get(self, request):
        customers = CustomerService.list_customers()

        paginator, page = self.paginate_queryset(customers)

        if page is not None:
            serializer = CustomerListSerializer(
                page,
                many=True,
            )

            return self.paginated_success_response(
                paginator=paginator,
                data=serializer.data,
                message="Customers retrieved successfully.",
                status_code=status.HTTP_200_OK,
            )

        serializer = CustomerListSerializer(
            customers,
            many=True,
        )

        return self.success_response(
            data=serializer.data,
            message="Customers retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )


@extend_schema(
    responses={
        status.HTTP_200_OK: response_schema(
            data_serializer=CustomerDetailSerializer,
        ),
    },
    description="Return detailed customer information.",
)
class CustomerDetailView(BaseAPIView):
    """
    Staff-only customer detail and update.
    """

    permission_classes = [IsStaffUser]

    def get(self, request, user_id):
        customer = CustomerService.get_customer(
            user_id=user_id
        )

        serializer = CustomerDetailSerializer(
            customer
        )

        return self.success_response(
            data=serializer.data,
            status_code=status.HTTP_200_OK,
        )

    @extend_schema(
        request=CustomerUpdateSerializer,
        responses={
            status.HTTP_200_OK: response_schema(
                data_serializer=CustomerDetailSerializer,
            ),
        },
        description="Update customer profile information.",
    )
    def patch(self, request, user_id):
        serializer = CustomerUpdateSerializer(
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True
        )

        customer = CustomerService.update_customer(
            user_id=user_id,
            **serializer.validated_data,
        )

        response_serializer = CustomerDetailSerializer(
            customer
        )

        return self.success_response(
            message="Customer updated successfully.",
            data=response_serializer.data,
            status_code=status.HTTP_200_OK,
        )


@extend_schema(
    responses={
        status.HTTP_200_OK: response_schema(
            data_serializer=CustomerStatusSerializer,
        ),
    },
    description="Activate a customer account. Staff access required.",
)
class CustomerActivateView(BaseAPIView):
    """
    Staff-only customer activation.
    """

    permission_classes = [IsStaffUser]

    def post(self, request, user_id):
        customer = CustomerService.activate_customer(
            user_id=user_id
        )

        serializer = CustomerStatusSerializer(
            customer
        )

        return self.success_response(
            message="Customer activated successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
        )


@extend_schema(
    responses={
        status.HTTP_200_OK: response_schema(
            data_serializer=CustomerStatusSerializer,
        ),
    },
    description="Deactivate a customer account. Staff access required.",
)
class CustomerDeactivateView(BaseAPIView):
    """
    Staff-only customer deactivation.
    """

    permission_classes = [IsStaffUser]

    def post(self, request, user_id):
        customer = CustomerService.deactivate_customer(
            user_id=user_id
        )

        serializer = CustomerStatusSerializer(
            customer
        )

        return self.success_response(
            message="Customer deactivated successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK,
        )




@extend_schema(
    summary="Get current authenticated user",
    description=(
        "Returns the profile of the user represented by the "
        "current authentication credentials."
    ),
    responses={
        200: OpenApiResponse(
            response=MeSerializer,
            description="Current user retrieved successfully.",
        ),
        401: OpenApiResponse(
            description="Authentication required.",
        ),
    },
)
class GetMeView(BaseAPIView):
    """
    Return the currently authenticated user's profile.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = MeSerializer(
            request.user
        )

        return self.success_response(
            data=serializer.data,
            message="Current user retrieved successfully.",
        )
