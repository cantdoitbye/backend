# opportunity/utils/__init__.py

"""
Opportunity Utilities Package

This package contains utility functions for opportunity management including:
- Matrix room creation and management
- Opportunity data synchronization with Matrix
- User invitations to opportunity rooms
- Helper functions for opportunity operations
"""

from .create_opportunity_matrix_room import create_opportunity_room
from .matrix_opportunity_manager import set_opportunity_room_data, update_opportunity_room_avatar
from .opportunity_decorator import handle_graphql_opportunity_errors

from .redis_helper import (
    increment_opportunity_like_count,
    increment_opportunity_comment_count,
    increment_opportunity_share_count,
    increment_opportunity_view_count,
    get_opportunity_engagement_counts,
    clear_opportunity_engagement_cache
)

__all__ = [
    'create_opportunity_room',
    'set_opportunity_room_data',
    'update_opportunity_room_avatar',
    'delete_opportunity_room_data',
    'handle_graphql_opportunity_errors',
    'increment_opportunity_like_count',
    'increment_opportunity_comment_count',
    'increment_opportunity_share_count',
    'increment_opportunity_view_count',
    'get_opportunity_engagement_counts',
    'clear_opportunity_engagement_cache',
]
