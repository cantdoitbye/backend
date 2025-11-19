# Notification Integration - Complete Guide Summary

## 📋 What You Have

I've analyzed your Ooumph_App_Notifications.html file and created complete documentation for integrating notifications into all your mutations. Here's what I've provided:

### 📄 Documents Created

1. **NOTIFICATION_INTEGRATION_GUIDE.md** (41KB)
   - Complete integration guide with code for ALL mutations
   - Organized by feature section (Onboarding, Feed, Community, etc.)
   - Ready-to-copy code snippets
   - Placement instructions for each notification
   - 80+ notification implementations

2. **NOTIFICATION_QUICK_REFERENCE.md** (14KB)
   - Quick lookup table for all notifications
   - Maps HTML notifications to implementation details
   - Shows event types, file locations, and priorities
   - Code templates for common patterns
   - Django Admin usage instructions

3. **NOTIFICATION_EXAMPLES.md** (29KB)
   - Complete, working examples for common mutations
   - Shows full context of where to add notification code
   - Covers: Posts, Comments, Connections, Communities, Messages, Stories, Profile
   - Best practices and patterns to follow
   - Testing instructions

---

## 🎯 Your Notification System

Based on the project knowledge search, you already have:

✅ **Global Notification Service** (`notification/global_service.py`)
- Template-driven notification system
- PostgreSQL storage for all notifications
- Automatic retry handling
- Async/sync support

✅ **Notification Templates** (`notification/notification_templates.py`)
- 200+ pre-defined notification templates
- Supports all notifications from your HTML file

✅ **Django Models** (`notification/models.py`)
- UserNotification - stores individual notifications
- NotificationLog - tracks batch sends
- NotificationPreference - user preferences

✅ **Microservice Integration**
- Sends notifications to external notification service
- URL configured in settings: `NOTIFICATION_SERVICE_URL`
- Handles device tokens and FCM push notifications

---

## 🚀 How to Use This Guide

### Step 1: Understand the Pattern

Every notification follows this simple pattern:

```python
from notification.global_service import GlobalNotificationService

# After successful operation in your mutation
try:
    if recipient.device_id and recipient.uid != sender.uid:
        service = GlobalNotificationService()
        service.send(
            event_type="notification_event_type",
            recipients=[{
                'device_id': recipient.device_id,
                'uid': recipient.uid
            }],
            username=sender.username,
            # ... other template variables
        )
except Exception as e:
    logger.error(f"Notification error: {e}")
```

### Step 2: Find Your Mutation

Use **NOTIFICATION_QUICK_REFERENCE.md** to quickly find:
- Which mutation needs which notification
- What event type to use
- Where the file is located

Example:
```
| Post Comment | CreateComment | new_comment_on_post | post/graphql/mutations.py | 3.1 |
```

### Step 3: Copy the Code

Open **NOTIFICATION_INTEGRATION_GUIDE.md** and go to the section number (e.g., 3.1). Copy the notification code block and paste it into your mutation.

### Step 4: See Complete Examples

If you need more context, check **NOTIFICATION_EXAMPLES.md** for complete, working mutation examples showing where exactly to place the notification code.

---

## 📊 Notification Breakdown

From your HTML file, here are the notifications categorized:

### App Closed Notifications (Push)
1. **Onboarding** (4 notifications)
   - Welcome, Login, Password Reset, Signup

2. **Areas of Interest** (1 notification)
   - Interest selection reminder

3. **Feed & Content** (4 notifications)
   - New post, Comment, Vibe reaction, Story

4. **Profile & Connections** (13 notifications)
   - Connection requests, Profile updates, Achievements, Skills, etc.

5. **Community** (13 notifications)
   - New communities, Posts, Comments, Events, Goals, etc.

6. **Stories** (4 notifications)
   - New story, Reactions, Mentions, Expiring

7. **Notifications & Requests** (4 notifications)
   - Pending requests, Invites, Acceptances

8. **Chat & Messaging** (4 notifications)
   - New messages, Unread, Group mentions

9. **Search & Discovery** (3 notifications)
   - Trending topics, New users, Suggestions

10. **Menu & Privacy** (4 notifications)
    - Privacy reminders, Security alerts

### App Open Notifications (In-App)
Same categories as above but delivered through app UI

### Incomplete Process Notifications
18 different incomplete process reminders

### Version Updates
4 version-related notifications

**Total: ~80 unique notification types**

---

## 🔑 Key Implementation Details

### Your Existing Service Pattern

From your project, the old pattern was:
```python
from post.services.notification_service import NotificationService
import asyncio

notification_service = NotificationService()
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
try:
    loop.run_until_complete(notification_service.notifyNewComment(...))
finally:
    loop.close()
```

### New Pattern (What You Should Use)
```python
from notification.global_service import GlobalNotificationService

service = GlobalNotificationService()
service.send(
    event_type="new_comment_on_post",
    recipients=recipients,
    username=username,
    comment_text=text
)
```

**Much simpler!** The service handles async internally.

---

## 🎨 Available Event Types

All event types are pre-defined in `notification/notification_templates.py`. Here are some key ones:

### Posts & Comments
- `new_post_from_connection`
- `new_comment_on_post`
- `vibe_reaction_on_post`

### Connections
- `new_connection_request`
- `connection_accepted`
- `mutual_connection_added`

### Community
- `new_community_post`
- `community_post_comment`
- `new_sibling_community`
- `new_child_community`
- `community_role_changed`
- `community_announcement`

### Messages
- `new_message`
- `unread_messages`
- `group_chat_mention`
- `new_group_chat_created`

### Stories
- `new_story_from_connection`
- `story_reaction`
- `story_mention`
- `story_expiring_soon`

### Profile
- `profile_viewed`
- `vibe_sent_to_profile`
- `achievement_added`
- `education_added`
- `experience_added`
- `skill_added`

And many more...

---

## 💡 Best Practices

### 1. Always Check Device ID
```python
if user.device_id:
    # Send notification
```

### 2. Don't Notify Self
```python
if recipient.uid != sender.uid:
    # Send notification
```

### 3. Batch Multiple Recipients
```python
# Good: One call
recipients = [...]
service.send(event_type="...", recipients=recipients, ...)

# Bad: Multiple calls
for r in recipients:
    service.send(...)  # Don't do this
```

### 4. Handle Errors Gracefully
```python
try:
    # Send notification
except Exception as e:
    logger.error(f"Notification error: {e}")
    # Don't fail the mutation
```

### 5. Import Once
```python
# At top of file
from notification.global_service import GlobalNotificationService

# Not inside each mutation
```

---

## 🧪 Testing

### Test Individual Notification
```python
from notification.global_service import GlobalNotificationService

service = GlobalNotificationService()
service.send(
    event_type="new_comment_on_post",
    recipients=[{
        'device_id': 'your_test_device_id',
        'uid': 'test_user_uid'
    }],
    username="Test User",
    comment_text="Test comment",
    post_id="test_123"
)
```

### Check Django Admin
1. Go to `/admin/notification/usernotification/`
2. See all sent notifications
3. Check status, timestamps, data
4. View error messages if any failed

### View Stats
```bash
python manage.py notification_stats
```

---

## 📍 Where to Start

### High Priority Mutations (Implement First)

1. **CreateComment** (`post/graphql/mutations.py`)
   - Event: `new_comment_on_post`
   - See: Guide Section 3.1, Examples Section

2. **SendMessage** (`msg/graphql/mutations.py`)
   - Event: `new_message`
   - See: Guide Section 8.1, Examples Section

3. **SendConnectionRequest** (`connection/graphql/mutations.py`)
   - Event: `new_connection_request`
   - See: Guide Section 4.1, Examples Section

4. **AcceptConnectionRequest** (`connection/graphql/mutations.py`)
   - Event: `connection_accepted`
   - See: Guide Section 4.2, Examples Section

5. **CreatePost** (`post/graphql/mutations.py`)
   - Event: `new_post_from_connection`
   - See: Guide Section 3.1, Examples Section

6. **CreateCommunityPost** (`community/graphql/mutations.py`)
   - Event: `new_community_post`
   - See: Guide Section 5.6, Examples Section

7. **CreateLike** (`post/graphql/mutations.py`)
   - Event: `vibe_reaction_on_post`
   - See: Guide Section 3.2, Examples Section

8. **CreateStory** (`story/graphql/mutations.py`)
   - Event: `new_story_from_connection`
   - See: Guide Section 6.1, Examples Section

---

## 📂 File Structure

Your notification system files:
```
notification/
├── global_service.py           # Main service
├── notification_templates.py   # All 200+ templates
├── models.py                   # PostgreSQL models
├── admin.py                    # Django admin
├── migrations/                 # Database migrations
├── management/
│   └── commands/
│       ├── test_notification.py
│       └── notification_stats.py
└── README.md                   # Full documentation
```

---

## 🔧 Implementation Checklist

- [ ] Read NOTIFICATION_QUICK_REFERENCE.md
- [ ] Review NOTIFICATION_EXAMPLES.md for pattern understanding
- [ ] Start with CreateComment mutation (most common)
- [ ] Add notification code using NOTIFICATION_INTEGRATION_GUIDE.md
- [ ] Test in Django shell
- [ ] Check Django Admin for notification record
- [ ] Verify device receives push notification
- [ ] Move to next high-priority mutation
- [ ] Implement batch notifications for communities
- [ ] Add scheduled task notifications (incomplete processes)
- [ ] Add error handling and logging
- [ ] Monitor notification success rates

---

## 🐛 Troubleshooting

### Notification Not Sent?
1. Check if user has device_id: `user.device_id`
2. Check Django Admin for notification record
3. Check notification status (sent/failed/pending)
4. Check error message in notification record
5. Verify `NOTIFICATION_SERVICE_URL` in settings
6. Check microservice logs

### Wrong Message?
1. Verify event_type is correct
2. Check template variables match template
3. Review `notification/notification_templates.py`

### Duplicate Notifications?
1. Don't call service.send() in a loop
2. Batch recipients into single call
3. Check for duplicate mutation execution

---

## 📚 Additional Resources

### In Your Project
- `notification/README.md` - Complete documentation
- `notification/SIMPLE_USAGE.md` - Basic usage guide
- `notification/MIGRATION_EXAMPLES.md` - Migration from old services
- `notification/FINAL_SUMMARY.md` - Setup summary

### Django Admin
- User Notifications: `/admin/notification/usernotification/`
- Notification Logs: `/admin/notification/notificationlog/`
- User Preferences: `/admin/notification/notificationpreference/`

### Management Commands
```bash
python manage.py test_notification
python manage.py notification_stats
```

---

## 🎯 Next Steps

1. **Review the Documents**
   - Start with NOTIFICATION_QUICK_REFERENCE.md
   - Then NOTIFICATION_EXAMPLES.md
   - Use NOTIFICATION_INTEGRATION_GUIDE.md as reference

2. **Implement High-Priority Notifications**
   - CreateComment
   - SendMessage
   - Connection requests
   - Post creation

3. **Test Each Implementation**
   - Use Django shell
   - Check Admin panel
   - Verify push notifications

4. **Gradually Add More**
   - Follow priority list
   - Test after each addition
   - Monitor error rates

5. **Add Scheduled Tasks**
   - Incomplete process reminders
   - Version updates
   - Analytics-based notifications

---

## ✨ Summary

You now have:
- ✅ Complete code for 80+ notifications
- ✅ Event types mapped to mutations
- ✅ Working examples with full context
- ✅ Quick reference for fast lookup
- ✅ Best practices and patterns
- ✅ Testing and troubleshooting guides

Everything you need to integrate notifications into your mutations!

Just:
1. Find your mutation in the quick reference
2. Copy the code from the integration guide
3. Paste into your mutation file
4. Test and verify

It's that simple! 🚀

---

## 📞 Support

If you encounter issues:
1. Check NOTIFICATION_INTEGRATION_GUIDE.md for your specific case
2. Review NOTIFICATION_EXAMPLES.md for complete working examples
3. Check Django Admin for notification records
4. Review error messages in logs
5. Verify microservice is running and accessible

All notification templates are pre-configured and ready to use. Just add the code!
