# Notification System - Quick Start Guide

## 🚀 **How to Add Notifications to Your Mutation**

### **Step 1: Import GlobalNotificationService**

```python
from notification.global_service import GlobalNotificationService
```

### **Step 2: Gather Recipients**

Recipients must have:
- `device_id` (FCM token from user profile)
- `uid` (user UID)

```python
recipients = []
for user in users_to_notify:
    profile = user.profile.single()
    if profile and profile.device_id:
        recipients.append({
            'device_id': profile.device_id,
            'uid': user.uid
        })
```

### **Step 3: Send Notification**

```python
if recipients:
    try:
        service = GlobalNotificationService()
        service.send(
            event_type="notification_template_name",  # From notification_templates.py
            recipients=recipients,
            # Template variables (placeholders in template)
            username="John Doe",
            post_id="123",
            community_name="Tech Community"
        )
    except Exception as e:
        print(f"Failed to send notification: {e}")
```

---

## 📋 **Available Templates**

### **Post & Feed**
- `new_post_from_connection` - Connection posts new content
- `new_comment_on_post` - Someone comments on your post
- `post_comment` - New comment notification
- `vibe_reaction_on_post` - Someone vibes with your post

### **Connections**
- `new_connection_request` - Someone wants to connect
- `connection_accepted` - Connection request accepted
- `connection_rejected` - Connection request declined

### **Community**
- `new_community_post` - New post in community
- `user_joined_community` - User joined community
- `new_child_community` - Child community created
- `new_sibling_community` - Sibling community created
- `community_post_comment` - Comment on community post
- `community_post_reaction` - Reaction on community post
- `new_members_joined` - New members joined community

### **Story**
- `new_story_from_connection` - Connection shares story
- `story_reaction` - Someone reacts to your story
- `story_mention` - You're mentioned in a story

### **Profile**
- `achievement_added` - Achievement unlocked
- `education_added` - Education updated
- `experience_added` - Work experience added
- `skill_added` - Skill added
- `profile_viewed` - Someone viewed your profile
- `vibe_sent_to_profile` - Vibe received

### **Authentication & Security**
- `password_reset_success` - Password successfully reset
- `signup_completed` - User signup completed

**See `notification/notification_templates.py` for complete list**

---

## 💡 **Examples**

### **Example 1: Notify Post Creator of New Comment**

```python
# In CreateComment mutation
post_creator = post.created_by.single()

if post_creator and post_creator.uid != commenter.uid:
    creator_profile = post_creator.profile.single()
    if creator_profile and creator_profile.device_id:
        try:
            from notification.global_service import GlobalNotificationService
            
            service = GlobalNotificationService()
            service.send(
                event_type="new_comment_on_post",
                recipients=[{
                    'device_id': creator_profile.device_id,
                    'uid': post_creator.uid
                }],
                username=commenter.username,
                post_id=post.uid
            )
        except Exception as e:
            print(f"Failed to send comment notification: {e}")
```

### **Example 2: Notify Community Members of New Post**

```python
# In CreateCommunityPost mutation
members = community.members.all()
recipients = []

for member in members:
    user = member.user.single()
    if user and user.uid != creator.uid:  # Don't notify creator
        profile = user.profile.single()
        if profile and profile.device_id:
            recipients.append({
                'device_id': profile.device_id,
                'uid': user.uid
            })

if recipients:
    try:
        from notification.global_service import GlobalNotificationService
        
        service = GlobalNotificationService()
        service.send(
            event_type="new_community_post",
            recipients=recipients,
            username=creator.username,
            community_name=community.name,
            post_id=post.uid,
            community_id=community.uid,
            post_image_url=post.post_file_id[0] if post.post_file_id else None
        )
    except Exception as e:
        print(f"Failed to send community post notification: {e}")
```

### **Example 3: Notify Story Creator of Reaction**

```python
# In CreateStoryReaction mutation
story_creator = story.created_by.single()

if story_creator and story_creator.uid != reactor.uid:
    creator_profile = story_creator.profile.single()
    if creator_profile and creator_profile.device_id:
        try:
            from notification.global_service import GlobalNotificationService
            
            service = GlobalNotificationService()
            service.send(
                event_type="story_reaction",
                recipients=[{
                    'device_id': creator_profile.device_id,
                    'uid': story_creator.uid
                }],
                username=reactor.username,
                story_id=story.uid
            )
        except Exception as e:
            print(f"Failed to send story reaction notification: {e}")
```

### **Example 4: Notify User of Password Reset Success**

```python
# In VerifyOTPAndResetPassword mutation
try:
    from notification.global_service import GlobalNotificationService
    
    # Get user node and profile
    user_node = Users.nodes.get(user_id=str(user.id))
    profile = user_node.profile.single()
    
    if profile and profile.device_id:
        notification_service = GlobalNotificationService()
        notification_service.send(
            event_type="password_reset_success",
            recipients=[{
                'device_id': profile.device_id,
                'uid': user_node.uid
            }]
        )
except Exception as e:
    # Don't fail the password reset if notification fails
    print(f"Failed to send password reset notification: {e}")
```

### **Example 5: Notify User of Signup Completion**

```python
# In CreateUser mutation
try:
    from notification.global_service import GlobalNotificationService
    
    # Get user profile
    profile = user_node.profile.single()
    
    if profile and profile.device_id:
        notification_service = GlobalNotificationService()
        notification_service.send(
            event_type="signup_completed",
            recipients=[{
                'device_id': profile.device_id,
                'uid': user_node.uid
            }],
            username=user_node.username or email.split('@')[0]
        )
except Exception as e:
    # Don't fail the signup if notification fails
    print(f"Failed to send signup completion notification: {e}")
```

---

## 🎯 **Template Variables**

Each template has placeholders that need to be filled. Common variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `username` | Acting user's name | "John Doe" |
| `user_id` | User UID | "user_123" |
| `post_id` | Post UID | "post_456" |
| `story_id` | Story UID | "story_789" |
| `community_id` | Community UID | "comm_101" |
| `community_name` | Community name | "Tech Community" |
| `comment_text` | Comment content | "Great post!" |
| `post_image_url` | Post image URL | "https://..." |
| `achievement_name` | Achievement name | "Super Contributor" |
| `achievement_icon` | Achievement icon URL | "https://..." |

**Check the template definition in `notification/notification_templates.py` to see required variables**

---

## 📦 **Notification Payload Structure**

The notification service automatically generates this payload:

```json
{
  "title": "John Doe just posted something new!",
  "body": "Check it out.",
  "image_url": "https://cdn.example.com/image.jpg",
  "click_action": "/post/123",
  "deep_link": "ooumph://post/123",
  "web_link": "https://app.ooumph.com/post/123",
  "priority": "high",
  "data": {
    "type": "new_post_from_connection",
    "username": "John Doe",
    "post_id": "123",
    "post_image_url": "https://cdn.example.com/image.jpg"
  }
}
```

---

## ⚠️ **Best Practices**

### **1. Always Wrap in Try-Except**
```python
try:
    service.send(...)
except Exception as e:
    print(f"Failed to send notification: {e}")
    # Don't fail the mutation if notification fails
```

### **2. Don't Notify the Actor**
```python
if user.uid != actor.uid:  # Don't notify yourself
    # Send notification
```

### **3. Check Device ID Exists**
```python
profile = user.profile.single()
if profile and profile.device_id:
    # Send notification
```

### **4. Filter Valid Recipients**
```python
recipients = []
for user in users:
    profile = user.profile.single()
    if profile and profile.device_id:  # Only users with device tokens
        recipients.append({
            'device_id': profile.device_id,
            'uid': user.uid
        })
```

### **5. Use Appropriate Event Type**
```python
# Use the correct template name from notification_templates.py
event_type="new_post_from_connection"  # ✅ Correct
event_type="new_post"                   # ❌ Wrong (doesn't exist)
```

---

## 🔍 **Debugging**

### **Check if Notification Was Sent**

```sql
-- Check notification log
SELECT * FROM notification_log 
WHERE notification_type = 'new_post_from_connection' 
ORDER BY created_at DESC 
LIMIT 10;

-- Check individual notifications
SELECT * FROM user_notification 
WHERE user_uid = 'user_123' 
ORDER BY created_at DESC 
LIMIT 10;
```

### **Common Issues**

| Issue | Solution |
|-------|----------|
| No notification sent | Check if recipients have `device_id` |
| Template not found | Verify event_type exists in `notification_templates.py` |
| Missing placeholders | Check template definition for required variables |
| Notification failed | Check `error_message` in `user_notification` table |
| Wrong deep link | Verify template has correct `deep_link` format |

---

## 📱 **Testing**

### **Test Notification Manually**

```python
# In Django shell or test script
from notification.global_service import GlobalNotificationService

service = GlobalNotificationService()
service.send(
    event_type="new_post_from_connection",
    recipients=[{
        'device_id': 'YOUR_FCM_TOKEN',
        'uid': 'test_user_123'
    }],
    username="Test User",
    post_id="test_post_456"
)
```

### **Verify in Database**

```sql
-- Check if notification was created
SELECT * FROM user_notification 
WHERE user_uid = 'test_user_123' 
ORDER BY created_at DESC 
LIMIT 1;

-- Check notification status
SELECT status, error_message 
FROM user_notification 
WHERE user_uid = 'test_user_123' 
ORDER BY created_at DESC 
LIMIT 1;
```

---

## 🆘 **Need Help?**

1. Check `notification/notification_templates.py` for available templates
2. Review `NOTIFICATION_IMPLEMENTATION_SUMMARY.md` for detailed documentation
3. Look at existing mutations (CreatePost, CreateLike) for examples
4. Check application logs for error messages
5. Verify notification service URL is configured correctly

---

**Happy Coding! 🎉**
