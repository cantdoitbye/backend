# ✅ Deep Link & Web Link Fields - Update Complete

## 🎯 **Problem Solved**

Previously, `deep_link` and `web_link` were only stored in the `data` JSON field, making them harder to access in GraphQL queries. Now they are separate database fields!

---

## ✅ **Changes Made**

### **1. Database Model** (`notification/models.py`)
Added two new fields:
- `deep_link` - CharField for mobile deep links (e.g., `ooumph://post/123`)
- `web_link` - URLField for web links (e.g., `https://app.ooumph.com/post/123`)

### **2. GlobalNotificationService** (`notification/global_service.py`)
Updated to store deep_link and web_link when creating notifications

### **3. GraphQL Type** (`notification/graphql/types.py`)
Added `deep_link` and `web_link` to UserNotificationType fields

### **4. Migration** (`notification/migrations/0002_add_deep_link_web_link.py`)
Created migration to add the new database columns

### **5. Documentation**
- Updated `GRAPHQL_API_DOCUMENTATION.md`
- Created `MIGRATION_DEEP_LINK_WEB_LINK.md`

---

## 🚀 **How to Apply**

### **Step 1: Run Migration**
```bash
docker-compose exec web python manage.py migrate notification
```

### **Step 2: Restart Server**
```bash
docker-compose restart web
```

### **Step 3: Test in Postman**
```graphql
query {
  myNotifications(page: 1, pageSize: 5) {
    notifications {
      id
      title
      deepLink
      webLink
      clickAction
    }
  }
}
```

---

## 📊 **Before vs After**

### **Before (Old Way):**
```graphql
query {
  myNotifications {
    notifications {
      clickAction
      data  # Had to parse JSON to get deep_link and web_link
    }
  }
}
```

**Response:**
```json
{
  "clickAction": "/post/123",
  "data": {
    "deep_link": "ooumph://post/123",
    "web_link": "https://app.ooumph.com/post/123",
    "post_id": "123"
  }
}
```

### **After (New Way):**
```graphql
query {
  myNotifications {
    notifications {
      clickAction
      deepLink    # Direct access!
      webLink     # Direct access!
      data
    }
  }
}
```

**Response:**
```json
{
  "clickAction": "/post/123",
  "deepLink": "ooumph://post/123",
  "webLink": "https://app.ooumph.com/post/123",
  "data": {
    "post_id": "123",
    "username": "John"
  }
}
```

---

## 🎉 **Benefits**

✅ **Direct Access** - No need to parse JSON  
✅ **Type Safety** - Proper field types in GraphQL  
✅ **Cleaner Code** - Easier mobile/web integration  
✅ **Better Performance** - Can query/filter by deep_link  
✅ **Backward Compatible** - Old notifications still work  

---

## 📱 **Mobile App Usage**

```javascript
// React Native - Direct access to deepLink!
const Notification = ({ notification }) => (
  <TouchableOpacity 
    onPress={() => Linking.openURL(notification.deepLink)}
  >
    <Text>{notification.title}</Text>
  </TouchableOpacity>
);
```

---

## 🌐 **Web App Usage**

```javascript
// React - Direct access to webLink!
const Notification = ({ notification }) => (
  <a href={notification.webLink}>
    {notification.title}
  </a>
);
```

---

## ✅ **Verification**

### **Check Database:**
```sql
SELECT id, notification_type, deep_link, web_link 
FROM notification_usernotification 
ORDER BY created_at DESC 
LIMIT 5;
```

### **Check GraphQL:**
```graphql
query {
  myNotifications(page: 1, pageSize: 1) {
    notifications {
      deepLink
      webLink
    }
  }
}
```

---

## 📋 **Files Modified**

1. ✅ `notification/models.py` - Added fields
2. ✅ `notification/global_service.py` - Store fields
3. ✅ `notification/graphql/types.py` - Expose fields
4. ✅ `notification/migrations/0002_add_deep_link_web_link.py` - Migration
5. ✅ `notification/GRAPHQL_API_DOCUMENTATION.md` - Updated docs
6. ✅ `notification/MIGRATION_DEEP_LINK_WEB_LINK.md` - Migration guide

---

## ⚠️ **Important**

### **Must Run Migration:**
```bash
docker-compose exec web python manage.py migrate notification
```

### **Must Restart Server:**
```bash
docker-compose restart web
```

### **Then Refresh Postman Schema**

---

## 🎯 **Quick Test**

```bash
# 1. Run migration
docker-compose exec web python manage.py migrate notification

# 2. Restart server
docker-compose restart web

# 3. Test in Postman
# Query: myNotifications
# Check response has deepLink and webLink fields
```

---

**Status:** ✅ **READY TO MIGRATE**

**Next Steps:**
1. Run migration command
2. Restart server
3. Test in Postman
4. Verify deepLink and webLink appear in responses

🚀 **Your notifications now have direct deep_link and web_link access!**
