# ✅ Connection Query - Final Fix

## 🎯 **Correct Implementation**

After analyzing the actual Connection models and their relationships, here's the correct query:

### **Connection Model Details:**

| Model | Status | Relationship | Date Field |
|-------|--------|--------------|------------|
| **Connection** | `'Received'` | `HAS_RECIEVED_CONNECTION` (from receiver) | `timestamp` |
| **ConnectionV2** | `'Pending'` | `HAS_CONNECTION` (to receiver) | `created_date` |

---

## ✅ **Final Query**

```cypher
MATCH (receiver:Users)-[:PROFILE]->(profile:Profile)
WHERE profile.device_id IS NOT NULL

# Check Connection (old model)
OPTIONAL MATCH (receiver)<-[:HAS_RECIEVED_CONNECTION]-(conn:Connection)
WHERE conn.connection_status = 'Received'
AND conn.timestamp < datetime() - duration('P1D')

# Check ConnectionV2 (new model)
OPTIONAL MATCH (receiver)-[:HAS_CONNECTION]->(conn2:ConnectionV2)
WHERE conn2.connection_status = 'Pending'
AND conn2.created_date < datetime() - duration('P1D')

# Combine counts
WITH receiver, profile, count(conn) + count(conn2) as request_count
WHERE request_count > 0
RETURN receiver.uid, receiver.username, request_count, profile.device_id
```

---

## 📊 **Key Differences**

### **Connection (Old Model):**
- **Relationship:** `receiver <-[:HAS_RECIEVED_CONNECTION]- Connection`
- **Status:** `'Received'` (when request is sent)
- **Date Field:** `timestamp`
- **Mutation:** `send_connection` (deprecated)

### **ConnectionV2 (New Model):**
- **Relationship:** `receiver -[:HAS_CONNECTION]-> ConnectionV2`
- **Status:** `'Pending'` (when request is sent)
- **Date Field:** `created_date`
- **Mutation:** `send_connection_v2` (recommended)

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

## 🔍 **Verify in Neo4j Browser**

### **Check Connection (Old Model):**
```cypher
MATCH (receiver:Users)<-[:HAS_RECIEVED_CONNECTION]-(conn:Connection)
WHERE conn.connection_status = 'Received'
RETURN receiver.username, conn.connection_status, conn.timestamp
LIMIT 5
```

### **Check ConnectionV2 (New Model):**
```cypher
MATCH (receiver:Users)-[:HAS_CONNECTION]->(conn:ConnectionV2)
WHERE conn.connection_status = 'Pending'
RETURN receiver.username, conn.connection_status, conn.created_date
LIMIT 5
```

### **Check Both Together:**
```cypher
MATCH (receiver:Users)-[:PROFILE]->(profile:Profile)
WHERE profile.device_id IS NOT NULL
OPTIONAL MATCH (receiver)<-[:HAS_RECIEVED_CONNECTION]-(conn:Connection)
WHERE conn.connection_status = 'Received'
OPTIONAL MATCH (receiver)-[:HAS_CONNECTION]->(conn2:ConnectionV2)
WHERE conn2.connection_status = 'Pending'
WITH receiver, count(conn) + count(conn2) as total
WHERE total > 0
RETURN receiver.username, total
```

---

## 📝 **Files Updated**

1. ✅ `notification/management/commands/send_scheduled_notifications.py`
   - Fixed relationship names
   - Fixed date field names
   - Now correctly queries both models

2. ✅ `notification/management/commands/check_notification_data.py`
   - Fixed relationship names
   - Fixed date field names
   - Shows accurate counts

---

## ⚠️ **Important Notes**

### **Relationship Direction:**
- **Connection:** `receiver <-[:HAS_RECIEVED_CONNECTION]- conn` (incoming)
- **ConnectionV2:** `receiver -[:HAS_CONNECTION]-> conn` (outgoing)

### **Date Fields:**
- **Connection:** Uses `timestamp` field
- **ConnectionV2:** Uses `created_date` field

### **Status Values:**
- **Connection:** `'Received'` (case-sensitive!)
- **ConnectionV2:** `'Pending'` (case-sensitive!)

---

## 🎯 **Quick Test Commands**

```bash
# 1. Check what data exists
docker-compose exec hey_backend python manage.py check_notification_data

# 2. Test scheduled notifications
docker-compose exec hey_backend python manage.py send_scheduled_notifications --dry-run

# 3. If still no results, check in Neo4j:
# Open Neo4j Browser and run:
MATCH (c:Connection) WHERE c.connection_status = 'Received' RETURN count(c)
MATCH (c:ConnectionV2) WHERE c.connection_status = 'Pending' RETURN count(c)
```

---

## ✅ **Summary**

**Fixed Issues:**
1. ✅ Correct relationship names (`HAS_RECIEVED_CONNECTION` vs `HAS_CONNECTION`)
2. ✅ Correct date fields (`timestamp` vs `created_date`)
3. ✅ Correct status values (`'Received'` vs `'Pending'`)
4. ✅ Correct relationship directions (incoming vs outgoing)

**The query now correctly checks both Connection models with their actual structure!** 🎉

---

**Status:** ✅ **FINAL FIX APPLIED - READY TO TEST**

Run the test commands above to verify! 🚀
