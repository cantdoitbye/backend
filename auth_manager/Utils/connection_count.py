from neomodel import db
from graphql import GraphQLError
from auth_manager.models import ConnectionStats
from auth_manager.models import Users
from connection.models import Connection

def get_received_connections_count(user):
    
    
    user_id=str(user.user_id)
    query = """
    MATCH (u:Users {user_id: $user_id})<-[:HAS_RECIEVED_CONNECTION]-(c:Connection)
    RETURN count(c) 
    """
    results, _ = db.cypher_query(query, {'user_id': user_id})
    
    received_connections_count = results[0][0] if results else 0
    
    user_node=Users.nodes.get(user_id=user_id) #login user
            
    connection_stat =user_node.connection_stat.single()
    connection_stat.received_connections_count = received_connections_count
    connection_stat.save()
    return 

def get_send_connections_count(user):
    
    
    user_id=str(user.user_id)
    query = """
    MATCH (u:Users {user_id: $user_id})<-[:HAS_SEND_CONNECTION]-(c:Connection)
    RETURN count(c) 
    """
    results, _ = db.cypher_query(query, {'user_id': user_id})
    
    send_connections_count = results[0][0] if results else 0
    
    user_node=Users.nodes.get(user_id=user_id) #login user
            
    connection_stat =user_node.connection_stat.single()
    connection_stat.sent_connections_count = send_connections_count
    connection_stat.save()
    return 