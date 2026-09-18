from rest_framework import serializers

from drf_spectacular.utils import inline_serializer


def response_schema(
    *,
    data_serializer=None,
    many=False,
):
    """
    Build the common QuickBook API response schema.

    Successful responses follow:

        {
            "success": true,
            "message": "...",
            "data": ...
        }

    The data field is optional for endpoints such as logout.
    """

    fields = {
        "success": serializers.BooleanField(),
        "message": serializers.CharField(),
    }

    if data_serializer is not None:
        if many:
            data_field = data_serializer(many=True)
        else:
            data_field = data_serializer()

        fields["data"] = data_field

    return inline_serializer(
        name=(
            f"{data_serializer.__name__}Response"
            if data_serializer is not None
            else "SuccessResponse"
        ),
        fields=fields,
    )