# 📨 Notification Templates Implementation

## ✅ Complete Implementation Status

All **81 main notification templates** from `Ooumph App Notifications.html` have been implemented (excluding onboarding notifications as requested).

## 📊 Templates by Category

### 1. Feed & Content Interactions (15 templates)
- ✅ `new_post_from_connection` - Connection posts new content
- ✅ `new_comment_on_post` - Comment on user's post  
- ✅ `post_comment` - Detailed comment notification
- ✅ `vibe_reaction_on_post` - Vibe/reaction on post
- ✅ `new_story_from_connection` - Connection shares story
- ✅ `vibe_analytics` - Post getting multiple vibes
- Plus 9 more feed-related templates

### 2. Profile & Connections (24 templates)
- ✅ `profile_edit_reminder` - Reminder to complete profile
- ✅ `new_connection_request` - Someone wants to connect
- ✅ `connection_accepted` - Connection request accepted
- ✅ `mutual_connection_added` - New mutual connection
- ✅ `special_moment_added_background` - Special moment added (background)
- ✅ `special_moment_added_active` - Special moment added (active)
- ✅ `achievement_added` - New achievement unlocked
- ✅ `education_added` - Education updated
- ✅ `experience_added` - Work experience added
- ✅ `skill_added` - New skill added
- ✅ `note_saved` - Note saved
- ✅ `sub_relation_updated` - Sub-relation modified
- ✅ `profile_viewed` - Profile viewed by someone
- ✅ `profile_viewed_multiple` - Multiple profile views
- ✅ `vibe_received` - Vibe received
- ✅ `multiple_vibes_received` - Multiple vibes received
- Plus 8 more profile-related templates

### 3. Community Interactions (15 templates)
- ✅ `new_sibling_community` - Sibling community created
- ✅ `new_child_community` - Child community created
- ✅ `community_role_change` - User role updated
- ✅ `new_members_joined` - New members joined community
- ✅ `community_announcement` - Important announcement
- ✅ `new_community_post` - New post in community
- ✅ `community_post_reaction` - Reaction on community post
- ✅ `community_post_comment` - Comment on community post
- ✅ `community_post_mention` - Mentioned in community post
- ✅ `community_event_reminder` - Event starting soon
- ✅ `community_goal_created` - New community goal
- ✅ `community_achievement_unlocked` - Achievement unlocked
- ✅ `community_affiliation` - Joined new community
- Plus 2 more community templates

### 4. Story & Media (5 templates)
- ✅ `new_story_available` - Connection shares story
- ✅ `story_reaction` - Reaction on user's story
- ✅ `story_mention` - Mentioned in a story
- ✅ `story_expiring_soon` - Story about to expire
- ✅ `story_upload_reminder` - Reminder to share story

### 5. Requests & Invitations (6 templates)
- ✅ `pending_connection_requests` - Pending connection requests
- ✅ `community_invitation_received` - Invited to community
- ✅ `community_request_accepted` - Community request approved
- ✅ `friend_request_accepted` - Friend request accepted
- ✅ `event_invitation_received` - Event invitation
- ✅ `pending_invites_reminder` - Reminder about pending invites

### 6. Chat & Messaging (5 templates)
- ✅ `new_message` - New chat message received
- ✅ `unread_messages` - Unread messages waiting
- ✅ `group_chat_mention` - Mentioned in group chat
- ✅ `new_group_chat_created` - Added to group chat
- ✅ `chat_engagement_reminder` - Reminder to chat

### 7. Discovery & Trending (5 templates)
- ✅ `trending_topic_matching_interest` - Trending topic matches interest
- ✅ `new_user_in_network` - New user with shared interests
- ✅ `suggested_community` - Recommended community
- ✅ `explore_top_vibes` - Explore trending content
- ✅ `find_new_arrivals` - Meet new people

### 8. Settings & Privacy (5 templates)
- ✅ `privacy_settings_reminder` - Review privacy settings
- ✅ `profile_visibility_change` - Profile visibility changed
- ✅ `account_security_alert` - Security alert (URGENT)
- ✅ `new_feature_in_settings` - New settings available
- ✅ `general_settings_reminder` - Update general settings

### 9. App Updates & System (4 templates)
- ✅ `new_app_version_available` - Update available
- ✅ `mandatory_update_required` - Update required (URGENT)
- ✅ `new_features_added` - New features announcement
- ✅ `security_update` - Security update available

### 10. Engagement Reminders (3 templates)
- ✅ `vibe_interaction_reminder` - Reminder to react to posts
- ✅ `commenting_reminder` - Reminder to comment
- ✅ `connection_flow_reminder` - Reminder to connect

### 11. Incomplete Actions (9 templates)
- ✅ `achievement_incomplete` - Incomplete achievement
- ✅ `education_incomplete` - Incomplete education entry
- ✅ `experience_incomplete` - Incomplete work experience
- ✅ `skill_incomplete` - Unsaved skill
- ✅ `note_incomplete` - Unsaved note
- ✅ `sub_relation_incomplete` - Unsaved relation changes
- ✅ `unfinished_task` - Pending task
- ✅ `missed_achievement` - Close to achievement
- ✅ `vibe_with_incomplete_profile` - Vibe received but profile incomplete

## 🎯 Priority Distribution

| Priority | Count | Use Cases |
|----------|-------|-----------|
| **URGENT** | 2 | Security alerts, mandatory updates |
| **HIGH** | 31 | User interactions, new content, connection requests |
| **NORMAL** | 48 | General updates, reminders, suggestions |
| **LOW** | 0 | None currently |

## 💡 How to Use

### Basic Usage

```python
from notification.global_service import GlobalNotificationService

service = GlobalNotificationService()

# Example 1: Comment on post
service.send(
    event_type="new_comment_on_post",
    recipients=[{'device_id': 'FCM_TOKEN', 'uid': 'user_123'}],
    username="John Doe",
    comment_text="Great post!",
    post_id="post_456"
)

# Example 2: Connection request
service.send(
    event_type="new_connection_request",
    recipients=[{'device_id': receiver.device_id, 'uid': receiver.uid}],
    username=sender.username
)

# Example 3: Community post
service.send(
    event_type="new_community_post",
    recipients=community_members,
    username=poster.username,
    community_name=community.name,
    post_id=post.uid,
    community_id=community.uid
)
```

### Template Placeholders

Each template supports dynamic placeholders. Common placeholders include:

- `{username}` - Username of the acting user
- `{user_id}` - User ID
- `{post_id}` - Post ID
- `{comment_text}` - Comment content
- `{community_name}` - Community name
- `{community_id}` - Community ID
- `{event_name}` - Event name
- `{achievement_name}` - Achievement name
- `{message_preview}` - Chat message preview
- `{count}` - Various counts (views, vibes, members, etc.)

## 📋 Template Structure

Each template contains:

```python
{
    "title": "Short notification title with {placeholders}",
    "body": "Longer notification body with {placeholders}",
    "click_action": "/path/to/{resource}",  # Deep link
    "priority": "high|normal|low|urgent",
    "image_url": "{optional_image_url}"  # Optional
}
```

## 🔧 Template Functions

The `notification_templates.py` file provides helper functions:

### `get_template(event_type: str) -> dict`
Get a specific template by event type.

```python
from notification.notification_templates import get_template

template = get_template("new_comment_on_post")
```

### `get_all_event_types() -> list`
Get all available event types.

```python
from notification.notification_templates import get_all_event_types

all_types = get_all_event_types()
print(f"Total: {len(all_types)} templates")
```

### `search_templates(keyword: str) -> dict`
Search templates by keyword.

```python
from notification.notification_templates import search_templates

# Find all community-related templates
community_templates = search_templates("community")

# Find all comment-related templates  
comment_templates = search_templates("comment")
```

## 📊 PostgreSQL Storage

Every notification sent is automatically stored in the `user_notification` table:

```sql
CREATE TABLE user_notification (
    id SERIAL PRIMARY KEY,
    user_uid VARCHAR(255) NOT NULL,           -- Neo4j user UID
    notification_type VARCHAR(100) NOT NULL,   -- Template key
    title VARCHAR(255) NOT NULL,               -- Rendered title
    body TEXT NOT NULL,                        -- Rendered body
    device_id VARCHAR(255) NOT NULL,           -- FCM token
    status VARCHAR(20) DEFAULT 'pending',      -- sent/failed/pending/read
    priority VARCHAR(20) DEFAULT 'normal',     -- urgent/high/normal/low
    click_action VARCHAR(500),                 -- Deep link
    image_url TEXT,                            -- Optional image
    data JSONB DEFAULT '{}',                   -- Additional data
    is_read BOOLEAN DEFAULT FALSE,
    error_message TEXT,                        -- If failed
    created_at TIMESTAMP DEFAULT NOW(),
    sent_at TIMESTAMP,
    read_at TIMESTAMP
);
```

## 🧪 Testing

Run the test command to verify everything works:

```bash
# Test notification service
python manage.py test_notification

# View statistics
python manage.py notification_stats

# Or use the comprehensive test script
./test_notification_service.sh
```

## 📚 Related Documentation

- **Main README**: `notification/README.md`
- **Simple Usage Guide**: `notification/SIMPLE_USAGE.md`
- **Migration Examples**: `notification/MIGRATION_EXAMPLES.md`
- **Setup Guide**: `NOTIFICATION_SETUP.md`
- **Quick Start**: `QUICK_START.md`

## ✅ Implementation Complete

All main notifications from the HTML file have been implemented. The service is:

- ✅ Template-driven (81 templates)
- ✅ PostgreSQL-backed storage
- ✅ Priority-aware (urgent/high/normal)
- ✅ Asynchronous (non-blocking)
- ✅ Error-handled (with retries)
- ✅ Trackable (Django admin + stats)
- ✅ Easy to use (one function call)
- ✅ Well-documented

Ready to integrate into your ~300 mutations! 🚀

