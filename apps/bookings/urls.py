from django.urls import path

from apps.bookings.views import (
    BookingCancelView,
    BookingDetailView,
    BookingListCreateView,
)


urlpatterns = [
    path(
        "",
        BookingListCreateView.as_view(),
        name="booking-list-create",
    ),
    path(
        "<int:booking_id>/",
        BookingDetailView.as_view(),
        name="booking-detail",
    ),
    path(
        "<int:booking_id>/cancel/",
        BookingCancelView.as_view(),
        name="booking-cancel",
    ),
]