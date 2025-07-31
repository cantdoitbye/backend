"""
Feed Algorithm Metrics and Monitoring Utilities

This module handles all metrics, logging, and performance monitoring
for the feed algorithm implementation.
"""

import time
import logging
from typing import Dict, Any, List
from neomodel import db
from auth_manager.models import Users

logger = logging.getLogger(__name__)


def log_feed_metrics(user_id: str, original_count: int, final_count: int, 
                    algorithm_time: float, total_time: float):
    """
    Log detailed metrics for feed performance monitoring.
    
    Args:
        user_id: User identifier
        original_count: Number of items before algorithm
        final_count: Number of items after algorithm
        algorithm_time: Time spent in algorithm processing
        total_time: Total resolver execution time
    """
    try:
        logger.info(f"FEED_METRICS: user={user_id}, original={original_count}, "
                   f"final={final_count}, algo_time={algorithm_time:.3f}s, "
                   f"total_time={total_time:.3f}s")
        
        # Optional: Store metrics in database for analytics
        # FeedMetrics.objects.create(
        #     user_id=user_id,
        #     original_count=original_count,
        #     final_count=final_count,
        #     algorithm_time=algorithm_time,
        #     total_time=total_time,
        #     timestamp=timezone.now()
        # )
        
    except Exception as e:
        logger.error(f"Error logging feed metrics: {e}")


def monitor_feed_performance(func):
    """
    Decorator to monitor feed performance and log metrics.
    
    Usage:
        @monitor_feed_performance
        def resolve_my_feed_test(self, info, **kwargs):
            # resolver implementation
    """
    def wrapper(self, info, *args, **kwargs):
        start_time = time.time()
        user_id = info.context.payload.get('user_id', 'unknown')
        
        try:
            result = func(self, info, *args, **kwargs)
            duration = time.time() - start_time
            
            logger.info(f"PERFORMANCE: {func.__name__} completed for user {user_id} "
                       f"in {duration:.3f}s, returned {len(result) if result else 0} items")
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"PERFORMANCE: {func.__name__} failed for user {user_id} "
                        f"after {duration:.3f}s with error: {e}")
            raise
    
    return wrapper


class FeedPerformanceTracker:
    """Class for tracking feed performance across multiple requests."""
    
    def __init__(self):
        self.metrics = []
    
    def record_performance(self, user_id: str, duration: float, item_count: int):
        """Record performance metrics for analysis."""
        self.metrics.append({
            'user_id': user_id,
            'duration': duration,
            'item_count': item_count,
            'timestamp': time.time()
        })
    
    def get_average_performance(self) -> Dict[str, float]:
        """Get average performance metrics."""
        if not self.metrics:
            return {}
        
        avg_duration = sum(m['duration'] for m in self.metrics) / len(self.metrics)
        avg_items = sum(m['item_count'] for m in self.metrics) / len(self.metrics)
        
        return {
            'average_duration': avg_duration,
            'average_items': avg_items,
            'total_requests': len(self.metrics)
        }