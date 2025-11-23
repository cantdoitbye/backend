# Notification GraphQL API Documentation

## 📋 **Overview**

Complete GraphQL API for managing user notifications with pagination, filtering, and preferences.

---

## 🔍 **Queries**

### **1. myNotifications - Get Paginated Notifications**

Get paginated list of notifications for the current user with filtering options.

#### **Query:**
```graphql
query GetMyNotifications(
  $page: Int = 1
  $pageSize: Int = 20
  $isRead: Boolean
  $notificationType: String
  $status: String
) {
  myNotifications(
    page: $page
    pageSize: $pageSize
    isRead: $isRead
    notificationType: $notificationType
    status: $status
  ) {
    notifications {
      id
      userUid
      notificationType
      title
      body
      deviceId
      status
      priority
      clickAction
      deepLink
      webLink
      imageUrl
      data
      errorMessage
      isRead
      readAt
      sentAt
      createdAt
    }
    totalCount
    page
    pageSize
    totalPages
    hasNext
    hasPrevious
    unreadCount
  }
}
```

#### **Variables:**
```json
{
  "page": 1,
  "pageSize": 20,
  "isRead": false,
  "notificationType": "new_post_from_connection",
  "status": "sent"
}
```

#### **Response:**
```json
{
  "data": {
    "myNotifications": {
      "notifications": [
        {
          "id": 123,
          "userUid": "user_abc123",
          "notificationType": "new_post_from_connection",
          "title": "John Doe just posted something new!",
          "body": "Check it out.",
          "deviceId": "fcm_token_xyz",
          "status": "sent",
          "priority": "high",
          "clickAction": "/post/456",
          "deepLink": "ooumph://post/456",
          "webLink": "https://app.ooumph.com/post/456",
          "imageUrl": "https://cdn.example.com/image.jpg",
          "data": {
            "post_id": "456",
            "username": "John Doe"
          },
          "errorMessage": null,
          "isRead": false,
          "readAt": null,
          "sentAt": "2025-11-20T10:30:00Z",
          "createdAt": "2025-11-20T10:30:00Z"
        }
      ],
      "totalCount": 45,
      "page": 1,
      "pageSize": 20,
      "totalPages": 3,
      "hasNext": true,
      "hasPrevious": false,
      "unreadCount": 12
    }
  }
}
```

#### **Parameters:**
- `page` (Int, default: 1): Page number (starts at 1)
- `pageSize` (Int, default: 20): Items per page (max 100)
- `isRead` (Boolean, optional): Filter by read status
  - `true`: Only read notifications
  - `false`: Only unread notifications
  - `null`: All notifications
- `notificationType` (String, optional): Filter by notification type
- `status` (String, optional): Filter by status (pending/sent/failed/read)

---

### **2. notification - Get Single Notification**

Get a single notification by ID.

#### **Query:**
```graphql
query GetNotification($notificationId: Int!) {
  notification(notificationId: $notificationId) {
    id
    userUid
    notificationType
    title
    body
    status
    priority
    clickAction
    imageUrl
    data
    isRead
    readAt
    sentAt
    createdAt
  }
}
```

#### **Variables:**
```json
{
  "notificationId": 123
}
```

---

### **3. notificationStats - Get Statistics**

Get notification statistics for the current user.

#### **Query:**
```graphql
query GetNotificationStats {
  notificationStats {
    totalCount
    unreadCount
    readCount
    pendingCount
    sentCount
    failedCount
  }
}
```

#### **Response:**
```json
{
  "data": {
    "notificationStats": {
      "totalCount": 45,
      "unreadCount": 12,
      "readCount": 33,
      "pendingCount": 2,
      "sentCount": 40,
      "failedCount": 3
    }
  }
}
```

---

### **4. notificationPreferences - Get Preferences**

Get notification preferences for the current user.

#### **Query:**
```graphql
query GetNotificationPreferences {
  notificationPreferences {
    id
    notificationType
    isEnabled
    createdAt
    updatedAt
  }
}
```

#### **Response:**
```json
{
  "data": {
    "notificationPreferences": [
      {
        "id": 1,
        "notificationType": "new_post_from_connection",
        "isEnabled": true,
        "createdAt": "2025-11-01T10:00:00Z",
        "updatedAt": "2025-11-01T10:00:00Z"
      },
      {
        "id": 2,
        "notificationType": "new_comment_on_post",
        "isEnabled": false,
        "createdAt": "2025-11-01T10:00:00Z",
        "updatedAt": "2025-11-15T14:30:00Z"
      }
    ]
  }
}
```

---

### **5. notificationLogs - Get Logs (Admin Only)**

Get notification batch logs for debugging (admin only).

#### **Query:**
```graphql
query GetNotificationLogs(
  $page: Int = 1
  $pageSize: Int = 20
  $notificationType: String
) {
  notificationLogs(
    page: $page
    pageSize: $pageSize
    notificationType: $notificationType
  ) {
    id
    notificationType
    recipientCount
    successfulCount
    failedCount
    status
    metadata
    errorMessage
    createdAt
  }
}
```

---

## ✏️ **Mutations**

### **1. markNotificationAsRead - Mark Single as Read**

Mark a single notification as read.

#### **Mutation:**
```graphql
mutation MarkNotificationAsRead($notificationId: Int!) {
  markNotificationAsRead(notificationId: $notificationId) {
    success
    message
    notification {
      id
      isRead
      readAt
      status
    }
  }
}
```

#### **Variables:**
```json
{
  "notificationId": 123
}
```

#### **Response:**
```json
{
  "data": {
    "markNotificationAsRead": {
      "success": true,
      "message": "Notification marked as read",
      "notification": {
        "id": 123,
        "isRead": true,
        "readAt": "2025-11-20T15:45:00Z",
        "status": "read"
      }
    }
  }
}
```

---

### **2. markAllNotificationsAsRead - Mark All as Read**

Mark all unread notifications as read for the current user.

#### **Mutation:**
```graphql
mutation MarkAllNotificationsAsRead {
  markAllNotificationsAsRead {
    success
    message
    updatedCount
  }
}
```

#### **Response:**
```json
{
  "data": {
    "markAllNotificationsAsRead": {
      "success": true,
      "message": "Marked 12 notifications as read",
      "updatedCount": 12
    }
  }
}
```

---

### **3. deleteNotification - Delete Single Notification**

Delete a single notification.

#### **Mutation:**
```graphql
mutation DeleteNotification($notificationId: Int!) {
  deleteNotification(notificationId: $notificationId) {
    success
    message
  }
}
```

#### **Variables:**
```json
{
  "notificationId": 123
}
```

#### **Response:**
```json
{
  "data": {
    "deleteNotification": {
      "success": true,
      "message": "Notification deleted successfully"
    }
  }
}
```

---

### **4. deleteAllNotifications - Delete All Notifications**

Delete all notifications for the current user.

#### **Mutation:**
```graphql
mutation DeleteAllNotifications($isReadOnly: Boolean = false) {
  deleteAllNotifications(isReadOnly: $isReadOnly) {
    success
    message
    deletedCount
  }
}
```

#### **Variables:**
```json
{
  "isReadOnly": true
}
```

#### **Response:**
```json
{
  "data": {
    "deleteAllNotifications": {
      "success": true,
      "message": "Deleted 33 notifications",
      "deletedCount": 33
    }
  }
}
```

#### **Parameters:**
- `isReadOnly` (Boolean, default: false): If true, only delete read notifications

---

### **5. updateNotificationPreference - Update Preference**

Enable or disable a specific notification type.

#### **Mutation:**
```graphql
mutation UpdateNotificationPreference(
  $notificationType: String!
  $isEnabled: Boolean!
) {
  updateNotificationPreference(
    notificationType: $notificationType
    isEnabled: $isEnabled
  ) {
    success
    message
    preference {
      id
      notificationType
      isEnabled
      updatedAt
    }
  }
}
```

#### **Variables:**
```json
{
  "notificationType": "new_comment_on_post",
  "isEnabled": false
}
```

#### **Response:**
```json
{
  "data": {
    "updateNotificationPreference": {
      "success": true,
      "message": "Notification preference disabled for new_comment_on_post",
      "preference": {
        "id": 2,
        "notificationType": "new_comment_on_post",
        "isEnabled": false,
        "updatedAt": "2025-11-20T16:00:00Z"
      }
    }
  }
}
```

---

## 💡 **Usage Examples**

### **Example 1: Get First Page of Unread Notifications**

```graphql
query {
  myNotifications(page: 1, pageSize: 10, isRead: false) {
    notifications {
      id
      title
      body
      notificationType
      createdAt
    }
    unreadCount
    hasNext
  }
}
```

---

### **Example 2: Get All Connection-Related Notifications**

```graphql
query {
  myNotifications(
    notificationType: "new_connection_request"
    pageSize: 50
  ) {
    notifications {
      id
      title
      body
      data
      createdAt
    }
    totalCount
  }
}
```

---

### **Example 3: Mark Notification as Read and Get Updated Data**

```graphql
mutation {
  markNotificationAsRead(notificationId: 123) {
    success
    notification {
      id
      isRead
      readAt
    }
  }
}
```

---

### **Example 4: Get Notification Stats and Unread Notifications**

```graphql
query {
  notificationStats {
    totalCount
    unreadCount
  }
  
  myNotifications(isRead: false, pageSize: 5) {
    notifications {
      id
      title
      body
      createdAt
    }
  }
}
```

---

### **Example 5: Disable Specific Notification Type**

```graphql
mutation {
  updateNotificationPreference(
    notificationType: "profile_viewed"
    isEnabled: false
  ) {
    success
    message
  }
}
```

---

## 🔐 **Authentication**

All queries and mutations require authentication via JWT token.

**Headers:**
```
Authorization: JWT <your_token_here>
```

---

## 📊 **Pagination Best Practices**

### **Efficient Pagination:**

```graphql
# First page
query {
  myNotifications(page: 1, pageSize: 20) {
    notifications { id title }
    hasNext
    totalPages
  }
}

# Next page (if hasNext is true)
query {
  myNotifications(page: 2, pageSize: 20) {
    notifications { id title }
    hasNext
  }
}
```

### **Infinite Scroll:**

```javascript
// Frontend example
let currentPage = 1;
const pageSize = 20;

async function loadMore() {
  const response = await fetchNotifications(currentPage, pageSize);
  
  if (response.hasNext) {
    currentPage++;
    // Load more button or auto-load
  }
}
```

---

## 🎯 **Filtering Examples**

### **Get Only Failed Notifications:**
```graphql
query {
  myNotifications(status: "failed") {
    notifications {
      id
      title
      errorMessage
    }
  }
}
```

### **Get Read Notifications from Last Week:**
```graphql
query {
  myNotifications(isRead: true, pageSize: 100) {
    notifications {
      id
      title
      readAt
    }
  }
}
```

### **Get High Priority Unread Notifications:**
```graphql
query {
  myNotifications(isRead: false) {
    notifications {
      id
      title
      priority
      createdAt
    }
  }
}
```

---

## ⚠️ **Error Handling**

### **Common Errors:**

```json
{
  "errors": [
    {
      "message": "Authentication required",
      "path": ["myNotifications"]
    }
  ]
}
```

```json
{
  "errors": [
    {
      "message": "Notification not found or access denied",
      "path": ["notification"]
    }
  ]
}
```

```json
{
  "errors": [
    {
      "message": "Admin access required",
      "path": ["notificationLogs"]
    }
  ]
}
```

---

## 🚀 **Integration Guide**

### **Step 1: Add to Main Schema**

```python
# schema/schema.py
from notification.graphql.schema import NotificationQueries, NotificationMutations

class Query(
    NotificationQueries,
    # ... other queries
    graphene.ObjectType
):
    pass

class Mutation(
    NotificationMutations,
    # ... other mutations
    graphene.ObjectType
):
    pass

schema = graphene.Schema(query=Query, mutation=Mutation)
```

### **Step 2: Test Queries**

```bash
# Access GraphQL playground
http://localhost:8000/graphql

# Or use curl
curl -X POST http://localhost:8000/graphql \
  -H "Authorization: JWT <token>" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ myNotifications { totalCount } }"}'
```

---

## 📱 **Mobile App Integration**

### **React Native Example:**

```javascript
import { gql, useQuery, useMutation } from '@apollo/client';

const GET_NOTIFICATIONS = gql`
  query GetNotifications($page: Int!, $pageSize: Int!) {
    myNotifications(page: $page, pageSize: $pageSize) {
      notifications {
        id
        title
        body
        isRead
        createdAt
      }
      hasNext
      unreadCount
    }
  }
`;

const MARK_AS_READ = gql`
  mutation MarkAsRead($notificationId: Int!) {
    markNotificationAsRead(notificationId: $notificationId) {
      success
    }
  }
`;

function NotificationsList() {
  const { data, loading, fetchMore } = useQuery(GET_NOTIFICATIONS, {
    variables: { page: 1, pageSize: 20 }
  });
  
  const [markAsRead] = useMutation(MARK_AS_READ);
  
  const handleNotificationPress = async (id) => {
    await markAsRead({ variables: { notificationId: id } });
  };
  
  return (
    // Your UI here
  );
}
```

---

## 🧪 **Testing**

### **Test Query:**
```bash
# Get notifications
curl -X POST http://localhost:8000/graphql \
  -H "Authorization: JWT <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query { myNotifications(page: 1, pageSize: 5) { notifications { id title } totalCount } }"
  }'
```

### **Test Mutation:**
```bash
# Mark as read
curl -X POST http://localhost:8000/graphql \
  -H "Authorization: JWT <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation { markNotificationAsRead(notificationId: 123) { success message } }"
  }'
```

---

## 📚 **Additional Resources**

- **Notification Templates:** `notification/notification_templates.py`
- **Global Service:** `notification/global_service.py`
- **Models:** `notification/models.py`
- **Quick Start:** `NOTIFICATION_QUICK_START.md`

---

**Status:** ✅ **READY FOR USE**

**Version:** 1.0  
**Last Updated:** November 20, 2025
