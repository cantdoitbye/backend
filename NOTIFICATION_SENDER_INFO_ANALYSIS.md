# Notification Sender Information - Complete Analysis

## Executive Summary

**Current Problem:** Notifications don't include information about WHO triggered them (sender details).

**Impact:** Frontend cannot display sender's profile picture, name, or link to their profile when showing notifications.

---

## Current vs Required Structure

### Current Notification Response (myNotifications query)

```json
{
  "data": {
    "myNotifications": {
      "notifications": [
        {
          "id": 123,
          "user_uid": "recipient_uid_abc123",  // ← This is the RECIPIENT (you)
          "notification_type": "new_post_from_connection",
          "title": "John just posted something new!",
          "body": "Check it out.",
          "data": {
            "post_id": "post_xyz789",
            "type": "new_post_from_connection"
            // ❌ NO SENDER INFO HERE!
          },
          "is_read": false,
          "created_at": "2024-12-08T10:30:00Z"
        }
      ]
    }
  }
}
```

### Required Notification Response (with sender info)

```json
{
  "data": {
    "myNotifications": {
      "notifications": [
        {
          "id": 123,
          "user_uid": "recipient_uid_abc123",  // Recipient (you)
          "notification_type": "new_post_from_connection",
          "title": "John just posted something new!",
          "body": "Check it out.",
          "data": {
            "post_id": "post_xyz789",
            "type": "new_post_from_connection",
            
            // ✅ NEW SENDER INFO
            "sender_uid": "john_uid_def456",        // Neo4j UID
            "sender_user_id": "john_user_id_123",   // External user_id
            "sender_username": "john_doe",          // Display name
            "sender_profile_pic_id": "img_789"      // Profile picture
          },
          "is_read": false,
          "created_at": "2024-12-08T10:30:00Z"
        }
      ]
    }
  }
}
```

---

## Understanding User Identifiers

### In Neo4j Users Model:

```python
class Users(DjangoNode, StructuredNode):
    uid = UniqueIdProperty()           # ← Auto-generated: "a1b2c3d4e5f6..."
    user_id = StringProperty()         # ← Manual/External: "user_12345"
    username = StringProperty()        # ← Display: "john_doe"
```

### Example User:

| Field | Value | Purpose |
|-------|-------|---------|
| `uid` | `a1b2c3d4e5f6...` | Neo4j internal unique ID (auto-generated) |
| `user_id` | `user_12345` | External reference ID (set manually) |
| `username` | `john_doe` | Display name |
| `id` | `12345` | Neo4j node ID (internal, not used) |

### Which One to Use?

**Recommendation: Include BOTH `uid` and `user_id`**

- **`uid`**: For Neo4j queries and internal operations
- **`user_id`**: For external references and API consistency
- **`username`**: For display purposes
- **`profile_pic_id`**: For showing sender's avatar

---

## Current Notification Flow

### 1. Community Notification Example

```python
# In community/graphql/mutations.py
members_to_notify = []
for member in member_uid:
    user_node = Users.nodes.get(uid=member)
    profile = user_node.profile.single()
    if profile and profile.device_id:
        members_to_notify.append({
            'device_id': profile.device_id,
            'uid': user_node.uid  # ← Only recipient's uid
        })

# Send notification
notification_service.notifyCommunityCreated(
    creator_name=created_by.username,  # ← Only name, not IDs!
    members=members_to_notify,
    community_id=community.uid,
    community_name=community.name
)
```

### 2. Notification Service

```python
# In community/services/notification_service.py
async def notifyCommunityCreated(self, creator_name: str, members: List[dict], ...):
    notification_data = {
        "title": f"You've been added to {community_name}",
        "body": f"{creator_name} created a new community...",
        "data": {
            "community_id": community_id,
            "type": "community_created"
            # ❌ No creator_uid or creator_user_id!
        }
    }
```

---

## What Needs to Change

### Change 1: Update Notification Service Signatures

**Before:**
```python
async def notifyCommunityCreated(
    self, 
    creator_name: str,  # ← Only name
    members: List[dict], 
    community_id: str, 
    community_name: str
):
```

**After:**
```python
async def notifyCommunityCreated(
    self, 
    creator_uid: str,        # ← Add UID
    creator_user_id: str,    # ← Add user_id
    creator_name: str,       # ← Keep name
    creator_profile_pic: str,# ← Add profile pic
    members: List[dict], 
    community_id: str, 
    community_name: str
):
```

### Change 2: Update Notification Data Payload

**Before:**
```python
notification_data = {
    "data": {
        "community_id": community_id,
        "type": "community_created"
    }
}
```

**After:**
```python
notification_data = {
    "data": {
        "community_id": community_id,
        "type": "community_created",
        
        # Add sender info
        "sender_uid": creator_uid,
        "sender_user_id": creator_user_id,
        "sender_username": creator_name,
        "sender_profile_pic_id": creator_profile_pic
    }
}
```

### Change 3: Update All Notification Calls

**Before:**
```python
notification_service.notifyCommunityCreated(
    creator_name=created_by.username,
    members=members_to_notify,
    community_id=community.uid,
    community_name=community.name
)
```

**After:**
```python
# Get creator profile for profile pic
creator_profile = created_by.profile.single()

notification_service.notifyCommunityCreated(
    creator_uid=created_by.uid,
    creator_user_id=created_by.user_id,
    creator_name=created_by.username,
    creator_profile_pic=creator_profile.profile_pic_id if creator_profile else None,
    members=members_to_notify,
    community_id=community.uid,
    community_name=community.name
)
```

---

## Notifications That Need Sender Info

### High Priority (User-triggered actions):

1. ✅ `new_post_from_connection` - Who posted
2. ✅ `new_comment_on_post` - Who commented
3. ✅ `post_comment` - Who commented
4. ✅ `comment_vibe_reaction` - Who reacted
5. ✅ `vibe_reaction_on_post` - Who reacted
6. ✅ `new_story_from_connection` - Who posted story
7. ✅ `new_connection_request` - Who sent request
8. ✅ `connection_accepted` - Who accepted
9. ✅ `new_members_joined` - Who joined
10. ✅ `new_community_post` - Who posted
11. ✅ `community_post_reaction` - Who reacted
12. ✅ `community_post_comment` - Who commented
13. ✅ `new_message` - Who sent message
14. ✅ `opportunity_comment` - Who commented
15. ✅ `opportunity_like` - Who liked
16. ✅ `opportunity_share` - Who shared
17. ✅ `opportunity_application` - Who applied

### Low Priority (System notifications):

- `profile_edit_reminder` - No sender (system)
- `pending_connection_requests` - No sender (system)
- `achievement_added` - No sender (system)
- `education_added` - No sender (system)

---

## Implementation Options

### Option A: Model-Level Changes (Requires Migration)

**Pros:**
- Queryable fields
- Type-safe
- Better for analytics

**Cons:**
- Requires database migration
- More rigid structure

```python
class UserNotification(models.Model):
    # Recipient info
    user_uid = models.CharField(max_length=255)
    
    # NEW: Sender info
    sender_uid = models.CharField(max_length=255, null=True, blank=True)
    sender_user_id = models.CharField(max_length=255, null=True, blank=True)
    sender_username = models.CharField(max_length=255, null=True, blank=True)
    sender_profile_pic_id = models.CharField(max_length=255, null=True, blank=True)
    
    # Existing fields
    notification_type = models.CharField(max_length=100)
    data = models.JSONField(default=dict)
    # ...
```

### Option B: JSON Data Field Only (No Migration)

**Pros:**
- No migration needed
- Flexible structure
- Quick to implement

**Cons:**
- Not queryable
- Less type-safe

```python
# Just add to data field
notification_data = {
    "data": {
        "sender_uid": "...",
        "sender_user_id": "...",
        "sender_username": "...",
        "sender_profile_pic_id": "..."
    }
}
```

### Option C: Hybrid (Recommended)

**Pros:**
- Best of both worlds
- Queryable IDs
- Flexible additional data

**Cons:**
- Slight redundancy

```python
class UserNotification(models.Model):
    # Recipient
    user_uid = models.CharField(max_length=255)
    
    # Sender (queryable)
    sender_uid = models.CharField(max_length=255, null=True, blank=True)
    sender_user_id = models.CharField(max_length=255, null=True, blank=True)
    
    # Additional data (flexible)
    data = models.JSONField(default=dict)  # Contains username, profile_pic, etc.
```

---

## Questions for You

### 1. Which identifiers do you need?

- [ ] `uid` only
- [ ] `user_id` only
- [x] Both `uid` and `user_id` (Recommended)

### 2. What sender information do you need?

- [x] Sender UID
- [x] Sender user_id
- [x] Sender username
- [x] Sender profile picture ID
- [ ] Other: _______________

### 3. Which implementation approach?

- [ ] Option A: Model-level changes (requires migration)
- [x] Option B: JSON data field only (no migration) - **Fastest**
- [ ] Option C: Hybrid approach (recommended for long-term)

### 4. Priority notifications to update first?

- [x] All user-triggered notifications
- [ ] Specific types only (list them)
- [ ] Start with post/comment notifications only

---

## Next Steps

Once you confirm the approach, I will:

1. ✅ Update notification service signatures
2. ✅ Update notification data payloads
3. ✅ Update all notification calls across the codebase
4. ✅ Update notification templates if using global service
5. ✅ Test with sample notifications
6. ✅ Create migration if needed (Option A or C)

**Please review and let me know which option you prefer!**
