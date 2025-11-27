# opportunity/graphql/queries.py

"""
GraphQL Query Resolvers for Opportunity Module.

This module contains all GraphQL queries for fetching and filtering opportunities.
Includes single opportunity fetch, list queries, user's opportunities, and
search/filter functionality.

Used by: Frontend for displaying opportunities in feed, search, and profile
"""

import graphene
from graphql import GraphQLError
from graphql_jwt.decorators import login_required
from neomodel import db

from .types import OpportunityType, OpportunityListType
from .inputs import OpportunityFilterInput
from opportunity.models import Opportunity
from auth_manager.models import Users
from post.models import Comment
from post.graphql.types import CommentType


class OpportunityQueries(graphene.ObjectType):
    """
    Container for all opportunity-related queries.
    
    This class groups all opportunity queries and makes them available
    through the GraphQL API schema.
    """
    
    # ========== SINGLE OPPORTUNITY ==========
    opportunity = graphene.Field(
        OpportunityType,
        uid=graphene.String(required=True),
        description="Fetch a single opportunity by UID"
    )
    
    # ========== LIST QUERIES ==========
    opportunities = graphene.Field(
        OpportunityListType,
        filter=OpportunityFilterInput(),
        description="Fetch a list of opportunities with optional filters"
    )
    
    my_opportunities = graphene.Field(
        OpportunityListType,
        limit=graphene.Int(default_value=20),
        offset=graphene.Int(default_value=0),
        is_active=graphene.Boolean(),
        description="Fetch opportunities created by current user"
    )
    
    user_opportunities = graphene.Field(
        OpportunityListType,
        user_uid=graphene.String(required=True),
        limit=graphene.Int(default_value=20),
        offset=graphene.Int(default_value=0),
        description="Fetch opportunities created by a specific user"
    )

    opportunity_comments = graphene.Field(
        graphene.List(CommentType),
        opportunity_uid=graphene.String(required=True),
        limit=graphene.Int(default_value=20),
        offset=graphene.Int(default_value=0),
        description="Get comments for an opportunity with pagination"
    )
    
    # ========== RESOLVERS ==========
    
    @login_required
    def resolve_opportunity(self, info, uid):
        """
        Fetch a single opportunity by UID.
        
        Args:
            uid: Opportunity unique identifier
        
        Returns:
            OpportunityType with complete opportunity data
        
        Raises:
            GraphQLError if opportunity not found or deleted
        """
        try:
            user = info.context.user
            opportunity = Opportunity.nodes.get(uid=uid)
            
            # Don't show deleted opportunities
            if opportunity.is_deleted:
                raise GraphQLError("Opportunity not found")
            
            # Check privacy settings
            if opportunity.privacy != 'public':
                if user.is_anonymous:
                    raise GraphQLError("Authentication required to view this opportunity")
                
                current_user = Users.nodes.get(user_id=user.id)
                creator = opportunity.created_by.single()
                
                # Allow creator to always see their own opportunity
                if creator and creator.uid == current_user.uid:
                    return OpportunityType.from_neomodel(opportunity, info, user)
                
                # Check if user has access based on privacy setting
                if opportunity.privacy == 'connections':
                    # Check if user is connected to creator
                    connection_query = """
                    MATCH (user:Users {uid: $user_uid})-[:HAS_USER_CONNECTION]->(conn:Connection {status: 'accepted'})<-[:HAS_USER_CONNECTION]-(creator:Users {uid: $creator_uid})
                    RETURN conn LIMIT 1
                    """
                    results, _ = db.cypher_query(
                        connection_query,
                        {'user_uid': current_user.uid, 'creator_uid': creator.uid}
                    )
                    if not results:
                        raise GraphQLError("You don't have access to this opportunity")
            
            return OpportunityType.from_neomodel(opportunity, info, user)
            
        except Opportunity.DoesNotExist:
            raise GraphQLError("Opportunity not found")
        except GraphQLError:
            raise
        except Exception as error:
            message = getattr(error, 'message', str(error))
            print(f"Error fetching opportunity: {message}")
            raise GraphQLError(f"Failed to fetch opportunity: {message}")

    @login_required
    def resolve_opportunities(self, info, filter=None):
        """
        Fetch a list of opportunities with optional filters.
        
        Supports filtering by job type, location, salary range, skills, etc.
        Results are paginated and can be sorted.
        
        Args:
            filter: OpportunityFilterInput with filter criteria
        
        Returns:
            OpportunityListType with opportunities and pagination metadata
        """
        try:
            user = info.context.user
            
            # Default filter values
            limit = filter.limit if filter and filter.limit else 20
            offset = filter.offset if filter and filter.offset else 0
            
            # Build Cypher query
            query_parts = []
            params = {}
            
            # Base query - get all active, non-deleted opportunities
            query_parts.append("""
                MATCH (opp:Opportunity {is_deleted: false, is_active: true})
                MATCH (opp)-[:CREATED_BY]->(creator:Users)
            """)
            
            # Apply filters
            where_clauses = []
            
            if filter:
                # Opportunity type filter
                if filter.opportunity_type:
                    where_clauses.append("opp.opportunity_type = $opportunity_type")
                    params['opportunity_type'] = filter.opportunity_type
                
                # Search query
                if filter.search_query:
                    where_clauses.append("""
                        (toLower(opp.role) CONTAINS toLower($search_query) 
                        OR toLower(opp.description) CONTAINS toLower($search_query))
                    """)
                    params['search_query'] = filter.search_query
                
                # Job type filter
                if filter.job_type:
                    where_clauses.append("opp.job_type = $job_type")
                    params['job_type'] = filter.job_type
                
                # Location filter
                if filter.location:
                    where_clauses.append("toLower(opp.location) CONTAINS toLower($location)")
                    params['location'] = filter.location
                
                # Remote/Hybrid filters
                if filter.is_remote is not None:
                    where_clauses.append("opp.is_remote = $is_remote")
                    params['is_remote'] = filter.is_remote
                
                if filter.is_hybrid is not None:
                    where_clauses.append("opp.is_hybrid = $is_hybrid")
                    params['is_hybrid'] = filter.is_hybrid
                
                # Salary range filters
                if filter.salary_min:
                    where_clauses.append("opp.salary_max >= $salary_min")
                    params['salary_min'] = filter.salary_min
                
                if filter.salary_max:
                    where_clauses.append("opp.salary_min <= $salary_max")
                    params['salary_max'] = filter.salary_max
                
                # Skills filter (opportunity must have at least one of the skills)
                if filter.skills and len(filter.skills) > 0:
                    where_clauses.append("ANY(skill IN $skills WHERE skill IN opp.skills)")
                    params['skills'] = filter.skills
                
                # Tags filter
                if filter.tags and len(filter.tags) > 0:
                    where_clauses.append("ANY(tag IN $tags WHERE tag IN opp.tags)")
                    params['tags'] = filter.tags
                
                # Creator filter
                if filter.created_by_uid:
                    where_clauses.append("creator.uid = $creator_uid")
                    params['creator_uid'] = filter.created_by_uid
            
            # Add WHERE clause if we have filters
            if where_clauses:
                query_parts.append("WHERE " + " AND ".join(where_clauses))
            
            # Count total (before pagination)
            count_query = " ".join(query_parts) + " RETURN count(opp) as total"
            count_results, _ = db.cypher_query(count_query, params)
            total_count = count_results[0][0] if count_results else 0
            
            # Add sorting
            sort_by = filter.sort_by if filter and filter.sort_by else "created_at"
            sort_order = filter.sort_order if filter and filter.sort_order else "desc"
            
            if sort_by == "engagement":
                # Sort by engagement score (calculated)
                query_parts.append("""
                    WITH opp, creator,
                         size((opp)<-[:HAS_OPPORTUNITY]-(:Like)) * 1.0 +
                         size((opp)<-[:HAS_OPPORTUNITY]-(:Comment)) * 2.0 +
                         size((opp)<-[:HAS_OPPORTUNITY]-(:PostShare)) * 3.0 as engagement_score
                    ORDER BY engagement_score DESC
                """)
            elif sort_by == "salary_max":
                query_parts.append(f"ORDER BY opp.salary_max {sort_order.upper()}")
            else:
                query_parts.append(f"ORDER BY opp.{sort_by} {sort_order.upper()}")
            
            # Add pagination
            query_parts.append("SKIP $offset LIMIT $limit")
            params['offset'] = offset
            params['limit'] = limit
            
            # Return opportunities
            query_parts.append("RETURN opp, creator")
            
            final_query = " ".join(query_parts)
            results, _ = db.cypher_query(final_query, params)
            
            # Convert to OpportunityType
            opportunities = []
            for record in results:
                opp = Opportunity.inflate(record[0])
                opportunities.append(OpportunityType.from_neomodel(opp, info, user))
            
            has_more = (offset + limit) < total_count
            
            return OpportunityListType(
                opportunities=opportunities,
                total_count=total_count,
                has_more=has_more,
                offset=offset
            )
            
        except Exception as error:
            message = getattr(error, 'message', str(error))
            print(f"Error fetching opportunities: {message}")
            raise GraphQLError(f"Failed to fetch opportunities: {message}")
    
    @login_required
    def resolve_my_opportunities(self, info, limit=20, offset=0, is_active=None):
        """
        Fetch opportunities created by the current authenticated user.
        
        Args:
            limit: Number of opportunities to return
            offset: Number of opportunities to skip (pagination)
            is_active: Filter by active status (optional)
        
        Returns:
            OpportunityListType with user's opportunities
        """
        try:
            user = info.context.user
            if user.is_anonymous:
                raise GraphQLError("Authentication required")
            
            current_user = Users.nodes.get(user_id=user.id)
            
            # Build query
            query = """
            MATCH (opp:Opportunity {is_deleted: false})-[:CREATED_BY]->(creator:Users {uid: $user_uid})
            """
            params = {'user_uid': current_user.uid}
            
            # Filter by active status if provided
            if is_active is not None:
                query += " WHERE opp.is_active = $is_active"
                params['is_active'] = is_active
            
            # Count total
            count_query = query + " RETURN count(opp) as total"
            count_results, _ = db.cypher_query(count_query, params)
            total_count = count_results[0][0] if count_results else 0
            
            # Get opportunities
            query += """
            ORDER BY opp.created_at DESC
            SKIP $offset LIMIT $limit
            RETURN opp
            """
            params['offset'] = offset
            params['limit'] = limit
            
            results, _ = db.cypher_query(query, params)
            
            opportunities = []
            for record in results:
                opp = Opportunity.inflate(record[0])
                opportunities.append(OpportunityType.from_neomodel(opp, info, user))
            
            has_more = (offset + limit) < total_count
            
            return OpportunityListType(
                opportunities=opportunities,
                total_count=total_count,
                has_more=has_more,
                offset=offset
            )
            
        except Exception as error:
            message = getattr(error, 'message', str(error))
            print(f"Error fetching user opportunities: {message}")
            raise GraphQLError(f"Failed to fetch opportunities: {message}")
    
    @login_required
    def resolve_user_opportunities(self, info, user_uid, limit=20, offset=0):
        """
        Fetch opportunities created by a specific user.
        
        Args:
            user_uid: UID of the user whose opportunities to fetch
            limit: Number of opportunities to return
            offset: Number of opportunities to skip (pagination)
        
        Returns:
            OpportunityListType with user's opportunities
        """
        try:
            user = info.context.user
            
            # Build query
            query = """
            MATCH (opp:Opportunity {is_deleted: false, is_active: true})-[:CREATED_BY]->(creator:Users {uid: $user_uid})
            """
            params = {'user_uid': user_uid}
            
            # Only show public opportunities or opportunities visible to current user
            # (Future: Add privacy checks here)
            
            # Count total
            count_query = query + " RETURN count(opp) as total"
            count_results, _ = db.cypher_query(count_query, params)
            total_count = count_results[0][0] if count_results else 0
            
            # Get opportunities
            query += """
            ORDER BY opp.created_at DESC
            SKIP $offset LIMIT $limit
            RETURN opp
            """
            params['offset'] = offset
            params['limit'] = limit
            
            results, _ = db.cypher_query(query, params)
            
            opportunities = []
            for record in results:
                opp = Opportunity.inflate(record[0])
                opportunities.append(OpportunityType.from_neomodel(opp, info, user))
            
            has_more = (offset + limit) < total_count
            
            return OpportunityListType(
                opportunities=opportunities,
                total_count=total_count,
                has_more=has_more,
                offset=offset
            )
            
        except Exception as error:
            message = getattr(error, 'message', str(error))
            print(f"Error fetching user opportunities: {message}")
            raise GraphQLError(f"Failed to fetch opportunities: {message}")

    @login_required
    def resolve_opportunity_comments(self, info, opportunity_uid, limit=20, offset=0):
        """
        Get comments for an opportunity with nested replies support.
        Returns top-level comments first, sorted by timestamp.
        """
        try:
            # Verify opportunity exists
            try:
                opportunity = Opportunity.nodes.get(uid=opportunity_uid)
            except Opportunity.DoesNotExist:
                return []

            # Query to get comments with metrics
            query = """
            MATCH (opportunity:Opportunity {uid: $opportunity_uid})-[:HAS_OPPORTUNITY]-(comment:Comment)
            WHERE comment.is_deleted = false
            
            // Check if this is a top-level comment or reply
            OPTIONAL MATCH (comment)-[:REPLIED_TO]->(parent_comment:Comment)
            
            // Get comment metrics
            OPTIONAL MATCH (comment)-[:HAS_VIBE_REACTION]->(vibe:CommentVibe)
            WHERE vibe.is_active = true
            
            // Count replies to this comment
            OPTIONAL MATCH (comment)<-[:REPLIED_TO]-(reply:Comment)
            WHERE reply.is_deleted = false
            
            WITH comment, parent_comment,
                 COUNT(DISTINCT vibe) as vibes_count,
                 COUNT(DISTINCT reply) as reply_count,
                 CASE WHEN parent_comment IS NULL THEN 0 ELSE 1 END as is_reply
            
            // Calculate score
            WITH comment, parent_comment, vibes_count, reply_count, is_reply,
                 CASE 
                    WHEN vibes_count > 0 
                    THEN 2.0 + (vibes_count * 0.5)
                    ELSE 2.0 
                 END as calculated_score
            
            // Order by: top-level comments first, then by timestamp
            ORDER BY is_reply ASC, comment.timestamp DESC
            
            // Pagination
            SKIP $offset
            LIMIT $limit
            
            RETURN comment, parent_comment, vibes_count, reply_count, calculated_score, is_reply
            """
            
            results, _ = db.cypher_query(query, {
                'opportunity_uid': opportunity_uid,
                'offset': offset,
                'limit': limit
            })
            
            if not results:
                return []
            
            # Convert to CommentType objects
            comments = []
            for row in results:
                comment_node = Comment.inflate(row[0])
                comment_type = CommentType.from_neomodel(comment_node, info)
                comments.append(comment_type)
            
            return comments
            
        except Exception as e:
            print(f"Error fetching opportunity comments: {str(e)}")
            return []        
