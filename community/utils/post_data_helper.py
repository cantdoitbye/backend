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
        Get user-specific vibe details for a community item.
        Fetches CommunityContentVibe reactions from the current user.
        """
        try:
            if not user_node or not community_item:
                return []
            
            user_reactions = []
            
            # Query for vibe reactions from this user to this content
            try:
                query = """
                MATCH (u:Users {uid: $user_uid})-[:REACTED_BY]-(ccv:CommunityContentVibe)<-[:HAS_VIBE_REACTION]-(content {uid: $content_uid})
                WHERE ccv.is_active = true
                RETURN ccv.uid, ccv.vibe_intensity, ccv.vibe_name, ccv.is_active, ccv.timestamp
                """
                results, _ = db.cypher_query(query, {
                    'user_uid': user_node.uid,
                    'content_uid': community_item.uid
                })
                
                for record in results:
                    # Convert datetime to Unix timestamp if needed
                    timestamp_value = record[4] if len(record) > 4 else None
                    if timestamp_value:
                        # Check if it's a Neo4j datetime or Python datetime
                        if hasattr(timestamp_value, 'to_native'):
                            # Neo4j datetime - convert to native Python datetime first
                            timestamp_value = timestamp_value.to_native().timestamp()
                        elif hasattr(timestamp_value, 'timestamp'):
                            # Python datetime object
                            timestamp_value = timestamp_value.timestamp()
                        # If it's already a number (int/float), keep as is
                    
                    user_reactions.append({
                        'uid': record[0],
                        'vibe': record[1] if record[1] else 0,
                        'reaction': record[2] if record[2] else '',
                        'is_deleted': not record[3] if len(record) > 3 else False,
                        'timestamp': timestamp_value
                    })
            except Exception as e:
                print(f"Error querying vibe reactions: {e}")
            
            return user_reactions
        except Exception as e:
            print(f"Error getting user vibe details: {e}")
            return []
    
    @staticmethod
    def get_vibes_count(community_item):
        """
        Get total vibes count for a community item.
        Counts both old 'like' reactions and new CommunityContentVibe reactions.
        """
        try:
            vibe_count = 0
            
            # Count old-style likes
            if hasattr(community_item, 'like'):
                vibe_count += len([like for like in community_item.like.all() if not like.is_deleted])
            
            # Count new-style vibe reactions
            if hasattr(community_item, 'vibe_reactions'):
                vibe_count += len([vibe for vibe in community_item.vibe_reactions.all() if vibe.is_active])
            
            # Fallback to PostReactionManager if available
            if vibe_count == 0 and hasattr(community_item, 'uid'):
                post_reaction_manager = PostReactionManager.objects.filter(
                    post_uid=community_item.uid
                ).first()
                
                if post_reaction_manager:
                    all_reactions = post_reaction_manager.post_vibe
                    vibe_count = sum(reaction.get('vibes_count', 0) for reaction in all_reactions)
            
            return vibe_count
        except Exception as e:
            print(f"Error getting vibes count: {e}")
            return 0
    
    @staticmethod
    def get_vibe_feed_list(community_item=None):
        """
        Get the vibe feed list.
        Returns all available vibes with their cumulative scores for the content.
        If community_item is provided, shows actual scores; otherwise all zeros.
        """
        try:
            # Get all available vibes from IndividualVibeManager
            all_vibes = IndividualVibeManager.get_data()
            
            # If community_item provided, get content-specific scores and merge
            if community_item and hasattr(community_item, 'uid'):
                try:
                    query = """
                    MATCH (content {uid: $content_uid})-[:HAS_VIBE_REACTION]->(ccv:CommunityContentVibe)
                    WHERE ccv.is_active = true
                    RETURN ccv.individual_vibe_id as vibe_id, 
                           SUM(ccv.vibe_intensity) as total_score
                    """
                    results, _ = db.cypher_query(query, {'content_uid': community_item.uid})
                    
                    # Create a dictionary of vibe scores
                    vibe_scores = {}
                    if results:
                        for record in results:
                            vibe_id = str(record[0]) if record[0] else None
                            if vibe_id:
                                vibe_scores[vibe_id] = float(record[1]) if record[1] else 0.0
                    
                    # Merge scores with all available vibes
                    merged_vibes = []
                    for vibe in all_vibes:
                        vibe_id = vibe.get('vibes_id', '0')
                        # Update score if this vibe was sent to this content
                        if vibe_id in vibe_scores:
                            vibe['cumulative_vibe_score'] = vibe_scores[vibe_id]
                        else:
                            # Ensure score is float, not string
                            current_score = vibe.get('cumulative_vibe_score', 0)
                            if isinstance(current_score, str):
                                vibe['cumulative_vibe_score'] = float(current_score) if current_score else 0.0
                            elif not isinstance(current_score, (int, float)):
                                vibe['cumulative_vibe_score'] = 0.0
                        merged_vibes.append(vibe)
                    
                    return merged_vibes
                except Exception as e:
                    print(f"Error aggregating content-specific vibes: {e}")
            
            # Return standard vibe list (convert string scores to float)
            for vibe in all_vibes:
                current_score = vibe.get('cumulative_vibe_score', 0)
                if isinstance(current_score, str):
                    vibe['cumulative_vibe_score'] = float(current_score) if current_score else 0.0
                elif not isinstance(current_score, (int, float)):
                    vibe['cumulative_vibe_score'] = 0.0
            return all_vibes
        except Exception as e:
            print(f"Error getting vibe feed list from IndividualVibeManager: {e}")
            try:
                vibes = CommunityVibe.objects.all()[:10]
                return [
                    {
                        'vibes_id': str(vibe.id),
                        'vibes_name': vibe.name_of_vibe,
                        'cumulative_vibe_score': 0.0
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
                            'cumulative_vibe_score': 0.0
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
            
            # Pass community_item to get content-specific vibe aggregation
            result['vibe_feed_list'] = CommunityPostDataHelper.get_vibe_feed_list(community_item)
            
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
