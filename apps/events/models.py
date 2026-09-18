from django.db import models
from django.db.models import Q


class Vendor(models.Model):
    """
    Represents a business or organizer that provides events.
    """

    name = models.CharField(
        max_length=200,
    )

    email = models.EmailField(
        blank=True,
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
    )

    address = models.TextField(
        blank=True,
    )

    description = models.TextField(
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="created_vendors",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Event(models.Model):
    """
    Represents a bookable event.
    """

    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.PROTECT,
        related_name="events",
    )

    title = models.CharField(
        max_length=200,
    )

    description = models.TextField(
        blank=True,
    )

    venue_name = models.CharField(
        max_length=200,
    )

    address = models.TextField()

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )

    start_datetime = models.DateTimeField()

    end_datetime = models.DateTimeField()

    total_seats = models.PositiveIntegerField()

    available_seats = models.PositiveIntegerField()

    ticket_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="created_events",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["start_datetime"]

        constraints = [
            models.CheckConstraint(
                condition=Q(total_seats__gt=0),
                name="event_total_seats_positive",
            ),
            models.CheckConstraint(
                condition=Q(
                    available_seats__gte=0,
                ),
                name="event_available_seats_non_negative",
            ),
            models.CheckConstraint(
                condition=Q(
                    available_seats__lte=models.F("total_seats"),
                ),
                name="event_available_seats_lte_total",
            ),
            models.CheckConstraint(
                condition=Q(
                    end_datetime__gt=models.F("start_datetime"),
                ),
                name="event_end_after_start",
            ),
            models.CheckConstraint(
                condition=Q(
                    ticket_price__gte=0,
                ),
                name="event_ticket_price_non_negative",
            ),
        ]

    def __str__(self):
        return self.title

