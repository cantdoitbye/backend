from post.models import PostReactionManager
from vibe_manager.models import IndividualVibe

class PostReactionUtils:
    reaction_manager_map = {}

    @classmethod
    def initialize_map(cls, results):
        """
        Initialize the reaction_manager_map using the results.
        """
        uids = [post[0].get('uid') for post in results]
        reaction_managers = PostReactionManager.objects.filter(post_uid__in=uids)
        cls.reaction_manager_map = {manager.post_uid: manager for manager in reaction_managers}

    @classmethod
    def get_reaction_manager(cls, uid):
        """
        Retrieve the PostReactionManager for a given post_uid.
        """
        return cls.reaction_manager_map.get(uid)
    

class IndividualVibeManager:
    _stored_data = None  # Private variable to store the fetched data

    @classmethod
    def store_data(cls):
        """
        Retrieve and store the first 10 IndividualVibe objects.
        """
        cls._stored_data = list(IndividualVibe.objects.all()[:10])

    @classmethod
    def get_data(cls):
        """
        Retrieve the stored IndividualVibe objects.
        """
        if cls._stored_data is None:
            raise ValueError("No data has been stored yet. Call `store_data` to fetch and store data.")
        return cls._stored_data

