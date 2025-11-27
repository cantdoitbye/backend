# opportunity/graphql/types.py

"""
GraphQL Type Definitions for Opportunity Module.

This module defines the GraphQL types returned by opportunity queries and mutations.
Types include detailed opportunity information with engagement metrics, creator details,
and presigned URLs for document attachments.
"""

import graphene
from graphene import ObjectType
from auth_manager.graphql.types import UserType
from post.graphql.types import FileDetailType
from auth_manager.Utils.generate_presigned_url import generate_file_info
from auth_manager.models import Users
from neomodel import db


class OpportunityType(ObjectType):
    """
    GraphQL type for Opportunity objects returned from Neo4j database.
    
    This type defines the complete structure of opportunity data when queried
    through GraphQL API. It provides type safety for frontend applications and
    includes engagement metrics, creator information, and presigned URLs for
    file attachments.
    
    Used by:
    - Frontend applications querying opportunity data
    - Feed queries (mixed with posts and debates)
    - Opportunity detail views
    - Search and filter operations
    
    Maps to the Opportunity model fields from Neo4j database with additional
    computed fields for engagement metrics and file URLs.
    """
    
    # ========== CORE FIELDS ==========
    uid = graphene.String()
    
    # Opportunity type (job, event, cause, etc.)
    opportunity_type = graphene.String()
    
    role = graphene.String()
    job_type = graphene.String()
    
    # ========== LOCATION ==========
    location = graphene.String()
    is_remote = graphene.Boolean()
    is_hybrid = graphene.Boolean()
    
    # ========== EXPERIENCE & COMPENSATION ==========
    experience_level = graphene.String()
    salary_range_text = graphene.String()
    salary_min = graphene.Int()
    salary_max = graphene.Int()
    salary_currency = graphene.String()
    
    # ========== CONTENT ==========
    description = graphene.String()
    key_responsibilities = graphene.List(graphene.String)
    requirements = graphene.List(graphene.String)
    good_to_have_skills = graphene.List(graphene.String)
    skills = graphene.List(graphene.String)
    
    # ========== ATTACHMENTS ==========
    document_ids = graphene.List(graphene.String)
    document_urls = graphene.List(FileDetailType)  # Presigned URLs
    cover_image_id = graphene.String()
    cover_image_url = graphene.Field(FileDetailType)  # Presigned URL
    
    # ========== CALL TO ACTION ==========
    cta_text = graphene.String()
    cta_type = graphene.String()
    
    # ========== PRIVACY & TAGS ==========
    privacy = graphene.String()
    tags = graphene.List(graphene.String)
    
    # ========== STATUS & TIMESTAMPS ==========
    is_active = graphene.Boolean()
    is_deleted = graphene.Boolean()
    expires_at = graphene.DateTime()
    created_at = graphene.DateTime()
    updated_at = graphene.DateTime()
    
    # ========== MATRIX INTEGRATION ==========
    room_id = graphene.String()  # Matrix room ID for chat-based applications
    
    # ========== SCORING ==========
    score = graphene.Float()  # Score for feed ranking and recommendations
    
    # ========== CREATOR INFORMATION ==========
    created_by = graphene.Field(UserType)
    
    # ========== ENGAGEMENT METRICS ==========
    # These are computed from relationship counts
    like_count = graphene.Int()
    comment_count = graphene.Int()
    share_count = graphene.Int()
    view_count = graphene.Int()
    saved_count = graphene.Int()
    
    # ========== USER INTERACTION STATUS ==========
    # Whether current user has interacted with this opportunity
    is_liked = graphene.Boolean()
    is_saved = graphene.Boolean()
    
    # ========== COMPUTED FIELDS ==========
    is_expired = graphene.Boolean()  # Based on expires_at date
    engagement_score = graphene.Float()  # Calculated engagement score
    
    @classmethod
    def from_neomodel(cls, opportunity, info=None, user=None):
        """
        Convert Opportunity Neo4j model instance to GraphQL type.
        
        This method bridges the gap between the database model and GraphQL API.
        It safely extracts data from the Neo4j model, generates presigned URLs
        for files, calculates engagement metrics, and creates a GraphQL type
        that can be serialized and sent to frontend applications.
        
        Args:
            opportunity: Opportunity model instance from Neo4j
            info: GraphQL resolve info (optional)
            user: Current authenticated user (optional)
        
        Returns:
            OpportunityType instance with all fields populated
        """
        
        # ========== GET CREATOR ==========
        creator = opportunity.created_by.single()
        
        # ========== GENERATE PRESIGNED URLS FOR DOCUMENTS ==========
        document_urls = None
        if opportunity.document_ids:
            try:
                document_urls = [
                    FileDetailType(**generate_file_info(doc_id)) 
                    for doc_id in opportunity.document_ids
                ]
            except Exception as e:
                print(f"Error generating document URLs: {e}")
                document_urls = []
        
        # ========== GENERATE PRESIGNED URL FOR COVER IMAGE ==========
        cover_image_url = None
        if opportunity.cover_image_id:
            try:
                cover_image_url = FileDetailType(**generate_file_info(opportunity.cover_image_id))
            except Exception as e:
                print(f"Error generating cover image URL: {e}")
        
        # ========== COUNT INTERACTIONS ==========
        try:
            like_count = len(opportunity.like.all())
            comment_count = len(opportunity.comment.all())
            share_count = len(opportunity.share.all())
            view_count = len(opportunity.view.all())
            saved_count = len(opportunity.saved.all())
        except Exception as e:
            print(f"Error counting interactions: {e}")
            like_count = comment_count = share_count = view_count = saved_count = 0
        
        # ========== CHECK USER INTERACTION STATUS ==========
        is_liked = False
        is_saved = False
        if user and not user.is_anonymous:
            try:
                user_node = Users.nodes.get(user_id=user.id)
                
                # Check if current user has liked this opportunity
                liked_query = """
                MATCH (user:Users {uid: $user_uid})-[:HAS_USER]->(like:Like)-[:HAS_OPPORTUNITY]->(opp:Opportunity {uid: $opp_uid})
                RETURN like LIMIT 1
                """
                liked_results, _ = db.cypher_query(
                    liked_query, 
                    {'user_uid': user_node.uid, 'opp_uid': opportunity.uid}
                )
                is_liked = len(liked_results) > 0
                
                # Check if current user has saved this opportunity
                saved_query = """
                MATCH (user:Users {uid: $user_uid})-[:HAS_USER]->(saved:SavedPost)-[:HAS_OPPORTUNITY]->(opp:Opportunity {uid: $opp_uid})
                RETURN saved LIMIT 1
                """
                saved_results, _ = db.cypher_query(
                    saved_query, 
                    {'user_uid': user_node.uid, 'opp_uid': opportunity.uid}
                )
                is_saved = len(saved_results) > 0
                
            except Exception as e:
                print(f"Error checking user interaction: {e}")
        
        # ========== CHECK IF EXPIRED ==========
        is_expired = opportunity.is_expired if hasattr(opportunity, 'is_expired') else False
        
        # ========== CALCULATE ENGAGEMENT SCORE ==========
        engagement_score = opportunity.engagement_score if hasattr(opportunity, 'engagement_score') else 0.0
        
        # ========== RETURN GRAPHQL TYPE ==========
        return cls(
            uid=opportunity.uid,
            opportunity_type=opportunity.opportunity_type,
            role=opportunity.role,
            job_type=opportunity.job_type,
            location=opportunity.location,
            is_remote=opportunity.is_remote,
            is_hybrid=opportunity.is_hybrid,
            experience_level=opportunity.experience_level,
            salary_range_text=opportunity.salary_range_text,
            salary_min=opportunity.salary_min,
            salary_max=opportunity.salary_max,
            salary_currency=opportunity.salary_currency,
            description=opportunity.description,
            key_responsibilities=opportunity.key_responsibilities or [],
            requirements=opportunity.requirements or [],
            good_to_have_skills=opportunity.good_to_have_skills or [],
            skills=opportunity.skills or [],
            document_ids=opportunity.document_ids or [],
            document_urls=document_urls,
            cover_image_id=opportunity.cover_image_id,
            cover_image_url=cover_image_url,
            cta_text=opportunity.cta_text,
            cta_type=opportunity.cta_type,
            privacy=opportunity.privacy,
            tags=opportunity.tags or [],
            is_active=opportunity.is_active,
            is_deleted=opportunity.is_deleted,
            expires_at=opportunity.expires_at,
            created_at=opportunity.created_at,
            updated_at=opportunity.updated_at,
            room_id=opportunity.room_id,  # Matrix room ID
            score=opportunity.score if hasattr(opportunity, 'score') else 3.2,  # Default score
            created_by=UserType.from_neomodel(creator) if creator else None,
            like_count=like_count,
            comment_count=comment_count,
            share_count=share_count,
            view_count=view_count,
            saved_count=saved_count,
            is_liked=is_liked,
            is_saved=is_saved,
            is_expired=is_expired,
            engagement_score=engagement_score
        )

        # ADD THESE METHODS inside the OpportunityType class (after the from_neomodel method):

    def resolve_like_count(self, info):
        """Get like count for this opportunity"""
        from neomodel import db
        query = """
        MATCH (o:Opportunity {uid: $opportunity_uid})-[:HAS_OPPORTUNITY]-(like:Like)
        WHERE like.is_deleted = false
        RETURN count(like) as count
        """
        results, _ = db.cypher_query(query, {'opportunity_uid': self.uid})
        return results[0][0] if results else 0

    def resolve_comment_count(self, info):
        """Get comment count for this opportunity"""
        from neomodel import db
        query = """
        MATCH (o:Opportunity {uid: $opportunity_uid})-[:HAS_OPPORTUNITY]-(comment:Comment)
        WHERE comment.is_deleted = false
        RETURN count(comment) as count
        """
        results, _ = db.cypher_query(query, {'opportunity_uid': self.uid})
        return results[0][0] if results else 0

    def resolve_share_count(self, info):
        """Get share count for this opportunity"""
        from neomodel import db
        query = """
        MATCH (o:Opportunity {uid: $opportunity_uid})-[:HAS_OPPORTUNITY]-(share:PostShare)
        WHERE share.is_deleted = false
        RETURN count(share) as count
        """
        results, _ = db.cypher_query(query, {'opportunity_uid': self.uid})
        return results[0][0] if results else 0

    def resolve_view_count(self, info):
        """Get view count for this opportunity"""
        from neomodel import db
        query = """
        MATCH (o:Opportunity {uid: $opportunity_uid})-[:HAS_OPPORTUNITY]-(view:PostView)
        RETURN count(view) as count
        """
        results, _ = db.cypher_query(query, {'opportunity_uid': self.uid})
        return results[0][0] if results else 0

    def resolve_is_liked(self, info):
        """Check if current user has liked this opportunity"""
        try:
            from neomodel import db
            payload = info.context.payload
            user_id = payload.get('user_id')
            
            if not user_id:
                return False
            
            from auth_manager.models import Users
            user_node = Users.nodes.get(user_id=user_id)
            
            query = """
            MATCH (u:Users {uid: $user_uid})-[:HAS_USER]-(like:Like)-[:HAS_OPPORTUNITY]->(o:Opportunity {uid: $opportunity_uid})
            WHERE like.is_deleted = false
            RETURN like
            LIMIT 1
            """
            results, _ = db.cypher_query(query, {
                'user_uid': user_node.uid,
                'opportunity_uid': self.uid
            })
            return len(results) > 0
        except Exception:
            return False

    def resolve_is_saved(self, info):
        """Check if current user has saved this opportunity"""
        # TODO: Implement saved functionality if needed
        return False

    def resolve_engagement_score(self, info):
        """Calculate engagement score for this opportunity"""
        from neomodel import db
        query = """
        MATCH (o:Opportunity {uid: $opportunity_uid})
        OPTIONAL MATCH (o)-[:HAS_OPPORTUNITY]-(like:Like)
        WHERE like.is_deleted = false
        OPTIONAL MATCH (o)-[:HAS_OPPORTUNITY]-(comment:Comment)
        WHERE comment.is_deleted = false
        OPTIONAL MATCH (o)-[:HAS_OPPORTUNITY]-(share:PostShare)
        WHERE share.is_deleted = false
        WITH 
            COUNT(DISTINCT like) as like_count,
            COUNT(DISTINCT comment) as comment_count,
            COUNT(DISTINCT share) as share_count
        RETURN 
            (like_count * 0.5 + comment_count * 1.0 + share_count * 1.5) as score
        """
        results, _ = db.cypher_query(query, {'opportunity_uid': self.uid})
        return round(results[0][0], 2) if results else 0.0


class OpportunityListType(ObjectType):
    """
    Paginated list of opportunities with metadata.
    
    Used for feed queries and opportunity lists with pagination support.
    """
    opportunities = graphene.List(OpportunityType)
    total_count = graphene.Int()
    has_more = graphene.Boolean()
    offset = graphene.Int()
