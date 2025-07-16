from neomodel import db

def get_blocked_users(user_id):
    cypher_query = '''
    MATCH (u:Users {user_id: $user_id})-[:HAS_BLOCK]->(b:Block)-[:BLOCKED]->(blocked:Users)
    RETURN blocked
    '''
    results, columns = db.cypher_query(cypher_query, {'user_id': str(user_id)})
    blocked_users = [record[0] for record in results]
    return blocked_users
