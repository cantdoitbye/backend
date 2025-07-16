import random
import re
from rapidfuzz import process, fuzz

def generate_username_suggestions(base_username, email, existing_usernames):
    def add_variations(base_name):
        variations = [
            f"{base_name}{random.randint(1, 999)}",
            f"{base_name}_{random.randint(1, 999)}",
            f"{base_name}{random.choice(['123', '456', '789'])}",
            f"{base_name}_{random.choice(['123', '456', '789'])}",
            f"{base_name}{random.randint(1000, 9999)}",
            f"{base_name}_{random.randint(1000, 9999)}",
            f"{base_name}{random.choice(['x', 'y', 'z'])}{random.randint(1, 99)}",
        ]
        
        if len(base_name) > 2:
            variations.extend([
                f"{base_name[:2]}_{base_name[2:]}",
                f"{base_name[:3]}_{base_name[3:]}",
                f"{base_name[:4]}_{base_name[4:]}",
                f"{base_name}{random.choice(['x', 'y', 'z'])}",
                f"{base_name[:1]}_{base_name[1:]}",
                f"{base_name[:1]}{random.randint(1, 99)}_{base_name[1:]}",
                f"{base_name}{random.randint(100, 999)}",
                f"{base_name}_{random.randint(100, 999)}",
                f"{base_name}{random.choice(['a', 'b', 'c'])}{random.randint(1, 99)}",
            ])
        
        return variations

    def filter_username_pattern(usernames):
        username_pattern = r'^[a-z0-9_]+$'
        return [username for username in usernames if re.match(username_pattern, username) and '__' not in username]

    base_username = base_username.lower()
    email = email.lower()

    suggestions = set()
    potential_usernames = set(add_variations(base_username))

    if email:
        email_base = email.split('@')[0]
        potential_usernames.update(add_variations(email_base))
        
    scored_suggestions = []
    for suggestion in potential_usernames:
        matches = process.extract(suggestion, existing_usernames, limit=5, scorer=fuzz.ratio)
        max_score = max(matches, key=lambda x: x[1])[1] if matches else 0
        if not matches or all(match[1] < 80 for match in matches):
            scored_suggestions.append((suggestion, max_score))

    valid_suggestions = filter_username_pattern([s[0] for s in scored_suggestions if s[0] not in existing_usernames])

    if not valid_suggestions:
        valid_suggestions = filter_username_pattern([name for name in potential_usernames if name not in existing_usernames])

    base_top_suggestions = process.extract(base_username, valid_suggestions, limit=4, scorer=fuzz.ratio)
    email_top_suggestions = process.extract(email.split('@')[0], valid_suggestions, limit=4, scorer=fuzz.ratio)
    
    top_suggestions = list(set([suggestion[0] for suggestion in base_top_suggestions + email_top_suggestions]))[:4]
    return top_suggestions
