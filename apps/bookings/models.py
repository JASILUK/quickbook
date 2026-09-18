from django.conf import settings
from django.db import models


class Booking(models.Model):
    """
    Represents a customer's booking for an event.

    Seat availability is maintained on Event.
    Booking records the quantity reserved by the customer.
    """

    class Status(models.TextChoices):
        CONFIRMED = "CONFIRMED", "Confirmed"
        CANCELLED = "CANCELLED", "Cancelled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="bookings",
    )

    event = models.ForeignKey(
        "events.Event",
        on_delete=models.PROTECT,
        related_name="bookings",
    )

    quantity = models.PositiveIntegerField()

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CONFIRMED,
    )

    booked_at = models.DateTimeField(
        auto_now_add=True,
    )

    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-booked_at"]

        indexes = [
            models.Index(
                fields=["user", "status"],
                name="idx_booking_user_status",
            ),
            models.Index(
                fields=["event", "status"],
                name="idx_booking_event_status",
            ),
        ]

    def __str__(self):
        return (
            f"Booking #{self.id} - "
            f"{self.user.email} - "
            f"{self.event.title}"
        )