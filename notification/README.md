# 📨 Notification Service - Clean Structure

## What's Here (Clean & Simple!)

```
notification/
├── __init__.py                          # Package init
├── apps.py                              # Django app config
├── models.py                            # PostgreSQL models
├── admin.py                             # Django admin
├── global_service.py                    # ⭐ MAIN SERVICE (USE THIS!)
├── notification_templates.py            # All notification templates
├── tests.py                             # Unit tests
├── migrations/
│   └── 0001_initial.py                 # Database migration
├── management/commands/
│   ├── test_notification.py            # Test command
│   └── notification_stats.py           # Stats command
├── SIMPLE_USAGE.md                      # Quick start guide
├── MIGRATION_EXAMPLES.md                # Migration examples
└── FINAL_SUMMARY.md                     # Complete overview
```

## Core Files (Only What You Need!)

### 1. `global_service.py` ⭐
**The main service - this is what you import and use!**

```python
from notification.global_service import GlobalNotificationService

service = GlobalNotificationService()
service.send(
    event_type="new_comment_on_post",
    recipients=[{'device_id': '...', 'uid': '...'}],
    username="John",
    comment_text="Nice!",
    post_id="123"
)
```

### 2. `notification_templates.py`
**All notification templates (70+ ready)**

Defines:
- `NotificationEventType` enum with all event types
- `NOTIFICATION_TEMPLATES` dict with title, body, click_action, priority
- Helper functions to format notifications

### 3. `models.py`
**PostgreSQL models**

- `UserNotification` - Stores every notification sent
- `NotificationLog` - Batch logs
- `NotificationPreference` - User settings

### 4. `admin.py`
**Django admin interface**

View and manage notifications at `/admin/notification/`

## Quick Test

### Step 1: Run Migrations
```bash
python manage.py makemigrations notification
python manage.py migrate notification
```

### Step 2: Test Notification
```bash
python manage.py test_notification
```

This will:
- ✅ Send a test "new_comment_on_post" notification
- ✅ Store it in PostgreSQL
- ✅ Show you the complete details
- ✅ Verify it worked

### Step 3: View Stats
```bash
python manage.py notification_stats
```

Shows:
- Total notifications
- Count by status
- Count by type
- Recent notifications
- Batch logs

## How to Use in Your Code

### Simple Example
```python
from notification.global_service import GlobalNotificationService

# In your mutation/view
service = GlobalNotificationService()
service.send(
    event_type="new_comment_on_post",
    recipients=[{'device_id': device_id, 'uid': uid}],
    username="Alice",
    comment_text="Great post!",
    post_id="post_123"
)
```

### Community Example
```python
from notification.global_service import GlobalNotificationService

# Get members
members = [
    {'device_id': m.device_id, 'uid': m.uid}
    for m in community.members
    if m.device_id
]

# Send notification
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

## Available Event Types (70+)

See `notification_templates.py` for complete list:

**Post & Feed:**
- `new_post_from_connection`
- `new_comment_on_post`
- `vibe_reaction_on_post`

**Story:**
- `new_story_from_connection`
- `story_reaction`

**Connection:**
- `new_connection_request`
- `connection_accepted`

**Community:**
- `new_community_post`
- `community_post_comment`
- `community_event_reminder`

**Chat:**
- `new_message`
- `group_chat_mention`

**...and 60+ more!**

## Database Schema

### `user_notification` table
```
user_uid              - User UID from Neo4j
notification_type     - Type (e.g., "new_comment_on_post")
title                 - Notification title
body                  - Notification body
device_id             - FCM device token
status                - pending/sent/failed/read
priority              - normal/high/urgent/low
click_action          - Deep link URL
image_url             - Image URL (optional)
data                  - Additional JSON data
is_read               - Boolean
created_at, sent_at, read_at - Timestamps
error_message         - Error details if failed
```

## That's It!

Simple, clean structure. No extra complexity. Just what you need! 🚀

---

**Next:** Run migrations and test with `python manage.py test_notification`

