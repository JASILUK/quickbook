from django.db.models import QuerySet

from .models import ReferralClosure, ReferralNode


class ReferralRepository:
    """
    Database operations for the referral system.

    Business rules and placement logic belong in the service layer.
    """

    # ------------------------------------------------------------------
    # NODE QUERIES
    # ------------------------------------------------------------------

    @staticmethod
    def get_node_by_user_id(
        user_id: int,
    ) -> ReferralNode | None:
        return (
            ReferralNode.objects
            .select_related("user")
            .filter(user_id=user_id)
            .first()
        )

    @staticmethod
    def get_node_by_id(
        node_id: int,
    ) -> ReferralNode | None:
        return (
            ReferralNode.objects
            .select_related("user")
            .filter(id=node_id)
            .first()
        )

    @staticmethod
    def get_root_node() -> ReferralNode | None:
        return (
            ReferralNode.objects
            .select_related("user")
            .filter(parent__isnull=True)
            .first()
        )

    @staticmethod
    def get_root_for_node(
        node: ReferralNode,
    ) -> ReferralNode | None:
        """
        Find the root of the referral network containing this node.
        """

        root_link = (
            ReferralClosure.objects
            .select_related("ancestor__user")
            .filter(
                descendant=node,
                depth__gt=0,
            )
            .order_by("-depth")
            .first()
        )

        if root_link:
            return root_link.ancestor

        # The node itself is the root.
        if node.parent_id is None:
            return node

        return None


    @staticmethod
    def get_root_for_update(
        node: ReferralNode,
    ) -> ReferralNode | None:
        """
        Find and lock the root node of this referral network.

        Must be called inside transaction.atomic().
        """

        root_link = (
            ReferralClosure.objects
            .filter(
                descendant=node,
                depth__gt=0,
            )
            .order_by("-depth")
            .first()
        )

        if root_link:
            return (
                ReferralNode.objects
                .select_for_update()
                .select_related("user")
                .filter(id=root_link.ancestor_id)
                .first()
            )

        if node.parent_id is None:
            return (
                ReferralNode.objects
                .select_for_update()
                .select_related("user")
                .filter(id=node.id)
                .first()
            )

        return None

    # ------------------------------------------------------------------
    # CHILDREN / PLACEMENT QUERIES
    # ------------------------------------------------------------------

    @staticmethod
    def get_children(
        node: ReferralNode,
    ) -> QuerySet[ReferralNode]:
        """
        Get direct binary children of a node.
        """

        return (
            ReferralNode.objects
            .select_related("user")
            .filter(parent=node)
            .order_by("position")
        )

    @staticmethod
    def get_children_by_parent_ids(
        parent_ids: list[int],
    ) -> QuerySet[ReferralNode]:
        """
        Get children for multiple parents.

        Used by BFS placement to avoid one query per parent.
        """

        if not parent_ids:
            return ReferralNode.objects.none()

        return (
            ReferralNode.objects
            .select_related("user")
            .filter(parent_id__in=parent_ids)
            .order_by("parent_id", "position")
        )

    @staticmethod
    def get_child_at_position(
        parent: ReferralNode,
        position: str,
    ) -> ReferralNode | None:
        """
        Get a specific LEFT or RIGHT child.
        """

        return (
            ReferralNode.objects
            .select_related("user")
            .filter(
                parent=parent,
                position=position,
            )
            .first()
        )

    @staticmethod
    def create_node(
        *,
        user_id: int,
        parent_id: int | None = None,
        position: str | None = None,
    ) -> ReferralNode:
        """
        Create a referral node.
        """

        return ReferralNode.objects.create(
            user_id=user_id,
            parent_id=parent_id,
            position=position,
        )

    # ------------------------------------------------------------------
    # CLOSURE QUERIES
    # ------------------------------------------------------------------

    @staticmethod
    def get_ancestors(
        node: ReferralNode,
    ) -> QuerySet[ReferralClosure]:
        """
        Get all ancestors of a node, including itself at depth 0.
        """

        return (
            ReferralClosure.objects
            .select_related("ancestor__user")
            .filter(descendant=node)
            .order_by("depth")
        )

    @staticmethod
    def get_descendants(
        node: ReferralNode,
    ) -> QuerySet[ReferralClosure]:
        """
        Get the complete subtree below a node,
        including the node itself at depth 0.
        """

        return (
            ReferralClosure.objects
            .select_related("descendant__user")
            .filter(ancestor=node)
            .order_by("depth", "descendant_id")
        )

    @staticmethod
    def get_direct_descendants(
        node: ReferralNode,
    ) -> QuerySet[ReferralClosure]:
        """
        Get direct binary children using closure depth = 1.
        """

        return (
            ReferralClosure.objects
            .select_related("descendant__user")
            .filter(
                ancestor=node,
                depth=1,
            )
            .order_by("descendant__position")
        )

    @staticmethod
    def get_descendant_count(
        node: ReferralNode,
    ) -> int:
        """
        Count all descendants below the node.

        The node itself is excluded.
        """

        return (
            ReferralClosure.objects
            .filter(
                ancestor=node,
                depth__gt=0,
            )
            .count()
        )

    # ------------------------------------------------------------------
    # TEAM COUNTS
    # ------------------------------------------------------------------

    @staticmethod
    def get_left_team_count(
        node: ReferralNode,
    ) -> int:
        """
        Count everyone in the LEFT subtree.

        Includes the direct LEFT child.
        """

        left_child = (
            ReferralNode.objects
            .filter(
                parent=node,
                position=ReferralNode.Position.LEFT,
            )
            .first()
        )

        if not left_child:
            return 0

        return (
            ReferralClosure.objects
            .filter(
                ancestor=left_child,
                depth__gt=0,
            )
            .count()
            + 1
        )

    @staticmethod
    def get_right_team_count(
        node: ReferralNode,
    ) -> int:
        """
        Count everyone in the RIGHT subtree.

        Includes the direct RIGHT child.
        """

        right_child = (
            ReferralNode.objects
            .filter(
                parent=node,
                position=ReferralNode.Position.RIGHT,
            )
            .first()
        )

        if not right_child:
            return 0

        return (
            ReferralClosure.objects
            .filter(
                ancestor=right_child,
                depth__gt=0,
            )
            .count()
            + 1
        )

    # ------------------------------------------------------------------
    # CLOSURE CREATION
    # ------------------------------------------------------------------

    @staticmethod
    def create_closure(
        *,
        ancestor_id: int,
        descendant_id: int,
        depth: int,
    ) -> ReferralClosure:
        """
        Create one ancestor -> descendant closure record.
        """

        return ReferralClosure.objects.create(
            ancestor_id=ancestor_id,
            descendant_id=descendant_id,
            depth=depth,
        )

    @staticmethod
    def get_ancestor_links(
        node: ReferralNode,
    ) -> list[ReferralClosure]:
        """
        Get all closure records where this node is the descendant.

        Includes the node's own depth-0 record.
        """

        return list(
            ReferralClosure.objects
            .filter(descendant=node)
            .order_by("depth")
        )