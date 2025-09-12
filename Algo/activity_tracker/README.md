# Activity Tracker

A comprehensive activity tracking system for the Ooumph platform that captures user interactions to power personalized feed algorithms.

## Features

- **Activity Tracking**: Record various user interactions (likes, comments, shares, etc.)
- **Engagement Scoring**: Calculate user engagement metrics
- **Real-time Processing**: Process activities as they happen
- **Analytics**: Generate insights from user activities
- **API-First**: RESTful API for easy integration

## Activity Types

### Engagement
- Vibe interactions
- Comments & replies
- Shares & reposts
- Saves & bookmarks
- Media expansions (image/video clicks)

### User Interactions
- Profile visits
- Profile vibes

### Content Creation
- Post creation
- Content type tracking
- Hashtag usage

### Search & Discovery
- Explore clicks
- Search queries

### Negative Signals
- Content reports
- Hide actions

### Social Graph
- Circle updates (inner/outer/universal)
- Group/community joins

## API Endpoints

### Activities
- `GET /activities/` - List user activities
- `POST /activities/` - Create a new activity
- `GET /activities/recent/` - Get recent activities

### Engagement
- `GET /engagement/` - Get user engagement scores
- `POST /engagement/recalculate/` - Recalculate engagement scores

### Statistics
- `GET /stats/` - Get activity statistics

## Integration with Feed Algorithm

The activity tracker provides valuable signals for the feed algorithm:

1. **Content Relevance**: Track which content types users engage with
2. **User Preferences**: Learn from user interactions to improve recommendations
3. **Social Signals**: Leverage social graph for better content distribution
4. **Negative Feedback**: Avoid showing similar content to reported/hidden items

## Setup

1. Add 'activity_tracker' to INSTALLED_APPS
2. Run migrations: `python manage.py migrate`
3. Configure activity tracking in your views/signals

## Configuration

```python
# settings.py

# Activity tracking settings
ACTIVITY_TRACKING = {
    'AUTO_TRACK': True,  # Enable automatic activity tracking
    'ANONYMIZE_IP': True,  # Anonymize IP addresses
    'PRUNE_AFTER_DAYS': 90,  # Auto-delete activities older than X days
}
```

## Usage

### Tracking an Activity

```python
from activity_tracker.models import UserActivity

# Track a like activity
activity = UserActivity.objects.create(
    user=request.user,
    activity_type='vibe',
    content_object=post,  # The content being interacted with
    metadata={'value': 'positive'}  # Additional context
)
```

### Getting Engagement Scores

```python
from activity_tracker.models import UserEngagementScore

# Get a user's engagement score
score = UserEngagementScore.objects.get(user=user)
print(f"Engagement Score: {score.engagement_score}")
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
