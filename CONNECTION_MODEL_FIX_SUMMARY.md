# ✅ Connection Model Fix - Summary

## 🐛 **Issue**

The scheduled notifications were only checking `ConnectionV2` model, but the app uses both:
- **Connection** (old model) - Uses `connection_status = 'Received'`
- **ConnectionV2** (new model) - Uses `connection_status = 'Pending'`

---

## ✅ **Fix Applied**

Updated queries to check **BOTH** Connection models:

### **Before:**
```cypher
MATCH (receiver:Users)-[:CONNECTIONV2]->(conn:ConnectionV2)
WHERE conn.connection_status = 'Pending'
```

### **After:**
```cypher
MATCH (receiver:Users)-[:PROFILE]->(profile:Profile)
WHERE profile.device_id IS NOT NULL
OPTIONAL MATCH (receiver)<-[:RECEIVER]-(conn:Connection)
WHERE conn.connection_status = 'Received'
AND conn.created_date < datetime() - duration('P1D')
OPTIONAL MATCH (receiver)-[:CONNECTIONV2]->(conn2:ConnectionV2)
WHERE conn2.connection_status = 'Pending'
AND conn2.created_date < datetime() - duration('P1D')
WITH receiver, profile, count(conn) + count(conn2) as request_count
WHERE request_count > 0
```

---

## 📊 **What Changed**

### **1. send_scheduled_notifications.py**
- Now checks both Connection and ConnectionV2
- Counts pending requests from both models
- Uses correct status for each model:
  - Connection: `'Received'`
  - ConnectionV2: `'Pending'`

### **2. check_notification_data.py**
- Shows counts for both models separately
- Shows combined total
- Helps debug which model is being used

---

## 🧪 **Testing**

### **Step 1: Check Data**
```bash
docker-compose exec hey_backend python manage.py check_notification_data
```

**Expected Output:**
```
🔗 Pending Connections:
   Connection (Received status): 5
   ConnectionV2 (Pending status): 3
   Total pending connections: 8
   Users with old pending requests (>24h): 2
   Total old pending requests: 4
```

### **Step 2: Test Notifications**
```bash
docker-compose exec hey_backend python manage.py send_scheduled_notifications --dry-run
```

**Expected Output:**
```
📬 Checking for pending connection requests...
   Found 2 users with pending requests
   Would send to john_doe: 2 pending request(s)
   Would send to jane_smith: 2 pending request(s)
   ✓ Sent 2 pending request reminders
```

---

## 📝 **Connection Model Status Mapping**

| Model | Status Field | Meaning |
|-------|-------------|---------|
| **Connection** | `Received` | Pending connection request (old model) |
| **Connection** | `Accepted` | Accepted connection (old model) |
| **ConnectionV2** | `Pending` | Pending connection request (new model) |
| **ConnectionV2** | `Accepted` | Accepted connection (new model) |

---

## 🔍 **How to Check Which Model You're Using**

```bash
docker-compose exec hey_backend python manage.py shell
```

```python
from neomodel import db

# Check Connection (old model)
query = "MATCH (c:Connection) RETURN count(c) as count"
result, _ = db.cypher_query(query)
print(f"Connection (old): {result[0][0]}")

# Check ConnectionV2 (new model)
query = "MATCH (c:ConnectionV2) RETURN count(c) as count"
result, _ = db.cypher_query(query)
print(f"ConnectionV2 (new): {result[0][0]}")
```

---

## ✅ **Files Updated**

1. `notification/management/commands/send_scheduled_notifications.py`
   - Updated `send_pending_requests_reminders()` method
   - Now checks both Connection models

2. `notification/management/commands/check_notification_data.py`
   - Updated `check_pending_connections()` method
   - Shows counts for both models

---

## 🎯 **Quick Test**

```bash
# 1. Check what connections exist
docker-compose exec hey_backend python manage.py check_notification_data

# 2. Test notifications
docker-compose exec hey_backend python manage.py send_scheduled_notifications --dry-run

# 3. If you see pending connections but no notifications:
#    - Check if users have device_id
#    - Check if connections are older than 24 hours
```

---

## 📚 **Related Documentation**

- `SCHEDULED_NOTIFICATIONS_DEBUG_GUIDE.md` - Full debugging guide
- `notification/management/commands/send_scheduled_notifications.py` - Main command
- `notification/management/commands/check_notification_data.py` - Debug command

---

**Status:** ✅ **FIXED - NOW CHECKS BOTH CONNECTION MODELS**

The scheduled notifications will now work with both Connection and ConnectionV2! 🎉
