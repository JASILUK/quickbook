from django.urls import path

from .views import (
    CustomerActivateView,
    CustomerDeactivateView,
    CustomerDetailView,
    CustomerListView,
    LoginView,
    LogoutView,
    RefreshView,
    RegisterView,
    GetMeView
)


app_name = "accounts"


urlpatterns = [
    # ==================================================================
    # AUTHENTICATION
    # ==================================================================

    path(
        "register/",
        RegisterView.as_view(),
        name="register",
    ),

    path(
        "login/",
        LoginView.as_view(),
        name="login",
    ),

    path(
        "refresh/",
        RefreshView.as_view(),
        name="refresh",
    ),

    path(
        "logout/",
        LogoutView.as_view(),
        name="logout",
    ),

    path(
        "me/",
        GetMeView.as_view(),
        name="me",
    ),

    # ==================================================================
    # STAFF CUSTOMER MANAGEMENT
    # ==================================================================

    path(
        "customers/",
        CustomerListView.as_view(),
        name="customer-list",
    ),

    path(
        "customers/<int:user_id>/",
        CustomerDetailView.as_view(),
        name="customer-detail",
    ),

    path(
        "customers/<int:user_id>/activate/",
        CustomerActivateView.as_view(),
        name="customer-activate",
    ),

    path(
        "customers/<int:user_id>/deactivate/",
        CustomerDeactivateView.as_view(),
        name="customer-deactivate",
    ),
]