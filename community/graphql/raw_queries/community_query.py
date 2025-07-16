get_log_in_user_community_details_query = """
                MATCH (u:Users {email: $user_email})<-[:MEMBER]-(m:Membership)-[:MEMBEROF]->(c:Community)
                WHERE (c.community_type = $community_type OR $community_type IS NULL)
                AND (c.community_circle = $community_circle OR $community_circle IS NULL)

                RETURN c AS community, m AS community_membership
                """

get_log_in_user_sub_community_details_query = """
                MATCH (u:Users {email: $user_email})<-[:MEMBER]-(sm:SubCommunityMembership)-[:MEMBEROF]->(sc:SubCommunity)
                WHERE (sc.sub_community_group_type = $community_type OR $community_type IS NULL)
                AND (sc.sub_community_circle = $community_circle OR $community_circle IS NULL)
                RETURN sc AS subcommunity, sm AS subcommunity_membership
            """
get_log_in_user_communities_query = """
                MATCH (u:Users {email: $user_email})<-[:MEMBER]-(m:Membership)-[:MEMBEROF]->(c:Community)
                RETURN c AS community, m AS community_membership
                """

get_log_in_user_sub_communities_query = """
                MATCH (u:Users {email: $user_email})<-[:MEMBER]-(sm:SubCommunityMembership)-[:MEMBEROF]->(sc:SubCommunity)
                RETURN sc AS subcommunity, sm AS subcommunity_membership
            """

Inner_Community_Member_List_Query = """
        MATCH (c:Community {uid: $uid})-[:MEMBER_OF]->(m:Membership)-[:MEMBER]->(u:Users)-[:HAS_PROFILE]->(p:Profile)
        WHERE m.is_admin=true
        RETURN m,u,p
        ORDER BY m.join_date DESC
        """

Outer_Community_Member_List_Query = """
        MATCH (c:Community {uid: $uid})-[:MEMBER_OF]->(m:Membership)-[:MEMBER]->(u:Users)-[:HAS_PROFILE]->(p:Profile)
        WHERE m.is_admin=false AND (m.can_add_member=true OR m.can_remove_member=true)
        RETURN m,u,p
        ORDER BY m.join_date DESC
        """

Universe_Community_Member_List_Query = """
        MATCH (c:Community {uid: $uid})-[:MEMBER_OF]->(m:Membership)-[:MEMBER]->(u:Users)-[:HAS_PROFILE]->(p:Profile)
        WHERE m.is_admin=false
        RETURN m,u,p
        ORDER BY m.join_date DESC
        """

Inner_Sub_Community_Member_List_Query = """
        MATCH (c:SubCommunity {uid: $uid})-[:MEMBER_OF]->(m:SubCommunityMembership)-[:MEMBER]->(u:Users)-[:HAS_PROFILE]->(p:Profile)
        WHERE m.is_admin=true
        RETURN m,u,p
        ORDER BY m.join_date DESC
        """

Outer_Sub_Community_Member_List_Query = """
        MATCH (c:SubCommunity {uid: $uid})-[:MEMBER_OF]->(m:SubCommunityMembership)-[:MEMBER]->(u:Users)-[:HAS_PROFILE]->(p:Profile)
        WHERE m.is_admin=false AND (m.can_add_member=true OR m.can_remove_member=true)
        RETURN m,u,p
        ORDER BY m.join_date DESC
        """

Universe_Sub_Community_Member_List_Query = """
        MATCH (c:SubCommunity {uid: $uid})-[:MEMBER_OF]->(m:SubCommunityMembership)-[:MEMBER]->(u:Users)-[:HAS_PROFILE]->(p:Profile)
        WHERE m.is_admin=false
        RETURN m,u,p
        ORDER BY m.join_date DESC
        """

fetch_popular_community_feed="""     

        call(){
                
                // First part for Community
                MATCH (c:Community)
                WITH c AS entity
                RETURN entity
                LIMIT 15


                UNION ALL

                MATCH (sc:SubCommunity)
                WITH sc AS entity
                RETURN entity
                LIMIT 15
        }

        RETURN entity
        ORDER by  entity.number_of_members DESC, entity.created_date DESC
        LIMIT 20



"""

fetch_newest_community_feed="""     

        call(){
                
                // First part for Community
                MATCH (c:Community)
                WITH c AS entity
                RETURN entity
                LIMIT 15


                UNION ALL

                MATCH (sc:SubCommunity)
                WITH sc AS entity
                RETURN entity
                LIMIT 15
        }

        RETURN entity
        ORDER by entity.created_date DESC
        LIMIT 20



"""



fetch_popular_community_feed_with_filter="""     

        call(){
                
                // First part for Community
                MATCH (c:Community {community_type:$community_type})
                WITH c AS entity
                RETURN entity
                LIMIT 15


                UNION ALL

                MATCH (sc:SubCommunity {sub_community_group_type:$community_type})
                WITH sc AS entity
                RETURN entity
                LIMIT 15
        }

        RETURN entity
        ORDER by  entity.number_of_members DESC, entity.created_date DESC
        LIMIT 20



"""

fetch_newest_community_feed_with_filter="""     

        call(){
                
                // First part for Community
                MATCH (c:Community{community_type:$community_type})
                WITH c AS entity
                RETURN entity
                ORDER by entity.created_date DESC
                LIMIT 15


                UNION ALL

                MATCH (sc:SubCommunity{sub_community_group_type:$community_type})
                WITH sc AS entity
                RETURN entity
                ORDER by entity.created_date DESC
                LIMIT 15
        }

        RETURN entity
        ORDER by entity.created_date DESC
        LIMIT 20



"""




get_mutual_community_query="""

        call(){
        MATCH (u1:Users{uid:$log_in_user_uid})<-[:MEMBER]-(m1:SubCommunityMembership)<-[:MEMBER_OF]-(sc:SubCommunity)-[:MEMBER_OF]->(m2:SubCommunityMembership)-[:MEMBER]->(u2:Users{uid:$user_uid})
        WITH sc AS entity
                RETURN entity
                LIMIT 20

        UNION ALL

        MATCH (u3:Users{uid:$log_in_user_uid})<-[:MEMBER]-(m4:Membership)<-[:MEMBER_OF]-(c:Community)-[:MEMBER_OF]->(m3:Membership)-[:MEMBER]->(u4:Users{uid:$user_uid})
        WITH c AS entity
                RETURN entity
                LIMIT 20


        }

        RETURN entity
        ORDER by entity.created_date DESC
        LIMIT 20

"""


get_mutual_community_query_with_filter="""

        call(){
        MATCH (u1:Users{uid:$log_in_user_uid})<-[:MEMBER]-(m1:SubCommunityMembership)<-[:MEMBER_OF]-(sc:SubCommunity{sub_community_group_type:$community_type})-[:MEMBER_OF]->(m2:SubCommunityMembership)-[:MEMBER]->(u2:Users{uid:$user_uid})
        WITH sc AS entity
                RETURN entity
                LIMIT 20

        UNION ALL

        MATCH (u3:Users{uid:$log_in_user_uid})<-[:MEMBER]-(m4:Membership)<-[:MEMBER_OF]-(c:Community{community_type:$community_type})-[:MEMBER_OF]->(m3:Membership)-[:MEMBER]->(u4:Users{uid:$user_uid})
        WITH c AS entity
                RETURN entity
                LIMIT 20


        }

        RETURN entity
        ORDER by entity.created_date DESC
        LIMIT 20

"""



get_common_interest_community_query="""

        MATCH (u:Users {uid:$log_in_user_uid})-[:HAS_PROFILE]->(p:Profile)-[:HAS_INTEREST]->(i:Interest)
        MATCH (c:Community)-[:MEMBER_OF]->(m:Membership)-[:MEMBER]->(u2:Users{uid:$user_uid})
        WITH c, i, split(c.name, " ")[0] AS first_word
        WHERE ANY(name IN i.names WHERE toLower(first_word) = toLower(name)) // Match first word with user's interest array
        RETURN c
        LIMIT 20

"""

get_common_interest_community_query_with_filter="""

        MATCH (u:Users {uid:$log_in_user_uid})-[:HAS_PROFILE]->(p:Profile)-[:HAS_INTEREST]->(i:Interest)
        MATCH (c:Community{community_type:$community_type})-[:MEMBER_OF]->(m:Membership)-[:MEMBER]->(u2:Users{uid:$user_uid})
        WITH c, i, split(c.name, " ")[0] AS first_word
        WHERE ANY(name IN i.names WHERE toLower(first_word) = toLower(name)) // Match first word with user's interest array
        RETURN c
        LIMIT 20

"""




Inner_Sub_Community_Member_Count_Query = """
    MATCH (c:SubCommunity {uid: $uid})-[:MEMBER_OF]->(m:SubCommunityMembership)-[:MEMBER]->(u:Users)
    WHERE m.is_admin=true
    RETURN COUNT(m) AS inner_member_count
"""

Outer_Sub_Community_Member_Count_Query = """
    MATCH (c:SubCommunity {uid: $uid})-[:MEMBER_OF]->(m:SubCommunityMembership)-[:MEMBER]->(u:Users)
    WHERE m.is_admin=false AND (m.can_add_member=true OR m.can_remove_member=true)
    RETURN COUNT(m) AS outer_member_count
"""

Universe_Sub_Community_Member_Count_Query = """
    MATCH (c:SubCommunity {uid: $uid})-[:MEMBER_OF]->(m:SubCommunityMembership)-[:MEMBER]->(u:Users)
    WHERE m.is_admin=false
    RETURN COUNT(m) AS universe_member_count
"""

Combined_Community_Member_Count_Query = """
    MATCH (c:Community {uid: $uid})-[:MEMBER_OF]->(m:Membership)-[:MEMBER]->(u:Users)
    RETURN 
        COUNT(CASE WHEN m.is_admin=true THEN m END) AS inner_member_count,
        COUNT(CASE WHEN m.is_admin=false AND (m.can_add_member=true OR m.can_remove_member=true) THEN m END) AS outer_member_count,
        COUNT(CASE WHEN m.is_admin=false THEN m END) AS universe_member_count
"""

Combined_Sub_Community_Member_Count_Query = """
    MATCH (c:SubCommunity {uid: $uid})-[:MEMBER_OF]->(m:SubCommunityMembership)-[:MEMBER]->(u:Users)
    RETURN 
        COUNT(CASE WHEN m.is_admin=true THEN m END) AS inner_member_count,
        COUNT(CASE WHEN m.is_admin=false AND (m.can_add_member=true OR m.can_remove_member=true) THEN m END) AS outer_member_count,
        COUNT(CASE WHEN m.is_admin=false THEN m END) AS universe_member_count
"""
