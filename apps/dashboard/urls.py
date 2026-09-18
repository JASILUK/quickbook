from django.urls import path

from apps.dashboard.views import (
    DashboardHomeView,

    DashboardCustomerListView,
    DashboardCustomerDetailView,
    DashboardCustomerUpdateView,
    DashboardCustomerActivateView,
    DashboardCustomerDeactivateView,

    DashboardVendorListView,
    DashboardVendorCreateView,
    DashboardVendorDetailView,
    DashboardVendorUpdateView,
    DashboardVendorActivateView,
    DashboardVendorDeactivateView,

    DashboardEventListView,
    DashboardEventCreateView,
    DashboardEventDetailView,
    DashboardEventUpdateView,
    DashboardEventActivateView,
    DashboardEventDeactivateView,

    DashboardBookingCancelView,
    DashboardBookingDetailView,
    DashboardBookingListView
)


app_name = "dashboard"


urlpatterns = [
    path(
        "",
        DashboardHomeView.as_view(),
        name="home",
    ),

    # Customers
    path(
        "customers/",
        DashboardCustomerListView.as_view(),
        name="customers",
    ),
    path(
        "customers/<int:customer_id>/",
        DashboardCustomerDetailView.as_view(),
        name="customer-detail",
    ),
    path(
        "customers/<int:user_id>/edit/",
        DashboardCustomerUpdateView.as_view(),
        name="customer-edit",
    ),
    path(
        "customers/<int:user_id>/activate/",
        DashboardCustomerActivateView.as_view(),
        name="customer-activate",
    ),
    path(
        "customers/<int:user_id>/deactivate/",
        DashboardCustomerDeactivateView.as_view(),
        name="customer-deactivate",
    ),

    # Vendors
    path(
        "vendors/",
        DashboardVendorListView.as_view(),
        name="vendors",
    ),
    path(
        "vendors/create/",
        DashboardVendorCreateView.as_view(),
        name="vendor-create",
    ),
    path(
        "vendors/<int:vendor_id>/",
        DashboardVendorDetailView.as_view(),
        name="vendor-detail",
    ),
    path(
        "vendors/<int:vendor_id>/edit/",
        DashboardVendorUpdateView.as_view(),
        name="vendor-edit",
    ),
    path(
        "vendors/<int:vendor_id>/activate/",
        DashboardVendorActivateView.as_view(),
        name="vendor-activate",
    ),
    path(
        "vendors/<int:vendor_id>/deactivate/",
        DashboardVendorDeactivateView.as_view(),
        name="vendor-deactivate",
    ),

    # Events
    path(
        "events/",
        DashboardEventListView.as_view(),
        name="events",
    ),
    path(
        "events/create/",
        DashboardEventCreateView.as_view(),
        name="event-create",
    ),
    path(
        "events/<int:event_id>/",
        DashboardEventDetailView.as_view(),
        name="event-detail",
    ),
    path(
        "events/<int:event_id>/edit/",
        DashboardEventUpdateView.as_view(),
        name="event-edit",
    ),
    path(
        "events/<int:event_id>/activate/",
        DashboardEventActivateView.as_view(),
        name="event-activate",
    ),
    path(
        "events/<int:event_id>/deactivate/",
        DashboardEventDeactivateView.as_view(),
        name="event-deactivate",
    ),

    path(
        "bookings/",
        DashboardBookingListView.as_view(),
        name="bookings",
    ),

    path(
        "bookings/<int:booking_id>/",
        DashboardBookingDetailView.as_view(),
        name="booking-detail",
    ),

    path(
        "bookings/<int:booking_id>/cancel/",
        DashboardBookingCancelView.as_view(),
        name="booking-cancel",
    ),
]