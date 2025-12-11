import os
from django.core.cache import cache

def get_feed_config(user_id: str) -> dict:
    key = f"feed_ab_config:{user_id}"
    cfg = cache.get(key)
    if cfg:
        return cfg
    connected_ratio = float(os.getenv('FEED_CONNECTED_RATIO', '0.6'))
    exploration_ratio = float(os.getenv('FEED_EXPLORATION_RATIO', '0.2'))
    creator_cap = int(os.getenv('FEED_CREATOR_CAP', '2'))
    session_limit = int(os.getenv('FEED_SESSION_LIMIT', '5'))
    cfg = {
        'connected_ratio': connected_ratio,
        'exploration_ratio': exploration_ratio,
        'creator_cap': creator_cap,
        'session_limit': session_limit,
    }
    cache.set(key, cfg, 600)
    return cfg

