# vibe_manager/services/vibe_activity_service.py

from django.contrib.auth.models import User
from user_activity.models import VibeActivity
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class VibeActivityService:
    """
    Service for tracking vibe-related activities.
    
    This service handles all vibe activity tracking including creation, sending,
    receiving, and other vibe-related interactions. It provides a centralized
    way to record user activities related to the vibe system.
    
    The service is designed to be:
    - Thread-safe for concurrent operations
    - Error-resilient with proper exception handling
    - Flexible to support different vibe types and activities
    - Optimized for performance with minimal database overhead
    """
    
    @staticmethod
    def track_vibe_creation(user, vibe_data, success=True, error_message=None, **kwargs):
        """
        Track vibe creation activity.
        
        Records when a user creates a new vibe, including all relevant
        metadata about the vibe and the creation context.
        
        Args:
            user: User object or user_id who created the vibe
            vibe_data: Dictionary containing vibe information
                - vibe_id: Unique identifier of the created vibe
                - vibe_name: Name of the vibe
                - vibe_type: Type of vibe (main, individual, community, etc.)
                - category: Vibe category
                - iq, aq, sq, hq: Score weights
            success: Boolean indicating if creation was successful
            error_message: Error message if creation failed
            **kwargs: Additional metadata (ip_address, user_agent, etc.)
            
        Returns:
            VibeActivity: Created activity record or None if failed
            
        Example:
            >>> vibe_data = {
            ...     'vibe_id': 'vibe_123',
            ...     'vibe_name': 'Positive Energy',
            ...     'vibe_type': 'main',
            ...     'category': 'motivational',
            ...     'iq': 3.0, 'aq': 2.5, 'sq': 3.5, 'hq': 2.8
            ... }
            >>> activity = VibeActivityService.track_vibe_creation(
            ...     user=request.user,
            ...     vibe_data=vibe_data,
            ...     ip_address=request.META.get('REMOTE_ADDR')
            ... )
        """
        try:
            # Handle user_id if passed instead of User object
            if isinstance(user, str):
                user = User.objects.get(id=user)
            elif hasattr(user, 'user_id'):
                # Handle Neo4j Users model
                user = User.objects.get(id=user.user_id)
            
            # Extract vibe information
            vibe_id = vibe_data.get('vibe_id') or vibe_data.get('uid')
            vibe_name = vibe_data.get('vibe_name') or vibe_data.get('name')
            vibe_type = vibe_data.get('vibe_type', 'main')
            category = vibe_data.get('category')
            
            # Create metadata with vibe scoring information
            metadata = {
                'iq_weight': vibe_data.get('iq'),
                'aq_weight': vibe_data.get('aq'),
                'sq_weight': vibe_data.get('sq'),
                'hq_weight': vibe_data.get('hq'),
                'description': vibe_data.get('description'),
                'sub_category': vibe_data.get('subCategory'),
                'popularity': vibe_data.get('popularity', 0)
            }
            
            # Add any additional metadata
            metadata.update(kwargs.get('metadata', {}))
            
            # Create activity record
            activity = VibeActivity.objects.create(
                user=user,
                activity_type='vibe_create',
                vibe_type=vibe_type,
                vibe_id=str(vibe_id),
                vibe_name=vibe_name,
                vibe_category=category,
                success=success,
                error_message=error_message,
                ip_address=kwargs.get('ip_address'),
                user_agent=kwargs.get('user_agent'),
                metadata=metadata
            )
            
            logger.info(f"Tracked vibe creation: {user.username} created {vibe_name} ({vibe_id})")
            return activity
            
        except Exception as e:
            logger.error(f"Failed to track vibe creation: {str(e)}")
            return None
    
    @staticmethod
    def track_vibe_sending(sender, receiver_id, vibe_data, vibe_score, 
                          score_impacts=None, success=True, error_message=None, **kwargs):
        """
        Track vibe sending activity.
        
        Records when a user sends a vibe to another user, including
        score impacts and interaction context.
        
        Args:
            sender: User object who is sending the vibe
            receiver_id: ID of the user receiving the vibe
            vibe_data: Dictionary containing vibe information
            vibe_score: Score value for this vibe interaction
            score_impacts: Dictionary with score impact values
                - iq_impact, aq_impact, sq_impact, hq_impact
            success: Boolean indicating if sending was successful
            error_message: Error message if sending failed
            **kwargs: Additional metadata
            
        Returns:
            tuple: (sender_activity, receiver_activity) or (None, None) if failed
        """
        try:
            # Handle user_id if passed instead of User object
            if isinstance(sender, str):
                sender = User.objects.get(id=sender)
            elif hasattr(sender, 'user_id'):
                # Handle Neo4j Users model
                sender = User.objects.get(id=sender.user_id)
            
            # Extract vibe information
            vibe_id = vibe_data.get('vibe_id') or vibe_data.get('uid')
            vibe_name = vibe_data.get('vibe_name') or vibe_data.get('name')
            vibe_type = vibe_data.get('vibe_type', 'main')
            category = vibe_data.get('category')
            
            # Create metadata
            metadata = {
                'vibe_weights': {
                    'iq': vibe_data.get('iq'),
                    'aq': vibe_data.get('aq'),
                    'sq': vibe_data.get('sq'),
                    'hq': vibe_data.get('hq')
                },
                'interaction_context': 'vibe_send'
            }
            metadata.update(kwargs.get('metadata', {}))
            
            # Extract score impacts if provided
            iq_impact = score_impacts.get('iq_impact') if score_impacts else None
            aq_impact = score_impacts.get('aq_impact') if score_impacts else None
            sq_impact = score_impacts.get('sq_impact') if score_impacts else None
            hq_impact = score_impacts.get('hq_impact') if score_impacts else None
            
            # Track sender activity
            sender_activity = VibeActivity.objects.create(
                user=sender,
                activity_type='vibe_send',
                vibe_type=vibe_type,
                vibe_id=str(vibe_id),
                vibe_name=vibe_name,
                vibe_category=category,
                target_user_id=str(receiver_id),
                vibe_score=vibe_score,
                iq_impact=iq_impact,
                aq_impact=aq_impact,
                sq_impact=sq_impact,
                hq_impact=hq_impact,
                success=success,
                error_message=error_message,
                ip_address=kwargs.get('ip_address'),
                user_agent=kwargs.get('user_agent'),
                metadata=metadata
            )
            
            # Track receiver activity if successful
            receiver_activity = None
            if success:
                try:
                    receiver = User.objects.get(id=receiver_id)
                    receiver_metadata = metadata.copy()
                    receiver_metadata['interaction_context'] = 'vibe_receive'
                    receiver_metadata['sender_id'] = str(sender.id)
                    
                    receiver_activity = VibeActivity.objects.create(
                        user=receiver,
                        activity_type='vibe_receive',
                        vibe_type=vibe_type,
                        vibe_id=str(vibe_id),
                        vibe_name=vibe_name,
                        vibe_category=category,
                        target_user_id=str(sender.id),
                        vibe_score=vibe_score,
                        iq_impact=iq_impact,
                        aq_impact=aq_impact,
                        sq_impact=sq_impact,
                        hq_impact=hq_impact,
                        success=True,
                        metadata=receiver_metadata
                    )
                except User.DoesNotExist:
                    logger.warning(f"Receiver user {receiver_id} not found for vibe receive tracking")
            
            logger.info(f"Tracked vibe sending: {sender.username} sent {vibe_name} to {receiver_id}")
            return sender_activity, receiver_activity
            
        except Exception as e:
            logger.error(f"Failed to track vibe sending: {str(e)}")
            return None, None
    
    @staticmethod
    def track_vibe_view(user, vibe_data, duration_seconds=None, **kwargs):
        """
        Track vibe viewing activity.
        
        Records when a user views a vibe, including viewing duration
        and context information.
        
        Args:
            user: User object who viewed the vibe
            vibe_data: Dictionary containing vibe information
            duration_seconds: How long the user viewed the vibe
            **kwargs: Additional metadata
            
        Returns:
            VibeActivity: Created activity record or None if failed
        """
        try:
            # Handle user_id if passed instead of User object
            if isinstance(user, str):
                user = User.objects.get(id=user)
            elif hasattr(user, 'user_id'):
                user = User.objects.get(id=user.user_id)
            
            # Extract vibe information
            vibe_id = vibe_data.get('vibe_id') or vibe_data.get('uid')
            vibe_name = vibe_data.get('vibe_name') or vibe_data.get('name')
            vibe_type = vibe_data.get('vibe_type', 'main')
            category = vibe_data.get('category')
            
            # Create metadata
            metadata = {
                'duration_seconds': duration_seconds,
                'vibe_popularity': vibe_data.get('popularity', 0),
                'view_context': kwargs.get('view_context', 'direct')
            }
            metadata.update(kwargs.get('metadata', {}))
            
            # Create activity record
            activity = VibeActivity.objects.create(
                user=user,
                activity_type='vibe_view',
                vibe_type=vibe_type,
                vibe_id=str(vibe_id),
                vibe_name=vibe_name,
                vibe_category=category,
                ip_address=kwargs.get('ip_address'),
                user_agent=kwargs.get('user_agent'),
                metadata=metadata
            )
            
            logger.info(f"Tracked vibe view: {user.username} viewed {vibe_name} ({vibe_id})")
            return activity
            
        except Exception as e:
            logger.error(f"Failed to track vibe view: {str(e)}")
            return None
    
    @staticmethod
    def track_vibe_search(user, search_query, results_count=0, **kwargs):
        """
        Track vibe search activity.
        
        Records when a user searches for vibes, including search terms
        and results information.
        
        Args:
            user: User object who performed the search
            search_query: Search query string
            results_count: Number of results returned
            **kwargs: Additional metadata
            
        Returns:
            VibeActivity: Created activity record or None if failed
        """
        try:
            # Handle user_id if passed instead of User object
            if isinstance(user, str):
                user = User.objects.get(id=user)
            elif hasattr(user, 'user_id'):
                user = User.objects.get(id=user.user_id)
            
            # Create metadata
            metadata = {
                'search_query': search_query,
                'results_count': results_count,
                'search_type': kwargs.get('search_type', 'general')
            }
            metadata.update(kwargs.get('metadata', {}))
            
            # Create activity record
            activity = VibeActivity.objects.create(
                user=user,
                activity_type='vibe_search',
                vibe_type='main',  # Default for search activities
                vibe_id='search',  # Special ID for search activities
                vibe_name=search_query,
                ip_address=kwargs.get('ip_address'),
                user_agent=kwargs.get('user_agent'),
                metadata=metadata
            )
            
            logger.info(f"Tracked vibe search: {user.username} searched for '{search_query}'")
            return activity
            
        except Exception as e:
            logger.error(f"Failed to track vibe search: {str(e)}")
            return None
    
    @staticmethod
    def track_vibe_viewing(user, vibe_data, duration_seconds=None, ip_address=None, user_agent=None):
        """
        Track vibe viewing activity.
        
        Args:
            user: User instance who is viewing the vibe
            vibe_data: Dictionary containing vibe information
            duration_seconds: How long the user viewed the vibe
            ip_address: IP address of the user
            user_agent: User agent string
        """
        try:
            # Handle user_id if passed instead of User object
            if isinstance(user, str):
                user = User.objects.get(id=user)
            elif hasattr(user, 'user_id'):
                user = User.objects.get(id=user.user_id)
            
            # Extract vibe information
            vibe_id = vibe_data.get('vibe_id') or vibe_data.get('uid')
            vibe_name = vibe_data.get('vibe_name') or vibe_data.get('name')
            vibe_type = vibe_data.get('vibe_type', 'main')
            category = vibe_data.get('category')
            
            # Create metadata
            metadata = {
                'duration_seconds': duration_seconds,
                'vibe_popularity': vibe_data.get('popularity', 0),
                'view_context': 'direct'
            }
            
            # Create activity record
            activity = VibeActivity.objects.create(
                user=user,
                activity_type='vibe_view',
                vibe_type=vibe_type,
                vibe_id=str(vibe_id),
                vibe_name=vibe_name,
                vibe_category=category,
                vibe_score=vibe_data.get('vibe_score'),
                success=True,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata=metadata
            )
            
            logger.info(f"Tracked vibe viewing: {user.username} viewed {vibe_name} ({vibe_id})")
            return activity
            
        except Exception as e:
            # Silent fail - don't break the main flow if activity tracking fails
            logger.error(f"Failed to track vibe viewing activity: {str(e)}")
            return None
    
    @staticmethod
    def get_user_vibe_activity_summary(user, days=30):
        """
        Get summary of user's vibe activities.
        
        Args:
            user: User object
            days: Number of days to look back
            
        Returns:
            dict: Summary of vibe activities
        """
        try:
            from datetime import timedelta
            
            # Handle user_id if passed instead of User object
            if isinstance(user, str):
                user = User.objects.get(id=user)
            elif hasattr(user, 'user_id'):
                user = User.objects.get(id=user.user_id)
            
            # Calculate date range
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
            
            # Get activities in date range
            activities = VibeActivity.objects.filter(
                user=user,
                timestamp__gte=start_date,
                timestamp__lte=end_date
            )
            
            # Calculate summary statistics
            summary = {
                'total_activities': activities.count(),
                'vibes_created': activities.filter(activity_type='vibe_create').count(),
                'vibes_sent': activities.filter(activity_type='vibe_send').count(),
                'vibes_received': activities.filter(activity_type='vibe_receive').count(),
                'vibes_viewed': activities.filter(activity_type='vibe_view').count(),
                'searches_performed': activities.filter(activity_type='vibe_search').count(),
                'success_rate': activities.filter(success=True).count() / max(activities.count(), 1),
                'most_active_day': None,
                'favorite_vibe_category': None
            }
            
            # Find most active day
            if activities.exists():
                from django.db.models import Count
                daily_counts = activities.extra({
                    'day': 'date(timestamp)'
                }).values('day').annotate(count=Count('id')).order_by('-count')
                
                if daily_counts:
                    summary['most_active_day'] = daily_counts[0]['day']
                
                # Find favorite vibe category
                category_counts = activities.exclude(
                    vibe_category__isnull=True
                ).values('vibe_category').annotate(
                    count=Count('id')
                ).order_by('-count')
                
                if category_counts:
                    summary['favorite_vibe_category'] = category_counts[0]['vibe_category']
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get vibe activity summary: {str(e)}")
            return {}
    
    @staticmethod
    def get_user_vibe_summary(user, days=30):
        """
        Alias for get_user_vibe_activity_summary for compatibility.
        """
        return VibeActivityService.get_user_vibe_activity_summary(user, days)