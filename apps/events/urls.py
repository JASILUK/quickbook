from django.urls import path

from apps.events.views import (
    EventActivateView,
    EventDeactivateView,
    EventDetailView,
    EventListCreateView,
    VendorActivateView,
    VendorDeactivateView,
    VendorDetailView,
    VendorListCreateView,
)


urlpatterns = [
    # ============================================================
    # VENDORS
    # ============================================================

    path(
        "vendors/",
        VendorListCreateView.as_view(),
        name="vendor-list-create",
    ),

    path(
        "vendors/<int:vendor_id>/",
        VendorDetailView.as_view(),
        name="vendor-detail",
    ),

    path(
        "vendors/<int:vendor_id>/activate/",
        VendorActivateView.as_view(),
        name="vendor-activate",
    ),

    path(
        "vendors/<int:vendor_id>/deactivate/",
        VendorDeactivateView.as_view(),
        name="vendor-deactivate",
    ),

    # ============================================================
    # EVENTS
    # ============================================================

    path(
        "",
        EventListCreateView.as_view(),
        name="event-list-create",
    ),

    path(
        "<int:event_id>/",
        EventDetailView.as_view(),
        name="event-detail",
    ),

    path(
        "<int:event_id>/activate/",
        EventActivateView.as_view(),
        name="event-activate",
    ),

    path(
        "<int:event_id>/deactivate/",
        EventDeactivateView.as_view(),
        name="event-deactivate",
    ),
]