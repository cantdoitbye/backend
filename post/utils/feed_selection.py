def creator_key(row):
    try:
        u = row[1] if len(row) > 1 else None
        if isinstance(u, dict):
            return u.get('uid') or u.get('user_id') or 'unknown'
        return getattr(u, 'uid', None) or getattr(u, 'user_id', None) or 'unknown'
    except Exception:
        return 'unknown'

def post_type_of(row):
    try:
        p = row[0] if row else {}
        return p.get('post_type') if isinstance(p, dict) else getattr(p, 'post_type', None)
    except Exception:
        return None

def diversify(rows):
    seq = []
    last_creator = None
    last_type = None
    used = [False] * len(rows)
    remaining = len(rows)
    idx = 0
    while remaining > 0:
        picked = False
        n = len(rows)
        for _ in range(n):
            i = idx % n
            idx += 1
            if used[i]:
                continue
            ck = creator_key(rows[i])
            pt = post_type_of(rows[i])
            if ck == last_creator or (pt is not None and pt == last_type):
                continue
            used[i] = True
            seq.append(rows[i])
            last_creator = ck
            last_type = pt
            remaining -= 1
            picked = True
            break
        if not picked:
            for j in range(n):
                if not used[j]:
                    used[j] = True
                    seq.append(rows[j])
                    remaining -= 1
                    break
    return seq

def is_connected(row):
    try:
        return bool(row[4]) if len(row) > 4 else False
    except Exception:
        return False

def enforce_creator_cap(rows, max_per_creator=2):
    cap = {}
    picked = []
    for r in rows:
        ck = creator_key(r)
        cur = cap.get(ck, 0)
        if cur < max_per_creator:
            picked.append(r)
            cap[ck] = cur + 1
    return picked

def enforce_creator_cap_with_counts(rows, max_per_creator=2, session_counts=None, session_limit=5):
    cap = {}
    picked = []
    for r in rows:
        ck = creator_key(r)
        sc = 0
        if session_counts:
            sc = int(session_counts.get(str(ck), 0))
        if sc >= session_limit:
            continue
        cur = cap.get(ck, 0)
        if cur < max_per_creator:
            picked.append(r)
            cap[ck] = cur + 1
    return picked

def compose_with_quotas(scored_rows, first, connected_ratio=0.6, max_per_creator=2, session_counts=None, session_limit=5):
    connected = [r for r in scored_rows if is_connected(r)]
    other = [r for r in scored_rows if not is_connected(r)]
    target_connected = int(first * connected_ratio)
    target_other = first - target_connected
    conn_selected = enforce_creator_cap_with_counts(connected, max_per_creator, session_counts, session_limit)[:target_connected]
    other_selected = enforce_creator_cap_with_counts(other, max_per_creator, session_counts, session_limit)[:target_other]
    combined = conn_selected + other_selected
    if len(combined) < first:
        remaining = [r for r in scored_rows if r not in combined]
        combined += enforce_creator_cap(remaining, max_per_creator)[:first - len(combined)]
    return diversify(combined)[:first]

def inject_exploration(selected_rows, trending_rows, exploration_count):
    used = set()
    out = []
    for r in selected_rows:
        pd = r[0] if r else {}
        uid = pd.get('uid') if isinstance(pd, dict) else getattr(pd, 'uid', None)
        if uid:
            used.add(uid)
        out.append(r)
    added = 0
    for tr in trending_rows:
        if added >= exploration_count:
            break
        pd = tr[0] if tr else {}
        uid = pd.get('uid') if isinstance(pd, dict) else getattr(pd, 'uid', None)
        if uid and uid not in used:
            out.append(tr)
            used.add(uid)
            added += 1
    return out
