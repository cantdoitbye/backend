from post.utils.reaction_manager import PostReactionUtils, IndividualVibeManager
from post.redis import get_post_comment_count, get_post_like_count
from post.models import PostReactionManager, Like
from vibe_manager.models import IndividualVibe, CommunityVibe
from neomodel import db
from datetime import datetime

class CommunityPostDataHelper:
    """
    Helper class to fetch post-related data for community items
    """
    
    @staticmethod
    def get_user_vibe_details(user_node, community_item):
        """
        Get user-specific vibe details for a community item
        This is a placeholder - you'll need to implement based on your specific data relationships
        """
        try:
       
            user_reactions = []
            
        
            
            return user_reactions
        except Exception as e:
            print(f"Error getting user vibe details: {e}")
            return []
    
    @staticmethod
    def get_vibes_count(community_item):
        """
        Get total vibes count for a community item
        """
        try:
            if hasattr(community_item, 'like'):
                return len([like for like in community_item.like.all() if not like.is_deleted])
            
            if hasattr(community_item, 'uid'):
                post_reaction_manager = PostReactionManager.objects.filter(
                    post_uid=community_item.uid
                ).first()
                
                if post_reaction_manager:
                    all_reactions = post_reaction_manager.post_vibe
                    return sum(reaction.get('vibes_count', 0) for reaction in all_reactions)
            
            return 0
        except Exception as e:
            print(f"Error getting vibes count: {e}")
            return 0
    
    @staticmethod
    def get_vibe_feed_list():
        """
        Get the standard vibe feed list
        """
        try:
            vibe_feed_list_data = IndividualVibeManager.get_data()
            return vibe_feed_list_data
        except Exception as e:
            print(f"Error getting vibe feed list from IndividualVibeManager: {e}")
            try:
                vibes = CommunityVibe.objects.all()[:10]
                return [
                    {
                        'vibes_id': str(vibe.id),
                        'vibes_name': vibe.name_of_vibe,
                        'cumulative_vibe_score': 0
                    }
                    for vibe in vibes
                ]
            except Exception as e2:
                print(f"Error getting vibe feed list from CommunityVibe: {e2}")
                try:
                    vibes = IndividualVibe.objects.all()[:10]
                    return [
                        {
                            'vibes_id': str(vibe.id),
                            'vibes_name': vibe.name_of_vibe,
                            'cumulative_vibe_score': 0
                        }
                        for vibe in vibes
                    ]
                except Exception as e3:
                    print(f"Error getting vibe feed list from IndividualVibe: {e3}")
                    return []
    
    @staticmethod
    def get_community_item_reactions(community_item, user_node):
        """
        Get reactions for a community item (goal, activity, etc.)
        Returns a dictionary with vibes_count, my_vibe_details, and vibe_feed_list
        """
        result = {
            'vibes_count': 0,
            'my_vibe_details': [],
            'vibe_feed_list': []
        }
        
        try:
            result['vibes_count'] = CommunityPostDataHelper.get_vibes_count(community_item)
            
            result['my_vibe_details'] = CommunityPostDataHelper.get_user_vibe_details(user_node, community_item)
            
            result['vibe_feed_list'] = CommunityPostDataHelper.get_vibe_feed_list()
            
        except Exception as e:
            print(f"Error getting community item reactions: {e}")
        
        return result
    
    @staticmethod
    def get_post_metrics_for_community_item(community_item_uid):
        """
        Get post metrics if the community item has associated posts
        """
        try:
           
            
            comment_count = get_post_comment_count(community_item_uid)
            like_count = get_post_like_count(community_item_uid)
            
            return {
                'comment_count': comment_count,
                'like_count': like_count
            }
        except Exception as e:
            print(f"Error getting post metrics: {e}")
            return {
                'comment_count': 0,
                'like_count': 0
            }
