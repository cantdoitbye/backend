create_tag_and_relationship_query = """
    UNWIND $keywords AS tag
    MERGE (tagNode:Tag {name: tag})
    WITH tagNode
    MATCH (post:Post {uid: $uid})
    MERGE (post)-[r:TAGGED_WITH_KEYWORD]->(tagNode)
    SET r.weight = 0.5
    MERGE (tagNode)-[r_reverse:TAGGED_WITH_KEYWORD]->(post)
    SET r_reverse.weight = 0.5;
"""