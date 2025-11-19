from post.utils.reaction_manager import PostReactionUtils, IndividualVibeManager
from post.redis import get_post_comment_count, get_post_like_count
from post.models import PostReactionManager, Like
from vibe_manager.models import IndividualVibe, CommunityVibe
from community.utils.post_data_helper import CommunityPostDataHelper
from neomodel import db
from datetime import datetime

class EnhancedQueryHelper:
    """
    Helper class for enhanced community queries with post data
    """
    
    @staticmethod
    def format_reaction_for_feed(reaction):
        """
        Format a reaction object for feed display
        """
        try:
            if isinstance(reaction, dict):
                unix_timestamp = reaction.get('timestamp')
                timestamp = datetime.fromtimestamp(unix_timestamp) if unix_timestamp else None
                
                return {
                    'uid': reaction.get('uid'),
                    'vibe': reaction.get('vibe'),
                    'reaction': reaction.get('reaction'),
                    'is_deleted': reaction.get('is_deleted', False),
                    'timestamp': timestamp
                }
            else:
                return {
                    'uid': reaction.uid,
                    'vibe': reaction.vibe,
                    'reaction': reaction.reaction,
                    'is_deleted': reaction.is_deleted,
                    'timestamp': reaction.timestamp
                }
        except Exception as e:
            print(f"Error formatting reaction for feed: {e}")
            return None
    
    @staticmethod
    def get_creator_with_profile(creator_node):
        """
        Get creator information with profile data
        """
        try:
            if not creator_node:
                return None
            
            profile = creator_node.profile.single() if hasattr(creator_node, 'profile') else None
            
            creator_data = {
                'uid': creator_node.uid,
                'user_id': creator_node.user_id,
                'username': creator_node.username or creator_node.name if hasattr(creator_node, 'name') else None,
                'email': creator_node.email,
                'first_name': creator_node.first_name,
                'last_name': creator_node.last_name,
                'is_active': getattr(creator_node, 'is_active', True),
                'user_type': getattr(creator_node, 'user_type', None)
            }
            
            profile_data = None
            if profile:
                profile_data = {
                    'uid': profile.uid,
                    'user_id': profile.user_id,
                    'gender': profile.gender,
                    'profile_pic_id': profile.profile_pic_id
                }
            
            return {
                'creator': creator_data,
                'profile': profile_data
            }
        except Exception as e:
            print(f"Error getting creator with profile: {e}")
            return None
    
    @staticmethod
    def enhance_community_item_with_post_data(community_item, user_node):
        """
        Main method to enhance any community item with post data
        """
        try:
            creator_info = None
            if hasattr(community_item, 'created_by'):
                creator = community_item.created_by.single()
                creator_info = EnhancedQueryHelper.get_creator_with_profile(creator)
            
            # Get post-related data
            post_data = CommunityPostDataHelper.get_community_item_reactions(community_item, user_node)
            
            # Format reactions for feed
            formatted_reactions = []
            for reaction in post_data['my_vibe_details']:
                formatted_reaction = EnhancedQueryHelper.format_reaction_for_feed(reaction)
                if formatted_reaction:
                    formatted_reactions.append(formatted_reaction)
            
            return {
                'creator_info': creator_info,
                'vibes_count': post_data['vibes_count'],
                'my_vibe_details': formatted_reactions,
                'vibe_feed_list': post_data['vibe_feed_list']
            }
        except Exception as e:
            print(f"Error enhancing community item with post data: {e}")
            return {
                'creator_info': None,
                'vibes_count': 0,
                'my_vibe_details': [],
                'vibe_feed_list': []
            }