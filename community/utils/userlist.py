from neomodel import db
from graphql import GraphQLError
from auth_manager.models import ConnectionStats
from auth_manager.models import Users
from connection.models import Connection

def get_unavailable_list_user(user_uid_list):
        query = """
                    UNWIND $useruid as useruid
                    MATCH (u:Users)
                    WHERE u.uid = useruid
                    RETURN useruid as existing_users
                """
        
        # results, meta = db.cypher_query(query, {"contact": user_uid_list})
        
        existing_users, meta = db.cypher_query(query, {"useruid": user_uid_list})
        existing_users = [row[0] for row in existing_users]
        
        unavailable_users = [user_uid for user_uid in user_uid_list if user_uid not in existing_users]
        return unavailable_users