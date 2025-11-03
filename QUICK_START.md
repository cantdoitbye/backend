# 🚀 Notification Service - Quick Start

## ⚡ 30-Second Setup

```bash
# 1. Run migrations
python manage.py makemigrations notification
python manage.py migrate notification

# 2. Test it
python manage.py test_notification

# 3. Use it!
```

## 💡 One-Line Usage

```python
from notification.global_service import GlobalNotificationService

GlobalNotificationService().send(
    event_type="new_comment_on_post",
    recipients=[{'device_id': 'FCM_TOKEN', 'uid': 'user_123'}],
    username="John Doe",
    comment_text="Great post!",
    post_id="post_123"
)
```

## 📋 Common Event Types

| Event | Required Fields |
|-------|----------------|
| `new_comment_on_post` | username, comment_text, post_id |
| `new_connection_request` | username, connection_id |
| `vibe_reaction_on_post` | username, vibe_type, post_id |
| `new_story_from_connection` | username, story_id |
| `new_community_post` | username, community_name, post_title, post_id, community_id |
| `new_message` | sender_name, message_preview, chat_id |
| `profile_viewed` | username, profile_id |
| `achievement_added` | achievement_name, achievement_icon |

**See 70+ more in `notification/notification_templates.py`**

## 📊 What Happens

1. ✅ Notification sent via FCM
2. ✅ Stored in PostgreSQL (`user_notification` table)
3. ✅ Visible in Django admin
4. ✅ Trackable via `notification_stats` command

## 🔧 Quick Commands

```bash
# Test notification
python manage.py test_notification

# View stats
python manage.py notification_stats

# Or use automated test
./test_notification_service.sh
```

## 📖 More Help

- **Full Setup**: `NOTIFICATION_SETUP.md`
- **Examples**: `notification/SIMPLE_USAGE.md`
- **Migration Guide**: `notification/MIGRATION_EXAMPLES.md`

## ✨ That's It!

You're ready to send ~300 notifications! 🎉


