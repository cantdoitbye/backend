from django.core.cache import cache


def create_story_cache_key(story_uid):
    """
    Creates a cache key for the given story_uid with a 24-hour expiration.
    """
    story_cache_key = f"story_view:{story_uid}"
    
    # Set an empty value in the cache with a 24-hour expiration
    cache.set(story_cache_key, set(), timeout=86400)
    
    # print(f"Cache key {story_cache_key} created with 24-hour expiration.")
    

def check_story_cache_key_exists(story_uid):
    """
    Checks if a cache key for the given story_uid exists in Redis.
    Returns True if the key exists, otherwise False.
    """
    story_cache_key = f"story_view:{story_uid}"
    
    # Check if the key exists in the cache
    exists = cache.get(story_cache_key) is not None
    
    # print(f"Cache key {story_cache_key} exists: {exists}")
    return exists




def add_story_view(story_uid, user_id):
    """
    Adds a user's view to a specific story using Django's cache.
    Each view is stored as a unique user ID in a list keyed by the story ID.
    """
    story_view_key = f"story_view:{story_uid}"
    
    # Get the current list of viewers or create an empty set if it doesn't exist
    viewers = cache.get(story_view_key, set())
    
    # Add the user_id to the set of viewers
    viewers.add(user_id)
    
    # Save the updated viewers list back to the cache with a 24-hour expiration
    cache.set(story_view_key, viewers, timeout=86400)

    # Print the cached value for debugging
    # print(f"Cache content for key {story_view_key}: {cache.get(story_view_key)}")



def has_user_viewed_story(story_uid, user_id):
    """
    Checks if a user has already viewed a specific story.
    Returns True if the user ID is in the cached set for the story, False otherwise.
    """
    story_view_key = f"story_view:{story_uid}"
    viewers = cache.get(story_view_key, set())
    
    # Check if the user_id is in the set of viewers
    return user_id in viewers

def get_story_views_count(story_uid):
    """
    Returns the count of unique views for a specific story.
    If no views exist, it returns 0.
    """
    story_view_key = f"story_view:{story_uid}"
    viewers = cache.get(story_view_key, set())
    
    # Return the number of unique viewers
    return len(viewers)

def get_story_views_list(story_uid):
    """
    Returns the count of unique views for a specific story.
    If no views exist, it returns 0.
    """
    story_view_key = f"story_view:{story_uid}"
    viewers = cache.get(story_view_key, set())
    
    # Return the number of unique viewers
    return list(viewers)


def store_user_data_in_cache(user_node):
    """
    Stores the user's email and other details in the Django cache with a 24-hour expiration.
    If the data already exists in the cache, it will not overwrite it.

    :param user_node: The user node object containing user details (e.g., from the Neo4j model)
    """
    # Extract fields from the user_node
    uid=user_node.uid
    user_id = user_node.user_id
    email = user_node.email
    username = user_node.username
    first_name = user_node.first_name  
    last_name = user_node.last_name    
    user_type = user_node.user_type    

    profile_node=user_node.profile.single()

    profile_uid = profile_node.uid
    gender = profile_node.gender
    phone_number = profile_node.phone_number
    lives_in = profile_node.lives_in
    profile_pic_id = profile_node.profile_pic_id
    
    


    # Prepare the user data to store in the cache
    user_data = {
        'uid': uid,
        'user_id': user_id,
        'email': email,
        'username': username,
        'first_name': first_name,
        'last_name': last_name,
        'user_type': user_type,
        'profile_uid': profile_uid, 
        'gender': gender,
        'phone_number': phone_number,
        'lives_in': lives_in,
        'profile_pic_id': profile_pic_id,
        
    }
    
    # Create the cache key
    cache_key = f"user:{user_id}"

    # Use cache.add() to store the data only if the key doesn't already exist
    if cache.add(cache_key, user_data, timeout=86400):
        print(f"User {user_id} details have been stored in Django cache with a 24-hour expiration.")
    else:
        print(f"User {user_id} details already exist in the cache. No changes made.")


def get_user_data_from_cache(user_id):
    """
    Retrieves the user's details from the Django cache.
    
    :param user_id: The user ID to retrieve the data for
    :return: A dictionary containing user details (email, name, etc.) or None if not found
    """
    # Create the cache key based on the user_id
    cache_key = f"user:{user_id}"

    # Retrieve the user data from the cache
    user_data = cache.get(cache_key)

    # If the data is found in the cache, return it; otherwise, return None
    if user_data:
        return user_data
    else:
        return None
    
def get_story_vibes_count(story_uid):
    """
    Get the total vibes count for a story by counting StoryReaction nodes.
    """
    try:
        from story.models import Story
        from neomodel import db
        
        # Count reactions directly from Neo4j
        query = """
        MATCH (s:Story {uid: $story_uid})<-[:HAS_REACTION]-(r:StoryReaction)
        WHERE r.is_deleted = false
        RETURN count(r) as vibe_count
        """
        results, _ = db.cypher_query(query, {"story_uid": story_uid})
        return results[0][0] if results else 0
    except Exception as e:
        print(f"Error getting vibes count for story {story_uid}: {e}")
        return 0


def get_category_vibes_count(story_uids_list):
    """
    Get total vibes count for multiple stories in a category.
    """
    if not story_uids_list:
        return 0
    
    total_vibes = 0
    for story_uid in story_uids_list:
        if check_story_cache_key_exists(story_uid):
            total_vibes += get_story_vibes_count(story_uid)
    
    return total_vibes



    
