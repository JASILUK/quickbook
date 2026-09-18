from django.db import models
from django.db.models import Q


class ReferralNode(models.Model):

    class Position(models.TextChoices):
        LEFT = "L", "Left"
        RIGHT = "R", "Right"

    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="referral_node",
    )

    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="children",
    )

    position = models.CharField(
        max_length=1,
        choices=Position.choices,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["parent", "position"],
                name="unique_referral_parent_position",
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        parent__isnull=True,
                        position__isnull=True,
                    )
                    | Q(
                        parent__isnull=False,
                        position__isnull=False,
                    )
                ),
                name="valid_referral_parent_position",
            ),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.position or 'ROOT'}"



class ReferralClosure(models.Model):

    ancestor = models.ForeignKey(
        ReferralNode,
        on_delete=models.CASCADE,
        related_name="descendant_links",
    )

    descendant = models.ForeignKey(
        ReferralNode,
        on_delete=models.CASCADE,
        related_name="ancestor_links",
    )

    depth = models.PositiveIntegerField()

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["ancestor", "descendant"],
                name="unique_referral_ancestor_descendant",
            ),
        ]

        indexes = [
            models.Index(
                fields=["ancestor"],
                name="idx_closure_ancestor",
            ),
            models.Index(
                fields=["descendant"],
                name="idx_closure_descendant",
            ),
        ]

    def __str__(self):
        return (
            f"{self.ancestor.user.email}"
            f" -> "
            f"{self.descendant.user.email}"
            f" ({self.depth})"
        )