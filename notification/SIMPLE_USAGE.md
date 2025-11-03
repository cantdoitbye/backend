# Global Unified Notification Service - Usage Guide

## Simple Usage

The global notification service is template-driven and very easy to use.

### Basic Pattern

```python
from notification.global_service import GlobalNotificationService

# Create service instance
service = GlobalNotificationService()

# Send notification
service.send(
    event_type="new_post_from_connection",
    recipients=[
        {'device_id': 'device_token_1', 'uid': 'user_123'},
        {'device_id': 'device_token_2', 'uid': 'user_456'},
    ],
    username="John Doe",
    post_id="post_789"
)
```

That's it! The service will:
1. Format the notification using the template
2. Send to all recipients
3. Store in PostgreSQL
4. Handle retries automatically

## Real Examples

### Example 1: Post Comment
```python
from notification.global_service import GlobalNotificationService

# In your CreateComment mutation
service = GlobalNotificationService()
service.send(
    event_type="new_comment_on_post",
    recipients=[{'device_id': post_creator_device_id, 'uid': post_creator_uid}],
    username=commenter.username,
    comment_text=comment.text[:50],
    post_id=post.uid
)
```

### Example 2: Community Post
```python
from notification.global_service import GlobalNotificationService

# In your CreateCommunityPost mutation
service = GlobalNotificationService()
service.send(
    event_type="new_community_post",
    recipients=community_members,  # List of {'device_id': '...', 'uid': '...'}
    username=creator.username,
    community_name=community.name,
    post_title=post.title,
    post_id=post.uid,
    community_id=community.uid
)
```

### Example 3: Connection Request
```python
from notification.global_service import GlobalNotificationService

# In your CreateConnection mutation
service = GlobalNotificationService()
service.send(
    event_type="new_connection_request",
    recipients=[{'device_id': receiver_device_id, 'uid': receiver_uid}],
    username=sender.username,
    connection_id=connection.uid
)
```

## Available Event Types

See `notification/notification_templates.py` for all ~200 event types:
- `new_post_from_connection`
- `new_comment_on_post`
- `vibe_reaction_on_post`
- `new_story_from_connection`
- `new_connection_request`
- `connection_accepted`
- `new_community_post`
- `community_post_comment`
- `community_event_reminder`
- `new_message`
- `profile_viewed`
- And 190+ more...

## PostgreSQL Storage

All notifications are automatically stored in the `user_notification` table with:
- User UID
- Notification type
- Title & body
- Device ID
- Status (pending/sent/failed/read)
- Priority
- Click action
- Image URL
- Custom data
- Timestamps

## Adding New Notification Types

1. Add to `notification/notification_templates.py`:
```python
NotificationEventType.MY_NEW_EVENT = "my_new_event"

NOTIFICATION_TEMPLATES = {
    ...
    NotificationEventType.MY_NEW_EVENT: {
        "title": "{username} did something",
        "body": "{description}",
        "click_action": "/path/{item_id}",
        "priority": "normal",
    },
}
```

2. Use it:
```python
service.send(
    event_type="my_new_event",
    recipients=recipients,
    username="Alice",
    description="Something awesome",
    item_id="123"
)
```

## Benefits

✅ **One line to send** - No boilerplate code
✅ **Template-driven** - Consistent messages
✅ **PostgreSQL storage** - All notifications saved
✅ **Auto-retry** - Handles failures automatically
✅ **Type-safe** - Enum-based event types
✅ **Async ready** - Supports both sync and async
✅ **Easy to extend** - Just add template and use

## Migration from Old Services

**Before (Old Way):**
```python
from community.services.notification_service import NotificationService
import asyncio

notification_service = NotificationService()
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
try:
    loop.run_until_complete(notification_service.notifyCommunityPost(...))
finally:
    loop.close()
```

**After (New Way):**
```python
from notification.global_service import GlobalNotificationService

service = GlobalNotificationService()
service.send(
    event_type="new_community_post",
    recipients=members,
    username=creator.username,
    community_name=community.name,
    post_title=post.title,
    post_id=post.uid,
    community_id=community.uid
)
```

Much simpler!

## Next Steps

1. Run migrations:
   ```bash
   python manage.py makemigrations notification
   python manage.py migrate notification
   ```

2. Start using in your mutations

3. Add more templates as needed

