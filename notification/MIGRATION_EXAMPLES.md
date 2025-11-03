# Migration Examples - Old Service → New Global Service

This guide shows how to replace existing notification services with the new global service.

## Example 1: Post Comment Notification

### Old Way (community/services/notification_service.py pattern)
```python
from post.services.notification_service import NotificationService
import asyncio

# In your CreateComment mutation
notification_service = NotificationService()

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
try:
    loop.run_until_complete(
        notification_service.notifyNewComment(
            commenter_name=commenter.username,
            post_creator_device_id=post_creator.device_id,
            post_id=post.uid,
            comment_id=comment.uid,
            comment_content=comment.text
        )
    )
finally:
    loop.close()
```

### New Way (Global Service)
```python
from notification.global_service import GlobalNotificationService

# In your CreateComment mutation
service = GlobalNotificationService()
service.send(
    event_type="new_comment_on_post",
    recipients=[{
        'device_id': post_creator.device_id,
        'uid': post_creator.uid
    }],
    username=commenter.username,
    comment_text=comment.text[:100],
    post_id=post.uid
)
```

---

## Example 2: Community Post Notification

### Old Way
```python
from community.services.notification_service import NotificationService
import asyncio

# Get all members to notify
members_to_notify = []
for member in community.members:
    if member.device_id:
        members_to_notify.append({
            'device_id': member.device_id
        })

# Send notifications
notification_service = NotificationService()
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
try:
    loop.run_until_complete(
        notification_service.notifyCommunityPost(
            creator_name=creator.username,
            members=members_to_notify,
            community_name=community.name,
            post_title=post.title,
            post_id=post.uid,
            community_id=community.uid
        )
    )
finally:
    loop.close()
```

### New Way
```python
from notification.global_service import GlobalNotificationService

# Get all members to notify (now including uid)
members_to_notify = []
for member in community.members:
    if member.device_id:
        members_to_notify.append({
            'device_id': member.device_id,
            'uid': member.uid  # Don't forget uid for storage!
        })

# Send notifications (one line!)
service = GlobalNotificationService()
service.send(
    event_type="new_community_post",
    recipients=members_to_notify,
    username=creator.username,
    community_name=community.name,
    post_title=post.title[:50],
    post_id=post.uid,
    community_id=community.uid
)
```

---

## Example 3: Connection Request Notification

### Old Way
```python
from connection.services.notification_service import NotificationService
import asyncio

notification_service = NotificationService()

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
try:
    loop.run_until_complete(
        notification_service.notifyConnectionRequest(
            sender_name=sender.username,
            receiver_device_id=receiver.device_id,
            connection_id=connection.uid
        )
    )
finally:
    loop.close()
```

### New Way
```python
from notification.global_service import GlobalNotificationService

service = GlobalNotificationService()
service.send(
    event_type="new_connection_request",
    recipients=[{
        'device_id': receiver.device_id,
        'uid': receiver.uid
    }],
    username=sender.username,
    connection_id=connection.uid
)
```

---

## Example 4: Story Notification

### Old Way
```python
from story.services.notification_service import NotificationService
import asyncio

# Get all connections
connections_to_notify = []
for connection in user.connections:
    if connection.device_id:
        connections_to_notify.append({
            'device_id': connection.device_id
        })

notification_service = NotificationService()
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
try:
    loop.run_until_complete(
        notification_service.notifyNewStory(
            creator_name=user.username,
            connections=connections_to_notify,
            story_id=story.uid
        )
    )
finally:
    loop.close()
```

### New Way
```python
from notification.global_service import GlobalNotificationService

# Get all connections (with uid)
connections_to_notify = []
for connection in user.connections:
    if connection.device_id:
        connections_to_notify.append({
            'device_id': connection.device_id,
            'uid': connection.uid
        })

service = GlobalNotificationService()
service.send(
    event_type="new_story_from_connection",
    recipients=connections_to_notify,
    username=user.username,
    story_id=story.uid
)
```

---

## Example 5: Chat Message Notification

### Old Way
```python
from msg.services.notification_service import NotificationService
import asyncio

notification_service = NotificationService()

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
try:
    loop.run_until_complete(
        notification_service.notifyNewChatMessage(
            sender_name=sender.username,
            receiver_device_id=receiver.device_id,
            message_preview=message.text[:50],
            chat_id=chat.uid
        )
    )
finally:
    loop.close()
```

### New Way
```python
from notification.global_service import GlobalNotificationService

service = GlobalNotificationService()
service.send(
    event_type="new_message",
    recipients=[{
        'device_id': receiver.device_id,
        'uid': receiver.uid
    }],
    username=sender.username,
    message_preview=message.text[:100],
    chat_id=chat.uid
)
```

---

## Example 6: Community Event Reminder

### Old Way
```python
from community.services.notification_service import NotificationService
import asyncio

# Get event participants
participants = []
for participant in event.participants:
    if participant.device_id:
        participants.append({
            'device_id': participant.device_id
        })

notification_service = NotificationService()
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
try:
    loop.run_until_complete(
        notification_service.notifyCommunityEvent(
            event_name=event.name,
            community_name=community.name,
            members=participants,
            minutes_until_start=15,
            community_id=community.uid,
            event_id=event.uid
        )
    )
finally:
    loop.close()
```

### New Way
```python
from notification.global_service import GlobalNotificationService

# Get event participants
participants = []
for participant in event.participants:
    if participant.device_id:
        participants.append({
            'device_id': participant.device_id,
            'uid': participant.uid
        })

service = GlobalNotificationService()
service.send(
    event_type="community_event_reminder",
    recipients=participants,
    event_name=event.name,
    community_name=community.name,
    minutes=15,
    community_id=community.uid,
    event_id=event.uid
)
```

---

## Key Differences

| Aspect | Old Way | New Way |
|--------|---------|---------|
| **Imports** | Module-specific service + asyncio | One global service |
| **Setup** | Create loop, set event loop | None needed |
| **Async** | Manual loop.run_until_complete | Handled internally |
| **Cleanup** | Manual loop.close() | None needed |
| **Storage** | None | Automatic PostgreSQL |
| **Retries** | Manual | Automatic (3 retries) |
| **Logging** | Manual print statements | Automatic logging |
| **Templates** | Hardcoded in each function | Centralized templates |
| **Lines of Code** | ~15-20 lines | 3-5 lines |

---

## Important: Don't Forget UIDs!

The new service stores notifications in PostgreSQL, so you must include **both `device_id` and `uid`** in recipients:

```python
# ❌ OLD (missing uid)
recipients = [{'device_id': user.device_id}]

# ✅ NEW (includes uid)
recipients = [{'device_id': user.device_id, 'uid': user.uid}]
```

---

## Benefits Summary

1. **Less Code**: 3-5 lines vs 15-20 lines
2. **Simpler**: No asyncio management
3. **Storage**: All notifications saved in PostgreSQL
4. **Tracking**: Full audit trail
5. **Retries**: Automatic retry on failure
6. **Logging**: Built-in structured logging
7. **Templates**: Consistent messages
8. **Admin**: View all notifications in Django admin

---

## Gradual Migration

You can migrate gradually:
1. Start with new mutations
2. Replace old services one by one
3. Keep old services during transition
4. Eventually deprecate old services

The new service is **100% compatible** with existing notification infrastructure - it just makes it easier!

