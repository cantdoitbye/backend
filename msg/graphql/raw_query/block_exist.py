from neomodel import db

def relationship_exists(blocker, blocked):
    cypher_query = '''
    MATCH (blocker:Users {user_id: $blocker_id})-[:HAS_BLOCK]->(block:Block)-[:BLOCKED]->(blocked:Users {uid: $blocked_id})
    RETURN block
    '''
    results, _ = db.cypher_query(cypher_query, {'blocker_id': str(blocker.user_id), 'blocked_id': str(blocked.uid)})
    return len(results) > 0