"""Simplified utility functions for analytics and logging."""

from typing import Dict, Any, Optional
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def log_user_event(
    event_name: str,
    user_id: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """Log a user event.
    
    Args:
        event_name: Name of the event
        user_id: User ID if applicable
        metadata: Event-specific data
        
    Returns:
        True if logged successfully
    """
    try:
        # For now, just log to console
        # In production, this would create an AnalyticsEvent
        logger.info(
            f"User event: {event_name}",
            extra={
                'user_id': user_id,
                'metadata': metadata or {},
                'timestamp': timezone.now().isoformat()
            }
        )
        return True
    except Exception as e:
        logger.error(f"Failed to log user event {event_name}: {e}")
        return False


def log_analytics_event(
    event_type: str,
    event_name: str,
    user_id: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """Log an analytics event.
    
    Args:
        event_type: Type of event
        event_name: Specific name of the event
        user_id: User ID if applicable
        metadata: Event-specific data
        
    Returns:
        True if logged successfully
    """
    try:
        # For now, just log to console
        logger.info(
            f"Analytics event: {event_type}.{event_name}",
            extra={
                'event_type': event_type,
                'event_name': event_name,
                'user_id': user_id,
                'metadata': metadata or {},
                'timestamp': timezone.now().isoformat()
            }
        )
        return True
    except Exception as e:
        logger.error(f"Failed to log analytics event {event_name}: {e}")
        return False
