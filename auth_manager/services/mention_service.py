from typing import List, Dict, Any, Optional
from django.core.cache import cache
from django.contrib.auth.models import User
from django.db.models import Q
from neomodel import db
import logging
import json
from auth_manager.Utils import generate_presigned_url
from auth_manager.graphql.types import FileDetailType


logger = logging.getLogger(__name__)



class UserMentionService:
    """
    Simple and effective user mention service for @ tagging.
    Uses Redis caching for fast response times.
    """
    
    def __init__(self):
        self.cache = cache
        self.connection_cache_ttl = 86400  # 24 hours
        self.community_cache_ttl = 300     # 5 minutes
    
    def search_users_for_mention(self, current_user_id: int, query: str, limit: int = 10) -> List[Dict]:
        """
        Main method to search users for @ mentions.
        Returns connected users first, then community users.
        
        Args:
            current_user_id: ID of user making the search
            query: Search query (empty string returns all connections)
            limit: Maximum results to return
            
        Returns:
            List of user dictionaries with id, username, display_name, avatar_url
        """
        original_query = query
        query = query.strip().lower()

        logger.info("Debug mention search", extra={
          "user_id": current_user_id, 
          "original_query": original_query, 
          "processed_query": query, 
          "query_empty": not query
        })
        
        # If query is empty, return all connections
        if not query:
            connected_users = self._get_all_connections(current_user_id, limit)
            logger.info("Returning all connections", extra={
              "user_id": current_user_id, 
              "count": len(connected_users)
            })
            return connected_users
        
        # If query is less than 2 characters, return empty
        # if len(query) < 2:
        #     return []
        
        # Step 1: Search connected users (fastest)
        connected_users = self._search_connected_users(current_user_id, query, limit)
        
        # Step 2: If we need more results, search community
        if len(connected_users) < limit:
            remaining_slots = limit - len(connected_users)
            community_users = self._search_community_users(current_user_id, query, remaining_slots)
            
            # Combine and deduplicate
            all_users = connected_users + community_users
            seen_ids = {user['id'] for user in connected_users}
            
            for user in community_users:
                if user['id'] not in seen_ids and len(connected_users) < limit:
                    connected_users.append(user)
                    seen_ids.add(user['id'])
        
        return connected_users[:limit]
    
    def _search_connected_users(self, user_id: int, query: str, limit: int) -> List[Dict]:
        """Search through user's connections with Redis caching."""
        cache_key = f"user_connections:{user_id}"
        
        # Try cache first
        cached_connections = self.cache.get(cache_key)
        if cached_connections is None:
            cached_connections = self._load_user_connections(user_id)
        
        # Filter cached connections by query
        results = []
        for user_data in cached_connections:
            if self._user_matches_query(user_data, query):
                results.append(user_data)
                if len(results) >= limit:
                    break
        
        return results
    
    def _search_community_users(self, user_id: int, query: str, limit: int) -> List[Dict]:
        """Search community users with caching."""
        cache_key = f"community_search:{query}:{limit}"
        
        cached_results = self.cache.get(cache_key)
        if cached_results is not None:
            # Filter out current user from cached results
            return [user for user in cached_results if user['id'] != user_id]
        
        # Database search
        results = self._database_search_users(user_id, query, limit)
        
        # Cache results
        self.cache.set(cache_key, results, self.community_cache_ttl)
        
        return results
    
    def _load_user_connections(self, user_id: int) -> List[Dict]:
        """Load user connections from Neo4j and cache them."""
        print(f"DEBUG: _load_user_connections called with user_id={user_id}")

        try:
            # Cypher query to get user's connections
            cypher_query = """
            MATCH (u:Users {user_id: $user_id})-[:HAS_CONNECTION]->(conn:Connection)-[:HAS_RECIEVED_CONNECTION]->(connected_user:Users)
            WHERE conn.connection_status = 'Accepted'
            MATCH (connected_user)-[:HAS_PROFILE]->(profile:Profile)
            RETURN DISTINCT
                connected_user.user_id as user_id,
                connected_user.username as username,
                connected_user.first_name as first_name,
                connected_user.last_name as last_name,
                profile.profile_pic_id as profile_pic_id
            LIMIT 500
            """
            print(f"DEBUG: Executing cypher query for user_id={user_id}")

            results, meta = db.cypher_query(cypher_query, {'user_id': str(user_id)})
            print(f"DEBUG: Query returned {len(results)} rows")

            logger.info("Raw query results", extra={"user_id": user_id, "results_count": len(results), "results": results[:2] if results else []})

            if results:
                print(f"DEBUG: First row sample: {results[0]}")

            connections = []
            seen_user_ids = set()

            for row in results:

                avatar_url = ""
                if row[4]:  # profile_pic_id exists
                   try:
                       file_info = generate_presigned_url.generate_file_info(row[4])
                       if file_info and 'url' in file_info:
                          avatar_url = file_info['url']
                   except Exception as e:
                       logger.warning("Error generating avatar URL", extra={"profile_pic_id": row[4], "error": str(e)})

                user_data = {
                    'id': int(row[0]),
                    'username': row[1] or '',
                    'first_name': row[2] or '',
                    'last_name': row[3] or '',
                    'display_name': f"{row[2] or ''} {row[3] or ''}".strip() or row[1],
                    'avatar_url':avatar_url,
                    'is_connection': True
                }
                
                # Build search text for fast matching
                search_parts = [
                    user_data['username'],
                    user_data['first_name'], 
                    user_data['last_name'],
                    user_data['display_name']
                ]
                # search_text = ' '.join(filter(None, search_parts)).lower()

                # graphql_user_data = user_data.copy()
                # user_data['_search_text'] = search_text  # Keep for internal filtering


                user_data['_search_text'] = ' '.join(filter(None, search_parts)).lower()
                
                connections.append(user_data)

                for conn in connections:
                    if '_search_text' in conn:
                        del conn['_search_text']
            
            # Cache connections
            cache_key = f"user_connections:{user_id}"
            self.cache.set(cache_key, connections, self.connection_cache_ttl)
            
            logger.info("Loaded user connections", extra={"user_id": user_id, "count": len(connections)})
            return connections
            
        except Exception as e:
            logger.error("Error loading user connections", user_id=user_id, error=str(e))
            return []
    
    def _database_search_users(self, current_user_id: int, query: str, limit: int) -> List[Dict]:
        """Search users in Django User model and get profile pics from Neo4j."""
        try:
            # Search Django User model
            search_q = Q(
                Q(username__istartswith=query) |
                Q(first_name__istartswith=query) |
                Q(last_name__istartswith=query)
            )
            
            django_users = User.objects.filter(search_q).exclude(
                id=current_user_id
            ).filter(
                is_active=True
            ).values(
                'id', 'username', 'first_name', 'last_name'
            )[:limit]
            
            if not django_users:
                return []
            
            # Get user IDs to query Neo4j for profile pics
            user_ids = [str(user['id']) for user in django_users]
            
            # Query Neo4j for profile pictures
            cypher_query = """
            MATCH (u:Users)-[:HAS_PROFILE]->(p:Profile)
            WHERE u.user_id IN $user_ids
            RETURN u.user_id as user_id, p.profile_pic_id as profile_pic_id
            """
            
            neo4j_results, _ = db.cypher_query(cypher_query, {'user_ids': user_ids})
            
            # Create lookup dict for profile pics
            profile_pics = {int(row[0]): row[1] for row in neo4j_results if row[1]}
            
            results = []
            for user in django_users:
                # Generate avatar URL
                avatar_url = "/static/default_avatar.png"
                profile_pic_id = profile_pics.get(user['id'])
                
                if profile_pic_id:
                    try:
                        file_info = generate_presigned_url.generate_file_info(profile_pic_id)
                        if file_info and 'url' in file_info:
                            avatar_url = file_info['url']
                    except Exception as e:
                        logger.warning("Error generating avatar URL", extra={"profile_pic_id": profile_pic_id, "error": str(e)})
                
                user_data = {
                    'id': user['id'],
                    'username': user['username'],
                    'first_name': user['first_name'] or '',
                    'last_name': user['last_name'] or '',
                    'display_name': f"{user['first_name'] or ''} {user['last_name'] or ''}".strip() or user['username'],
                    'avatar_url': avatar_url,
                    'is_connection': False
                }
                results.append(user_data)
            
            return results
            
        except Exception as e:
            logger.error("Error in database user search", extra={"current_user_id": current_user_id, "query": query, "error": str(e)})
            return []
    
    def _user_matches_query(self, user_data: Dict, query: str) -> bool:
        """Check if user matches search query from start of words."""
        query_lower = query.lower()
    
        # Check if query matches start of any word in username, first_name, last_name, display_name
        fields_to_check = [
           user_data.get('username', ''),
           user_data.get('first_name', ''), 
           user_data.get('last_name', ''),
           user_data.get('display_name', '')
        ]
    
        for field in fields_to_check:
           if field and field.lower().startswith(query_lower):
            return True
        
           # Also check each word in the field
           words = field.lower().split()
           for word in words:
             if word.startswith(query_lower):
                return True
       
        return False
    
    def invalidate_user_connections_cache(self, user_id: int):
        """Invalidate connections cache when user's connections change."""
        cache_key = f"user_connections:{user_id}"
        self.cache.delete(cache_key)
        logger.info("Invalidated user connections cache", extra={"user_id": user_id})

    def _get_all_connections(self, user_id: int, limit: int) -> List[Dict]:
        """Get all user connections without filtering."""
        print(f"DEBUG: _get_all_connections called with user_id={user_id}, limit={limit}")

        cache_key = f"user_connections:{user_id}"
        # self.cache.delete(cache_key)

        # Try cache first
        cached_connections = self.cache.get(cache_key)
        print(f"DEBUG: Cache check - key={cache_key}, found={cached_connections is not None}")
        if cached_connections:
            print(f"DEBUG: Cache hit with {len(cached_connections)} connections")

        if cached_connections is None:
            print(f"DEBUG: Cache miss, loading from database for user_id={user_id}")

            cached_connections = self._load_user_connections(user_id)
            print(f"DEBUG: Loaded {len(cached_connections)} connections from database")

        result = cached_connections[:limit]
        print(f"DEBUG: Returning {len(result)} connections (limit={limit})")
        # Return all connections up to limit
        return cached_connections[:limit]    
