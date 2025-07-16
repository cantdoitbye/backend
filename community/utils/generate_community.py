from neomodel import db
from community.models import Community  # Assuming you have a Community model
from auth_manager.models import Profile  # Your Profile model path
from auth_manager.models import Interest
from community.models import GeneratedCommunityUserManager


interest_synonyms = {
    "Music": ["Singing", "Playing Instruments", "Musician", "Composing", "Songwriting", "Band", "Music"],
    "Fitness": ["Gym", "Workout", "Bodybuilding", "Exercise", "Yoga", "Pilates", "Running", "Jogging", "Health & Fitness"],
    "Sports": ["Football", "Soccer", "Cricket", "Hockey", "Basketball", "Tennis", "Badminton", "Rugby", "Team Sports", "Individual Sports"],
    "Art": ["Painting", "Drawing", "Sketching", "Sculpting", "Designing", "Illustration", "Arts & Culture"],
    "Traveling": ["Travelling", "Exploring", "Adventure", "Backpacking", "Tourism", "Travel", "Adventure Travel", "Cultural Travel"],
    "Movies": ["Film", "Cinema", "Movie", "Filmmaking", "Directing", "Acting", "Film & Cinema", "TV & Streaming"],
    "Communication": ["Public Speaking", "Presentation", "Negotiation", "Debating", "Storytelling", "Networking", "Communication Skills"],
    "Photography": ["Camera Techniques", "Editing", "Videography", "Portraits", "Landscapes", "Wildlife", "Street Photography", "Photography & Videography"],
    "Gaming": ["PC Gaming", "Console Gaming", "Mobile Gaming", "Esports Tournaments", "Gaming & Esports"],
    "Technology": ["Computing", "Electronics & Gadgets", "Cybersecurity", "Space Exploration", "Green Technology", "Technology & Science"],
    "Entrepreneurship": ["Startups", "Business", "Innovation", "Entrepreneurship", "Marketing & Sales"],
    "Education": ["Online Learning", "Language Learning", "STEM Education", "EdTech", "Education & Learning"],
    "Finance": ["Stock Market", "Cryptocurrency", "Investing", "Real Estate", "Financial Independence", "Finance & Investing"],
    "Lifestyle": ["Fashion", "Beauty", "Personal Finance", "Lifestyle & Hobbies"],
    "Parenting": ["Pregnancy", "Child Development", "Parenting Tips", "Parenting & Family"],
    "Relationships": ["Dating", "Mental Health", "Relationships", "Spirituality", "Relationships & Community"],
    "Food": ["Cuisines", "Cooking", "Beverages", "Diet", "Food & Drink"],
    "Environment": ["Wildlife Conservation", "Ecosystems", "Sustainability", "Climate Change", "Nature & Environment"],
    "Crafts": ["Handmade Crafts", "Upcycling", "DIY Projects", "Paper Crafts", "DIY & Crafts"],
    "Wellness": ["Physical Wellness", "Mental Wellness", "Holistic Living", "Health & Wellness"],
    "Vehicles": ["Cars", "Motorcycles", "Eco-Friendly Vehicles", "Automobiles & Vehicles"],
    "Personal Development": ["Self-Improvement", "Confidence Building", "Productivity", "Personal Development"],
    "History": ["Ancient Civilizations", "Modern History", "Philosophy", "Mythology & Folklore", "History & Philosophy"],
    "Marketing": ["Content Creation", "Branding", "Digital Advertising", "Analytics", "Social Media & Digital Marketing"]
}


def normalize_interest(interest_name):
    # Convert the input interest name to lowercase for case-insensitive comparison
    interest_name_lower = interest_name.lower()

    # Normalize the interest name by checking the synonym mapping
    for key, synonyms in interest_synonyms.items():
        # Convert the main key and all synonyms to lowercase for comparison
        if interest_name_lower == key.lower() or interest_name_lower in [syn.lower() for syn in synonyms]:
            return key  # Return the main category (e.g., "music")
    
    return interest_name 

def generate_communities_based_on_interest():
    # Cypher query to get profiles with interests
    query = """
    MATCH (p:Profile)-[:HAS_INTEREST]->(i:Interest)
    RETURN i.names AS interest_names, collect(distinct p.user_id) AS user_ids
    """
    
    results, meta = db.cypher_query(query)
    # print(results)
    
    
    interest_communities = {}  # Dictionary to hold communities grouped by normalized interest

    for row in results:
        interest_names = row[0]  # List of interest names
        user_ids = row[1]  # List of user_ids who share those interests

        # Normalize each interest name
        normalized_interests = [normalize_interest(interest) for interest in interest_names]
        
        # Group users by normalized interest names
        for norm_interest in normalized_interests:
            if norm_interest not in interest_communities:
                interest_communities[norm_interest] = set()  # Initialize a set for unique users
            interest_communities[norm_interest].update(user_ids)  # Add users to the community


    filtered_communities = {interest: user_ids for interest, user_ids in interest_communities.items() if len(user_ids) >= 3}

    if not filtered_communities:
        return "No users found with similar interests."
    
    message=create_communities_from_filtered(filtered_communities)
    return message



def create_communities_from_filtered(filtered_communities):
    # Fetch all existing communities from the CommunityUserManager in one query
    existing_communities = {
        community.community_name: community for community in GeneratedCommunityUserManager.objects.all()
    }
    message = "" 
    for interest, user_ids in filtered_communities.items():
        if interest in existing_communities:
            new_users_added = False
            # Community exists, so add new user IDs if they're not already in the list
            community_obj = existing_communities[interest]
            for user_id in user_ids:
                result=community_obj.add_user_to_community(user_id)  # Adds user only if not already present
                if result:
                    new_users_added = True

            if new_users_added:
                message += f"Updated community '{interest}': new users found with this interest.\n"
            else:
                message += f"No new users found with '{interest}' to existing community '{interest}'.\n"
        else:
            # Community does not exist, so create a new Community object
            new_community = Community(
            name=interest,
            description=f"Welcome to the {interest} Community—a place for passionate individuals who share a love for all things {interest}! Whether you're a seasoned expert or just getting started, this community is dedicated to exploring, learning, and sharing experiences in the world of {interest}.",
            community_circle="Outer",
            community_type="interest group",
            category="public",
            group_icon_id="37" ,
            generated_community=True, # Assuming this is fetched from environment variables or elsewhere
            only_admin_can_message=False,
            only_admin_can_add_member=False,
            only_admin_can_remove_member=True
        )

            new_community.save()  # Save the newly created community
            
            # Also store the community details in CommunityUserManager
            new_community_user_manager = GeneratedCommunityUserManager(
                community_uid=new_community.uid,  # Using the new Community's ID as the UID
                community_name=interest,
                user_ids=list(user_ids)  # Add all user IDs for this new community
            )
            new_community_user_manager.save()

            message += f"Created new community '{interest}'.\n"

    
    return message
    