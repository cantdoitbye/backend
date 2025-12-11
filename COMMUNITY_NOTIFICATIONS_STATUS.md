# 🏘️ Community Notifications - Status Report

## 📋 **Overview**

This document shows which community mutations send notifications and which notification templates they use.

---

## ✅ **Mutations with Notifications**

### **1. AddMember** ✅
**Purpose:** Add new members to a community

**Notification Sent:** YES ✅

**Template Used:** `new_members_joined`

**Recipients:** New members being added

**Code Location:** Line ~1056

**Notification Details:**
```python
service.send(
    event_type="new_members_joined",
    recipients=members_to_notify,  # New members
    username=user.username,         # Admin who added them
    community_name=community.name,
    community_id=community.uid,
    community_icon=community.group_icon_id
)
```

**Template:**
```python
"new_members_joined": {
    "title": "New Members Joined!",
    "body": "{username} joined {community_name}. Say hello!",
    "click_action": "/community/{community_id}/members",
    "deep_link": "ooumph://community/{community_id}/members",
    "web_link": "https://app.ooumph.com/community/{community_id}/members",
    "priority": "normal"
}
```

---

### **2. AddSubCommunityMember** ✅
**Purpose:** Add members to a sub-community

**Notification Sent:** YES ✅

**Template Used:** `new_members_joined`

**Recipients:** New members being added

**Code Location:** Line ~1328

**Same implementation as AddMember**

---

### **3. CreateCommunityV2** ✅
**Purpose:** Create a new community

**Notification Sent:** YES ✅

**Template Used:** `user_joined_community`

**Recipients:** Initial members added to the community

**Code Location:** Line ~4875

**Notification Details:**
```python
service.send(
    event_type="user_joined_community",
    recipients=members_to_notify,  # Initial members
    username=created_by.username,   # Community creator
    community_name=community.name,
    community_id=community.uid,
    community_icon=community.group_icon_id
)
```

**Template:**
```python
"user_joined_community": {
    "title": "Welcome {username} to {community_name}!",
    "body": "You are now part of {community_name}.",
    "image_url": "{community_icon}",
    "click_action": "/community/{community_id}",
    "deep_link": "ooumph://community/{community_id}",
    "web_link": "https://app.ooumph.com/community/{community_id}",
    "priority": "normal"
}
```

---

### **4. JoinGeneratedCommunity** ❓
**Purpose:** Join a generated community

**Notification Sent:** NEED TO CHECK

Let me check this mutation:

---

## 🔍 **Analysis**

### **Current Behavior:**

1. **AddMember** - Notifies the **new members** that they were added
   - Template: `new_members_joined`
   - Message: "{username} joined {community_name}. Say hello!"
   - This is slightly confusing because it says "{username} joined" but it's sent TO the new member

2. **CreateCommunityV2** - Notifies **initial members** that they joined
   - Template: `user_joined_community`
   - Message: "Welcome {username} to {community_name}!"
   - This makes more sense - welcoming the user

---

## 💡 **Recommendation**

The notification logic seems backwards in `AddMember`. Consider:

### **Option 1: Keep Current (Notify New Members)**
- When admin adds members, notify the new members they were added
- Current template: `new_members_joined`
- Message should be: "You were added to {community_name} by {username}"

### **Option 2: Notify Existing Members**
- When new members join, notify existing members
- Use template: `new_members_joined`
- Message: "{username} joined {community_name}. Say hello!"
- Recipients: Existing community members (not the new member)

### **Option 3: Notify Both**
- Notify new member: "Welcome to {community_name}!"
- Notify existing members: "{username} joined {community_name}!"

---

## 📝 **Current Template Issues**

### **Template: `new_members_joined`**
```python
"title": "New Members Joined!",
"body": "{username} joined {community_name}. Say hello!",
```

**Problem:** This template is sent TO the new member, but the message says "{username} joined" which is confusing.

**Fix Options:**

#### **Option A: Change Template Message**
```python
"new_members_joined": {
    "title": "Welcome to {community_name}!",
    "body": "You were added by {username}. Start connecting!",
    # ...
}
```

#### **Option B: Change Recipients**
Send to existing members instead of new members:
```python
# In AddMember mutation
# Get existing members
existing_members = []
for membership in community.members.all():
    member_user = membership.user.single()
    if member_user and member_user.uid not in user_uids:  # Not the new member
        profile = member_user.profile.single()
        if profile and profile.device_id:
            existing_members.append({
                'device_id': profile.device_id,
                'uid': member_user.uid
            })

# Send to existing members
service.send(
    event_type="new_members_joined",
    recipients=existing_members,  # Changed!
    username=new_member.username,  # The new member's name
    community_name=community.name,
    community_id=community.uid
)
```

---

## ✅ **Verification Checklist**

- [x] AddMember sends notifications
- [x] AddSubCommunityMember sends notifications
- [x] CreateCommunityV2 sends notifications
- [ ] JoinGeneratedCommunity - Need to check
- [ ] Template messages match recipient expectations
- [ ] Recipients are correct (new members vs existing members)

---

## 🧪 **Testing**

### **Test AddMember Notification:**

```graphql
mutation {
  addMember(input: {
    communityUid: "community_123"
    userUid: ["user_456"]
  }) {
    success
    message
  }
}
```

**Expected:**
- New member (user_456) receives notification
- Notification says: "New Members Joined! {username} joined {community_name}. Say hello!"
- But {username} is the admin who added them, not the new member

**This seems incorrect!** 🤔

---

## 🎯 **Recommended Fix**

### **Update AddMember to notify existing members:**

```python
# In AddMember mutation, after adding members:

# Collect existing members (not the new ones)
existing_members = []
for membership in community.members.all():
    member_user = membership.user.single()
    if member_user and member_user.uid not in user_uids:  # Exclude new members
        profile = member_user.profile.single()
        if profile and profile.device_id:
            existing_members.append({
                'device_id': profile.device_id,
                'uid': member_user.uid
            })

# Notify existing members about new members
if existing_members and user_uids:
    try:
        from notification.global_service import GlobalNotificationService
        
        # Get first new member's name for notification
        first_new_member = Users.nodes.get(uid=user_uids[0])
        
        service = GlobalNotificationService()
        service.send(
            event_type="new_members_joined",
            recipients=existing_members,  # Existing members
            username=first_new_member.username,  # New member's name
            community_name=community.name,
            community_id=community.uid
        )
    except Exception as e:
        print(f"Failed to send new member notification: {e}")

# Also notify new members they were added
if members_to_notify:
    try:
        service = GlobalNotificationService()
        service.send(
            event_type="user_joined_community",  # Different template
            recipients=members_to_notify,  # New members
            username=user.username,  # Admin who added them
            community_name=community.name,
            community_id=community.uid
        )
    except Exception as e:
        print(f"Failed to send welcome notification: {e}")
```

---

## 📊 **Summary**

| Mutation | Sends Notification | Template | Recipients | Issue |
|----------|-------------------|----------|------------|-------|
| AddMember | ✅ Yes | `new_members_joined` | New members | ⚠️ Message doesn't match recipient |
| AddSubCommunityMember | ✅ Yes | `new_members_joined` | New members | ⚠️ Same issue |
| CreateCommunityV2 | ✅ Yes | `user_joined_community` | Initial members | ✅ Correct |

**Recommendation:** Fix AddMember to either:
1. Change the template message to match new member recipient
2. Change recipients to existing members
3. Send two notifications (one to new members, one to existing)

---

**Status:** ✅ **NOTIFICATIONS ARE BEING SENT**

**Issue:** ⚠️ **Template message doesn't match recipient in AddMember**

Would you like me to fix this? 🔧
