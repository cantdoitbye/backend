import logging

logger = logging.getLogger(__name__)


class ActivityService:
    def __init__(self):
        pass

    @staticmethod
    def track_content_interaction(user=None, content_type=None, content_id=None, interaction_type=None, **kwargs):
        return True

    @staticmethod
    def track_content_interaction_by_id(user_id=None, content_type=None, interaction_type=None, content_id=None, metadata=None):
        return True

    def track_activity_async(self, *args, **kwargs):
        return True

