from datetime import datetime, timedelta, timezone

def time_ago(created_at: datetime) -> str:
    
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    # Get the current time as timezone-aware in UTC
    now = datetime.now(timezone.utc)
    diff = now - created_at
    
    
    # If time difference is less than 1 day (24 hours)
    if diff < timedelta(days=1):
        hours = diff.seconds // 3600
        if hours > 0:
            return f"{hours} hours ago"
        minutes = diff.seconds // 60
        if minutes > 0:
            return f"{minutes} minutes ago"
        return "just now"

    # If time difference is less than 28 days (4 weeks)
    elif diff < timedelta(days=28):
        days = diff.days
        return f"{days} days ago" if days > 1 else "1 day ago"

    # If time difference is less than 52 weeks (1 year)
    elif diff < timedelta(weeks=52):
        weeks = diff.days // 7
        return f"{weeks} weeks ago" if weeks > 1 else "1 week ago"

    # If time difference is 1 year or more
    else:
        years = diff.days // 365
        return f"{years} years ago" if years > 1 else "1 year ago"


