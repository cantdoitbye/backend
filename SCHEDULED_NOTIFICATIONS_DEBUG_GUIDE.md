# 🐛 Scheduled Notifications - Debug Guide

## 📋 **Issue: No Notifications Being Sent**

If you're seeing "Total sent: 0" when running scheduled notifications, use this guide to debug.

---

## 🔍 **Step 1: Check What Data Exists**

Run the debug command to see what data is available:

```bash
docker-compose exec hey_backend python manage.py check_notification_data
```

**This will show:**
- Total users in database
- Users with profiles
- Users with device_id (can receive notifications)
- Incomplete profiles
- Pending connections
- Users with interests
- New users

---

## 📊 **Understanding the Output**

### **Example Output:**
```
🔍 CHECKING NOTIFICATION DATA

📊 Total Users:
   Total users: 150

👤 Users with Profiles:
   Users with profiles: 145

📱 Users with Device ID:
   Users with device_id: 12
   Sample users:
     - john_doe
     - jane_smith
     - test_user

📝 Incomplete Profiles:
   Incomplete profiles (last 30 days): 8
   Sample incomplete profiles:
     - new_user (missing: bio, pic, city)
     - another_user (missing: state)

🔗 Pending Connections:
   Total pending connections: 5
   Users with old pending requests (>24h): 2
   Total old pending requests: 3

🎯 Users with Interests:
   Users with interests: 10
   Sample users with interests:
     - john_doe: AI, ML, Python
     - jane_smith: Web Dev, React

🆕 New Users (Last 24 Hours):
   New users (last 24h): 2
   New users (last 7 days): 15
```

---

## ⚠️ **Common Issues**

### **Issue 1: No Users with device_id**

**Problem:**
```
📱 Users with Device ID:
   Users with device_id: 0
```

**Cause:** Users haven't logged in from mobile app or device_id not set

**Solution:**
- Users need to log in from mobile app to get FCM token
- Or manually set device_id for testing:

```cypher
MATCH (user:Users {email: "test@example.com"})-[:PROFILE]->(profile:Profile)
SET profile.device_id = "test_fcm_token_123"
RETURN profile
```

---

### **Issue 2: No Incomplete Profiles**

**Problem:**
```
📝 Incomplete Profiles:
   Incomplete profiles (last 30 days): 0
```

**Cause:** All users have complete profiles OR no users created in last 30 days

**What's Checked:**
- `bio` is empty
- `profile_pic_id` is empty
- `city` is empty
- `state` is empty

**Solution:** Check if you have recent users with incomplete data

---

### **Issue 3: No Pending Connections**

**Problem:**
```
🔗 Pending Connections:
   Total pending connections: 0
```

**Cause:** No pending connection requests OR using old Connection model

**Solution:**
- Check if you're using `ConnectionV2` model
- Create test connection requests
- Verify connection_status is "Pending" (case-sensitive)

---

### **Issue 4: No Users with Interests**

**Problem:**
```
🎯 Users with Interests:
   Users with interests: 0
```

**Cause:** Users haven't set interests in their profiles

**Solution:** Add interests to user profiles:

```cypher
MATCH (user:Users {email: "test@example.com"})-[:PROFILE]->(profile:Profile)
SET profile.interests = ["AI", "Machine Learning", "Python"]
RETURN profile
```

---

## 🧪 **Testing Scheduled Notifications**

### **Step 1: Check Data**
```bash
docker-compose exec hey_backend python manage.py check_notification_data
```

### **Step 2: Run Dry Run**
```bash
docker-compose exec hey_backend python manage.py send_scheduled_notifications --dry-run
```

### **Step 3: If Still No Results, Create Test Data**

#### **Create User with Incomplete Profile:**
```cypher
MATCH (user:Users {email: "test@example.com"})-[:PROFILE]->(profile:Profile)
SET profile.bio = null,
    profile.city = null,
    profile.device_id = "test_device_123"
SET user.created_date = datetime() - duration('P5D')
RETURN user, profile
```

#### **Create Pending Connection:**
```cypher
MATCH (user1:Users {email: "user1@example.com"})
MATCH (user2:Users {email: "user2@example.com"})
CREATE (conn:ConnectionV2 {
    uid: randomUUID(),
    connection_status: "Pending",
    created_date: datetime() - duration('P2D')
})
CREATE (user1)-[:CONNECTIONV2]->(conn)
CREATE (user2)-[:CONNECTIONV2]->(conn)
RETURN conn
```

#### **Add Interests:**
```cypher
MATCH (user:Users {email: "test@example.com"})-[:PROFILE]->(profile:Profile)
SET profile.interests = ["Web Development", "React", "JavaScript"],
    profile.device_id = "test_device_123"
RETURN profile
```

---

## 📝 **What Each Notification Checks**

### **1. Profile Edit Reminder**
**Checks:**
- User created in last 30 days (changed from 7 days)
- Has device_id
- Missing: bio OR profile_pic OR city OR state

**Query:**
```cypher
MATCH (user:Users)-[:PROFILE]->(profile:Profile)
WHERE user.created_date > datetime() - duration('P30D')
AND profile.device_id IS NOT NULL
AND (
    profile.bio IS NULL OR profile.bio = '' OR 
    profile.profile_pic_id IS NULL OR profile.profile_pic_id = '' OR
    profile.city IS NULL OR profile.city = '' OR
    profile.state IS NULL OR profile.state = ''
)
RETURN user, profile
```

---

### **2. Pending Connection Requests**
**Checks:**
- ConnectionV2 with status "Pending"
- Created more than 24 hours ago
- Receiver has device_id

**Query:**
```cypher
MATCH (receiver:Users)-[:CONNECTIONV2]->(conn:ConnectionV2)
WHERE conn.connection_status = 'Pending'
AND conn.created_date < datetime() - duration('P1D')
MATCH (receiver)-[:PROFILE]->(profile:Profile)
WHERE profile.device_id IS NOT NULL
RETURN receiver, conn, profile
```

---

### **3. Trending Topics**
**Checks:**
- User has interests
- User has device_id
- Matches with trending topics

---

### **4. Community Suggestions**
**Checks:**
- User has interests
- User has device_id
- User is in less than 3 communities

---

### **5. New User Notifications**
**Checks:**
- New users created in last 24 hours
- New user has interests
- Find existing users with matching interests
- Existing users have device_id

---

## 🎯 **Quick Fix for Testing**

If you want to test immediately, create a test user with all required data:

```bash
docker-compose exec hey_backend python manage.py shell
```

```python
from auth_manager.models import Users, Profile
from django.contrib.auth.models import User
from datetime import datetime, timedelta

# Create Django user
django_user = User.objects.create_user(
    username='test_notification@example.com',
    email='test_notification@example.com',
    password='testpass123'
)

# Get Neo4j user
user_node = Users.nodes.get(user_id=str(django_user.id))

# Get or create profile
profile = user_node.profile.single()
if not profile:
    profile = Profile(user_id=str(django_user.id))
    profile.save()
    profile.user.connect(user_node)
    user_node.profile.connect(profile)

# Set test data
profile.device_id = "test_fcm_token_for_notifications"
profile.bio = None  # Incomplete
profile.city = None  # Incomplete
profile.interests = ["AI", "Python", "Web Development"]
profile.save()

# Set user created date to 5 days ago
user_node.created_date = datetime.now() - timedelta(days=5)
user_node.save()

print(f"✅ Test user created: {user_node.email}")
print(f"   UID: {user_node.uid}")
print(f"   Device ID: {profile.device_id}")
print(f"   Incomplete: bio={profile.bio}, city={profile.city}")
```

---

## ✅ **Verification**

After creating test data, run:

```bash
# Check data
docker-compose exec hey_backend python manage.py check_notification_data

# Should now show:
# - Users with device_id: 1+
# - Incomplete profiles: 1+

# Test dry run
docker-compose exec hey_backend python manage.py send_scheduled_notifications --dry-run

# Should now show:
# - Would send profile reminder to test_notification@example.com
```

---

## 📚 **Commands Reference**

```bash
# Check what data exists
docker-compose exec hey_backend python manage.py check_notification_data

# Test scheduled notifications (dry run)
docker-compose exec hey_backend python manage.py send_scheduled_notifications --dry-run

# Send actual notifications
docker-compose exec hey_backend python manage.py send_scheduled_notifications

# Check specific notification type
docker-compose exec hey_backend python manage.py send_daily_notifications --type profile_reminders --dry-run
```

---

**Status:** ✅ **DEBUG TOOLS READY**

Run `check_notification_data` to see what's in your database! 🔍
