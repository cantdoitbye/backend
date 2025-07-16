from django.core.cache import cache
from community.models import Community
from community.graphql.raw_queries.community_query import *
from neomodel import db

class CommunityMemberCountManager:
    def __init__(self, community_uid):
        self.community_uid = community_uid
        self.redis_key_inner = f"community:{community_uid}:innermembercount"
        self.redis_key_outer = f"community:{community_uid}:outermembercount"
        self.redis_key_universe = f"community:{community_uid}:universemembercount"
        self.redis_key_membercount = f"community:{community_uid}:membercount"

    def get_counts(self):
        """Retrieve member counts from Redis."""
        return {
            "innermembercount": int(cache.get(self.redis_key_inner) or 0),
            "outermembercount": int(cache.get(self.redis_key_outer) or 0),
            "universemembercount": int(cache.get(self.redis_key_universe) or 0),
            "membercount": int(cache.get(self.redis_key_membercount) or 0),
        }

    def set_counts(self, innercount, outercount, universecount, membercount):
        """Set member counts in Redis."""
        cache.set(self.redis_key_inner, innercount, timeout=None)
        cache.set(self.redis_key_outer, outercount, timeout=None)
        cache.set(self.redis_key_universe, universecount, timeout=None)
        cache.set(self.redis_key_membercount, membercount, timeout=None)

    def update_counts_if_needed(self,current_membercount,communitytype):
        """Update Redis counts if the database member count doesn't match the cached count."""
        try:
            
            cached_membercount = cache.get(self.redis_key_membercount)

            # Update counts if cache is stale or unset
            if cached_membercount is None or current_membercount != cached_membercount:
                
                membercount=current_membercount

                if communitytype=="community":
                    params = {"uid":self.community_uid}    
                    results1,_ = db.cypher_query(Combined_Community_Member_Count_Query,params)
                    
                    for result in results1:
                        innercount=result[0]
                        outercount=result[1]
                        universecount=result[2]
                else:
                    params = {"uid":self.community_uid}    
                    results2,_ = db.cypher_query(Combined_Sub_Community_Member_Count_Query,params)
                    
                    for result in results2:
                        innercount=result[0]
                        outercount=result[1]
                        universecount=result[2]
                
                self.set_counts(innercount, outercount, universecount, membercount)

            # Return updated counts
            return self.get_counts()
        except Community.DoesNotExist:
            raise ValueError(f"Community with UID '{self.community_uid}' does not exist.")
