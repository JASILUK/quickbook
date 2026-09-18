from django.contrib import admin

from .models import ReferralNode, ReferralClosure


@admin.register(ReferralNode)
class ReferralNodeAdmin(admin.ModelAdmin):

    list_display = [
        "id",
        "user",
        "parent",
        "position",
        "created_at",
    ]

    list_filter = [
        "position",
        "created_at",
    ]

    search_fields = [
        "user__email",
        "user__first_name",
        "user__last_name",
    ]

    list_select_related = [
        "user",
        "parent",
    ]

    readonly_fields = [
        "created_at",
    ]


@admin.register(ReferralClosure)
class ReferralClosureAdmin(admin.ModelAdmin):

    list_display = [
        "id",
        "ancestor",
        "descendant",
        "depth",
        "created_at",
    ]

    list_filter = [
        "depth",
        "created_at",
    ]

    search_fields = [
        "ancestor__user__email",
        "descendant__user__email",
    ]

    list_select_related = [
        "ancestor",
        "descendant",
    ]

    readonly_fields = [
        "created_at",
    ]