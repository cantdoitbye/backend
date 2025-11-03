from typing import List, Optional
import logging
from auth_manager.models import Users
from post.models import UserMention
from community.models import CommunityPost
from post.models import Post, Comment
from neomodel import db


logger = logging.getLogger(__name__)

class MentionService:
    """
    Generic service for handling user mentions across all content types.
    """
    
    @staticmethod
    def create_mentions(
        mentioned_user_uids: List[str],
        content_type: str,
        content_uid: str,
        mentioned_by_uid: str,
        mention_context: Optional[str] = None
    ) -> List[UserMention]:
        """
        Create mentions for a piece of content.
        
        Args:
            mentioned_user_uids: List of user UIDs being mentioned
            content_type: Type of content ('post', 'community_post', 'comment', 'story', etc.)
            content_uid: UID of the content
            mentioned_by_uid: UID of user creating the mention
            mention_context: Optional context ('title', 'description', etc.)
        
        Returns:
            List of created UserMention objects
        """
        mentions = []
        
        try:
            mentioned_by = Users.nodes.get(uid=mentioned_by_uid)
            
            for mentioned_user_uid in mentioned_user_uids:
                try:
                    mentioned_user = Users.nodes.get(uid=mentioned_user_uid)
                    
                    # Create the mention
                    mention = UserMention(
                        content_type=content_type,
                        content_uid=content_uid,
                        mention_context=mention_context
                    )
                    mention.save() 
                    
                    mention.mentioned_user.connect(mentioned_user)
                    mention.mentioned_by.connect(mentioned_by)
                    # Create specific relationship based on content type
                    MentionService._create_specific_relationship(mention, content_type, content_uid)
                    
                    mentions.append(mention)
                    
                    # Send notification for the mention
                    MentionService._send_mention_notification(mentioned_user_uid, mentioned_by_uid, content_type, content_uid)
                    
                except Users.DoesNotExist:
                    logger.warning(f"User with UID {mentioned_user_uid} not found for mention")
                    continue
                    
        except Users.DoesNotExist:
            logger.error(f"Mentioning user with UID {mentioned_by_uid} not found")
            
        return mentions
    
    @staticmethod
    def _create_specific_relationship(mention: UserMention, content_type: str, content_uid: str):
        """Create specific relationship based on content type for faster queries."""
        try:
            if content_type == 'post':
                post = Post.nodes.get(uid=content_uid)
                mention.post.connect(post)
            elif content_type == 'community_post':
                community_post = CommunityPost.nodes.get(uid=content_uid)
                mention.community_post.connect(community_post)
            elif content_type == 'comment':
                comment = Comment.nodes.get(uid=content_uid)
                mention.comment.connect(comment)
            elif content_type == 'story':
                from story.models import Story
                story = Story.nodes.get(uid=content_uid)
                mention.story.connect(story)    
            elif content_type == 'community_description':
                from community.models import Community
                community = Community.nodes.get(uid=content_uid)
                mention.community_description.connect(community)    
            # Add more content types as needed
        except Exception as e:
            logger.warning(f"Could not create specific relationship for {content_type}:{content_uid} - {str(e)}")
    
    @staticmethod
    def _send_mention_notification(mentioned_user_uid: str, mentioned_by_uid: str, content_type: str, content_uid: str):
        """Send notification for mention."""
        # Import here to avoid circular imports
        from post.services.notification_service import NotificationService
        import asyncio
        
        try:
            print(f"🔔 MENTION SERVICE DEBUG: Attempting to send mention notification...")
            print(f"🔔 MENTION SERVICE DEBUG: Mentioned user: {mentioned_user_uid}")
            print(f"🔔 MENTION SERVICE DEBUG: Mentioner: {mentioned_by_uid}")
            print(f"🔔 MENTION SERVICE DEBUG: Content: {content_type}:{content_uid}")
            
            # Create notification service and send notification asynchronously
            notification_service = NotificationService()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(notification_service.notify_user_mentioned(
                    mentioned_user_uid=mentioned_user_uid,
                    mentioner_uid=mentioned_by_uid,
                    content_type=content_type,
                    content_uid=content_uid
                ))
                print(f"🔔 MENTION SERVICE DEBUG: ✅ Mention notification sent successfully!")
            finally:
                loop.close()
                
        except Exception as e:
            print(f"🔔 MENTION SERVICE DEBUG: ❌ Failed to send mention notification: {str(e)}")
            logger.error(f"Failed to send mention notification: {str(e)}")
    
    @staticmethod
    def get_mentions_for_content(content_type: str, content_uid: str) -> List[UserMention]:
        """Get all mentions for a specific piece of content."""
        try:
            query = """
            MATCH (mention:UserMention {content_type: $content_type, content_uid: $content_uid, is_active: true})
            MATCH (mention)-[:MENTIONED_USER]->(mentioned_user:Users)
            MATCH (mention)-[:MENTIONED_BY]->(mentioned_by:Users)
            RETURN mention, mentioned_user, mentioned_by
            ORDER BY mention.mentioned_at DESC
            """
            
            results, _ = db.cypher_query(query, {
                'content_type': content_type,
                'content_uid': content_uid
            })
            
            mentions = []
            for result in results:
                mention = UserMention.inflate(result[0])
                mentions.append(mention)
            
            return mentions
            
        except Exception as e:
            logger.error(f"Error getting mentions for {content_type}:{content_uid} - {str(e)}")
            return []
    
    @staticmethod
    def get_user_mentions(user_uid: str, limit: int = 50) -> List[UserMention]:
        """Get all mentions for a specific user."""
        try:
            query = """
            MATCH (user:Users {uid: $user_uid})<-[:MENTIONED_USER]-(mention:UserMention {is_active: true})
            MATCH (mention)-[:MENTIONED_BY]->(mentioned_by:Users)
            RETURN mention, mentioned_by
            ORDER BY mention.mentioned_at DESC
            LIMIT $limit
            """
            
            results, _ = db.cypher_query(query, {
                'user_uid': user_uid,
                'limit': limit
            })
            
            mentions = []
            for result in results:
                mention = UserMention.inflate(result[0])
                mentions.append(mention)
            
            return mentions
            
        except Exception as e:
            logger.error(f"Error getting mentions for user {user_uid} - {str(e)}")
            return []