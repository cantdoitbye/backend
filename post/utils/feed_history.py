from django.core.cache import cache
from datetime import datetime
_mem = {}

def _today_key(user_id: str) -> str:
    d = datetime.utcnow().strftime('%Y-%m-%d')
    return f"feed_viewed:{user_id}:{d}"

def get_viewed_today(user_id: str) -> set:
    key = _today_key(user_id)
    data = cache.get(key)
    if not data:
        data = _mem.get(key)
    if not data:
        return set()
    return set(data)

def mark_viewed(user_id: str, post_uids: list) -> None:
    key = _today_key(user_id)
    cur = cache.get(key) or _mem.get(key) or []
    s = set(cur)
    for uid in post_uids:
        if uid:
            s.add(str(uid))
    cache.set(key, list(s), 86400)
    _mem[key] = list(s)

def _hidden_key(user_id: str) -> str:
    d = datetime.utcnow().strftime('%Y-%m-%d')
    return f"feed_hidden:{user_id}:{d}"

def get_hidden_today(user_id: str) -> set:
    k = _hidden_key(user_id)
    v = cache.get(k)
    if not v:
        v = _mem.get(k)
    if not v:
        return set()
    return set(v)

def hide_post_today(user_id: str, post_uid: str) -> None:
    k = _hidden_key(user_id)
    cur = cache.get(k) or _mem.get(k) or []
    s = set(cur)
    if post_uid:
        s.add(str(post_uid))
    cache.set(k, list(s), 86400)
    _mem[k] = list(s)

def _muted_key(user_id: str) -> str:
    return f"feed_muted:{user_id}"

def get_muted_creators(user_id: str) -> set:
    k = _muted_key(user_id)
    v = cache.get(k)
    if not v:
        v = _mem.get(k)
    if not v:
        return set()
    return set(v)

def mute_creator(user_id: str, creator_uid: str) -> None:
    k = _muted_key(user_id)
    cur = cache.get(k) or _mem.get(k) or []
    s = set(cur)
    if creator_uid:
        s.add(str(creator_uid))
    cache.set(k, list(s), 2592000)
    _mem[k] = list(s)

def _count_key(user_id: str) -> str:
    d = datetime.utcnow().strftime('%Y-%m-%d')
    return f"feed_creator_counts:{user_id}:{d}"

def get_creator_counts(user_id: str) -> dict:
    k = _count_key(user_id)
    v = cache.get(k)
    if not v:
        v = _mem.get(k)
    if not v:
        return {}
    return dict(v)

def increment_creator_counts(user_id: str, creator_uid: str, inc: int = 1) -> None:
    if not creator_uid:
        return
    k = _count_key(user_id)
    cur = cache.get(k) or _mem.get(k) or {}
    cur[str(creator_uid)] = int(cur.get(str(creator_uid), 0)) + int(inc)
    cache.set(k, cur, 86400)
    _mem[k] = cur
