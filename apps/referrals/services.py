from collections import defaultdict

from django.db import transaction

from apps.accounts.models import User
from config.exceptions import (
    ReferralPlacementError,
    ReferralServiceError,
)

from .models import ReferralNode
from .repositories import ReferralRepository


class ReferralService:
    """
    Business logic for the referral system.

    Database queries belong to ReferralRepository.
    Referral rules and workflows belong here.
    """

    # ==================================================================
    # CREATE REFERRAL PLACEMENT
    # ==================================================================

    
    @staticmethod
    @transaction.atomic
    def create_placement(
        *,
        user: User,
        sponsor: User | None = None,
    ) -> ReferralNode:
        """
        Create the binary referral node for a user.

        If sponsor is None:
            The user becomes a root of a referral network.

        If sponsor exists:
            The user is placed into the sponsor's binary tree
            using BFS, preferring LEFT before RIGHT.

        The referral network root is locked during placement so
        concurrent registrations cannot choose the same empty slot.
        """

        # --------------------------------------------------------------
        # PREVENT DUPLICATE REFERRAL NODE
        # --------------------------------------------------------------

        existing_node = (
            ReferralRepository.get_node_by_user_id(
                user.id
            )
        )

        if existing_node:
            return existing_node

        # --------------------------------------------------------------
        # ROOT USER
        # --------------------------------------------------------------

        if sponsor is None:

            node = ReferralRepository.create_node(
                user_id=user.id,
            )

            ReferralRepository.create_closure(
                ancestor_id=node.id,
                descendant_id=node.id,
                depth=0,
            )

            return node

        # --------------------------------------------------------------
        # VALIDATE SPONSOR
        # --------------------------------------------------------------

        if sponsor.id == user.id:
            raise ReferralServiceError(
                "A user cannot refer themselves.",
                code="SELF_REFERRAL",
            )

        if not sponsor.is_active:
            raise ReferralServiceError(
                "The referring user is inactive.",
                code="INACTIVE_SPONSOR",
            )

        sponsor_node = (
            ReferralRepository.get_node_by_user_id(
                sponsor.id
            )
        )

        if sponsor_node is None:
            raise ReferralPlacementError(
                "The referring user does not have a referral node.",
                code="SPONSOR_NODE_NOT_FOUND",
                status_code=400,
            )

        # --------------------------------------------------------------
        # LOCK THE NETWORK ROOT
        # --------------------------------------------------------------
        #
        # This is the important concurrency protection.
        #
        # Every placement inside the same referral network must
        # acquire the same root lock before searching for a slot.
        #
        # Example:
        #
        #              A  <- locked
        #             / \
        #            B   C
        #
        # Registration 1 and Registration 2 cannot simultaneously
        # search and choose the same empty position.
        # --------------------------------------------------------------

        root_node = ReferralRepository.get_root_for_update(
            sponsor_node
        )

        if root_node is None:
            raise ReferralPlacementError(
                "The referral network root could not be determined.",
                code="REFERRAL_ROOT_NOT_FOUND",
                status_code=400,
            )

        # --------------------------------------------------------------
        # FIND BINARY PLACEMENT
        # --------------------------------------------------------------

        parent_id, position = (
            ReferralService._find_next_available_slot(
                sponsor_node
            )
        )

        # --------------------------------------------------------------
        # CREATE REFERRAL NODE
        # --------------------------------------------------------------

        node = ReferralRepository.create_node(
            user_id=user.id,
            parent_id=parent_id,
            position=position,
        )

        # --------------------------------------------------------------
        # CREATE CLOSURE RECORDS
        # --------------------------------------------------------------

        ReferralService._create_closure_records(
            node=node,
        )

        return node
    


    # ==================================================================
    # FIND NEXT BINARY SLOT
    # ==================================================================

    @staticmethod
    def _find_next_available_slot(
        root_node: ReferralNode,
    ) -> tuple[int, str]:
        """
        Find the first available binary slot using BFS.

        Traversal order:

            LEFT
            RIGHT

        Example:

                A
               / \
              B   C
             /
            D

        Next available slot:

            B -> RIGHT
        """

        current_level = [root_node.id]

        while current_level:

            children = (
                ReferralRepository
                .get_children_by_parent_ids(
                    current_level
                )
            )

            children_by_parent = defaultdict(dict)

            for child in children:
                children_by_parent[
                    child.parent_id
                ][child.position] = child.id

            next_level = []

            for parent_id in current_level:

                parent_children = (
                    children_by_parent.get(
                        parent_id,
                        {},
                    )
                )

                # LEFT has priority.
                if (
                    ReferralNode.Position.LEFT
                    not in parent_children
                ):
                    return (
                        parent_id,
                        ReferralNode.Position.LEFT,
                    )

                # RIGHT is checked second.
                if (
                    ReferralNode.Position.RIGHT
                    not in parent_children
                ):
                    return (
                        parent_id,
                        ReferralNode.Position.RIGHT,
                    )

                # Both positions are occupied.
                next_level.extend(
                    [
                        parent_children[
                            ReferralNode.Position.LEFT
                        ],
                        parent_children[
                            ReferralNode.Position.RIGHT
                        ],
                    ]
                )

            current_level = next_level

        raise ReferralPlacementError(
            "No available referral placement was found.",
            code="NO_AVAILABLE_PLACEMENT",
        )

    # ==================================================================
    # CREATE CLOSURE RECORDS
    # ==================================================================

    @staticmethod
    def _create_closure_records(
        *,
        node: ReferralNode,
    ) -> None:
        """
        Create closure records for a newly inserted node.

        Example:

                A
                |
                B
                |
                D

        Creates:

            D -> D    depth 0
            B -> D    depth 1
            A -> D    depth 2
        """

        # --------------------------------------------------------------
        # SELF RELATIONSHIP
        # --------------------------------------------------------------

        ReferralRepository.create_closure(
            ancestor_id=node.id,
            descendant_id=node.id,
            depth=0,
        )

        # --------------------------------------------------------------
        # ROOT HAS NO PARENT
        # --------------------------------------------------------------

        if node.parent_id is None:
            return

        # --------------------------------------------------------------
        # GET PARENT ANCESTOR CHAIN
        # --------------------------------------------------------------

        ancestor_links = (
            ReferralRepository.get_ancestor_links(
                node.parent
            )
        )

        # --------------------------------------------------------------
        # EXTEND ANCESTOR RELATIONSHIPS
        # --------------------------------------------------------------

        for link in ancestor_links:

            ReferralRepository.create_closure(
                ancestor_id=link.ancestor_id,
                descendant_id=node.id,
                depth=link.depth + 1,
            )

    # ==================================================================
    # GET TREE
    # ==================================================================

    @staticmethod
    def get_tree(
        *,
        user_id: int,
    ) -> dict:
        """
        Return the complete downline subtree rooted at the user.

        The requested user becomes the root of the returned subtree.
        """

        node = ReferralRepository.get_node_by_user_id(
            user_id
        )

        if node is None:
            raise ReferralServiceError(
                "Referral node not found.",
                code="REFERRAL_NODE_NOT_FOUND",
                status_code=404,
            )

        descendants = (
            ReferralRepository
            .get_descendants(node)
        )

        children_map = defaultdict(list)

        for link in descendants:

            # Skip self relationship.
            if link.depth == 0:
                continue

            descendant = link.descendant

            children_map[
                descendant.parent_id
            ].append(descendant)

        def build_node(
            current_node: ReferralNode,
        ) -> dict:

            children = children_map.get(
                current_node.id,
                [],
            )

            left_child = None
            right_child = None

            for child in children:

                if (
                    child.position
                    == ReferralNode.Position.LEFT
                ):
                    left_child = child

                elif (
                    child.position
                    == ReferralNode.Position.RIGHT
                ):
                    right_child = child

            return {
                "user_id": current_node.user_id,
                "email": current_node.user.email,
                "first_name": current_node.user.first_name,
                "last_name": current_node.user.last_name,
                "position": current_node.position,
                "left": (
                    build_node(left_child)
                    if left_child
                    else None
                ),
                "right": (
                    build_node(right_child)
                    if right_child
                    else None
                ),
            }

        return build_node(node)

    # ==================================================================
    # GET ROOT
    # ==================================================================

    @staticmethod
    def get_root(
        *,
        user_id: int,
    ) -> ReferralNode:
        """
        Find the root node of the network containing the user.
        """

        node = ReferralRepository.get_node_by_user_id(
            user_id
        )

        if node is None:
            raise ReferralServiceError(
                "Referral node not found.",
                code="REFERRAL_NODE_NOT_FOUND",
                status_code=404,
            )

        root = ReferralRepository.get_root_for_node(
            node
        )

        if root is None:
            raise ReferralServiceError(
                "Referral root could not be determined.",
                code="REFERRAL_ROOT_NOT_FOUND",
                status_code=404,
            )

        return root

    # ==================================================================
    # GET STATS
    # ==================================================================

    @staticmethod
    def get_stats(
        *,
        user_id: int,
    ) -> dict:
        """
        Return binary referral statistics for a user.
        """

        node = ReferralRepository.get_node_by_user_id(
            user_id
        )

        if node is None:
            raise ReferralServiceError(
                "Referral node not found.",
                code="REFERRAL_NODE_NOT_FOUND",
                status_code=404,
            )

        # --------------------------------------------------------------
        # TEAM COUNTS
        # --------------------------------------------------------------

        left_team_count = (
            ReferralRepository
            .get_left_team_count(node)
        )

        right_team_count = (
            ReferralRepository
            .get_right_team_count(node)
        )

        total_team_count = (
            left_team_count
            + right_team_count
        )

        # --------------------------------------------------------------
        # DIRECT BINARY CHILDREN
        # --------------------------------------------------------------

        direct_children = (
            ReferralRepository
            .get_direct_descendants(node)
        )

        direct_binary_children_count = (
            direct_children.count()
        )

        return {
            "user_id": user_id,
            "left_team_count": left_team_count,
            "right_team_count": right_team_count,
            "total_team_count": total_team_count,
            "direct_binary_children_count": (
                direct_binary_children_count
            ),
        }