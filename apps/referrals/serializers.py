from rest_framework import serializers


class ReferralTreeSerializer(serializers.Serializer):
    """
    Represents a referral node and its complete binary subtree.

    The tree is returned recursively:
        user
        ├── left
        └── right
    """

    user_id = serializers.IntegerField(
        read_only=True,
    )

    email = serializers.EmailField(
        read_only=True,
    )

    first_name = serializers.CharField(
        read_only=True,
    )

    last_name = serializers.CharField(
        read_only=True,
    )

    position = serializers.CharField(
        read_only=True,
        allow_null=True,
    )

    left = serializers.SerializerMethodField()

    right = serializers.SerializerMethodField()

    def get_left(self, obj):
        left_node = obj.get("left")

        if left_node is None:
            return None

        return ReferralTreeSerializer(
            left_node,
            context=self.context,
        ).data

    def get_right(self, obj):
        right_node = obj.get("right")

        if right_node is None:
            return None

        return ReferralTreeSerializer(
            right_node,
            context=self.context,
        ).data


class ReferralRootSerializer(serializers.Serializer):
    """
    Represents the root user of a referral network.
    """

    user_id = serializers.IntegerField(
        read_only=True,
    )

    email = serializers.EmailField(
        read_only=True,
    )

    first_name = serializers.CharField(
        read_only=True,
    )

    last_name = serializers.CharField(
        read_only=True,
    )

    position = serializers.CharField(
        read_only=True,
        allow_null=True,
    )


class ReferralStatsSerializer(serializers.Serializer):
    """
    Referral statistics for a user.
    """

    user_id = serializers.IntegerField(
        read_only=True,
    )

    left_team_count = serializers.IntegerField(
        read_only=True,
    )

    right_team_count = serializers.IntegerField(
        read_only=True,
    )

    total_team_count = serializers.IntegerField(
        read_only=True,
    )

    direct_binary_children_count = serializers.IntegerField(
        read_only=True,
    )

