# 📋 Notification GraphQL - Quick Reference Card

## 🚀 **TO ACTIVATE IN POSTMAN**

```bash
# 1. Restart server (REQUIRED!)
docker-compose restart web

# 2. In Postman: Schema tab → Click "Refresh"
# 3. Done! Queries will appear in autocomplete
```

---

## 🔍 **QUERIES**

### **Get Notifications (Paginated)**
```graphql
query {
  myNotifications(page: 1, pageSize: 20, isRead: false) {
    notifications { id title body isRead createdAt }
    totalCount
    unreadCount
    hasNext
  }
}
```

### **Get Single Notification**
```graphql
query {
  notification(notificationId: 123) {
    id title body status isRead
  }
}
```

### **Get Statistics**
```graphql
query {
  notificationStats {
    totalCount unreadCount readCount
  }
}
```

### **Get Preferences**
```graphql
query {
  notificationPreferences {
    notificationType isEnabled
  }
}
```

---

## ✏️ **MUTATIONS**

### **Mark as Read**
```graphql
mutation {
  markNotificationAsRead(notificationId: 123) {
    success message
  }
}
```

### **Mark All as Read**
```graphql
mutation {
  markAllNotificationsAsRead {
    success updatedCount
  }
}
```

### **Delete Notification**
```graphql
mutation {
  deleteNotification(notificationId: 123) {
    success message
  }
}
```

### **Delete All (Read Only)**
```graphql
mutation {
  deleteAllNotifications(isReadOnly: true) {
    success deletedCount
  }
}
```

### **Update Preference**
```graphql
mutation {
  updateNotificationPreference(
    notificationType: "new_comment_on_post"
    isEnabled: false
  ) {
    success message
  }
}
```

---

## 🔑 **Authentication**

**All requests require JWT token:**
```
Authorization: JWT <your_token>
```

**Get token:**
```graphql
mutation {
  tokenAuth(username: "user@example.com", password: "password") {
    token
  }
}
```

---

## 📊 **Filters**

| Parameter | Type | Options |
|-----------|------|---------|
| `page` | Int | 1, 2, 3... |
| `pageSize` | Int | 1-100 (default: 20) |
| `isRead` | Boolean | true, false, null (all) |
| `notificationType` | String | "new_post_from_connection", etc. |
| `status` | String | "pending", "sent", "failed", "read" |

---

## 🎯 **Common Use Cases**

### **1. Notification Bell Badge**
```graphql
query {
  notificationStats { unreadCount }
}
```

### **2. Notification List**
```graphql
query {
  myNotifications(page: 1, pageSize: 20) {
    notifications {
      id title body notificationType
      isRead createdAt clickAction
    }
    hasNext
  }
}
```

### **3. Mark All Read Button**
```graphql
mutation {
  markAllNotificationsAsRead {
    success updatedCount
  }
}
```

### **4. Clear Read Notifications**
```graphql
mutation {
  deleteAllNotifications(isReadOnly: true) {
    success deletedCount
  }
}
```

---

## 📁 **Files**

- **API Docs:** `notification/GRAPHQL_API_DOCUMENTATION.md`
- **Setup Guide:** `notification/SETUP_INTEGRATION_COMPLETE.md`
- **Summary:** `NOTIFICATION_GRAPHQL_SUMMARY.md`

---

## ⚠️ **Remember**

1. ✅ Restart server after integration
2. ✅ Refresh Postman schema
3. ✅ Add JWT token to headers
4. ✅ Max page size is 100

---

**Quick Start:**
```bash
docker-compose restart web
```
Then refresh Postman! 🎉
