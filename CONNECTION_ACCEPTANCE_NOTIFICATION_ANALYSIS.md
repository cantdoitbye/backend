# Connection Acceptance Notification Analysis

## Summary
✅ **Notifications ARE being sent when a connection is accepted**

The notification is correctly sent to the user who sent the connection request (the sender), notifying them that their request has been accepted.

---

## Current Implementation

### Location
File: `connection/graphql/mutations.py`
Mutation: `UpdateConnection` (lines ~310-380)

### When Notification is Sent
When `input.connection_status == 'Accepted'`, the system:

1. **Updates connection statistics** (circle counts)
2. **Updates Matrix relations** (for chat functionality)
3. **Sends notification to the sender** ✅

### Notification Code (Lines 360-380)

```python
# === NEW NOTIFICATION CODE (USING GlobalNotificationService) ===
try:
    from notification.global_service import GlobalNotificationService
    
    sender_profile = sender.profile.single()
    if sender_profile and sender_profile.device_id:
        service = GlobalNotificationService()
        service.send(
            event_type="connection_accepted",
            recipients=[{
                'device_id': sender_profile.device_id,
                'uid': sender.uid
            }],
            username=receiver_node.username,
            accepter_id=receiver_node.uid,
            connection_id=connection.uid
        )
except Exception as e:
    print(f"Failed to send connection accepted notification: {e}")
```

---

## Notification Details

### Template Used
Event Type: `"connection_accepted"`

From `notification/notification_templates.py`:

```python
"connection_accepted": {
    "title": "{username} accepted your connection request!",
    "body": "Start a conversation now.",
    "click_action": "/profile/{user_id}",
    "deep_link": "ooumph://profile/{user_id}",
    "web_link": "https://app.ooumph.com/profile/{user_id}",
    "priority": "high"
}
```

### Recipient
- **Who receives it**: The user who SENT the connection request (sender)
- **Who does NOT receive it**: The user who accepted the request (receiver)

### Variables Passed
- `username`: The username of the person who accepted (receiver_node.username)
- `accepter_id`: The UID of the person who accepted (receiver_node.uid)
- `connection_id`: The connection UID

### Notification Content
- **Title**: "{username} accepted your connection request!"
- **Body**: "Start a conversation now."
- **Priority**: High
- **Deep Link**: Opens the accepter's profile
- **Web Link**: Opens the accepter's profile on web

---

## How It Works

### Flow Diagram
```
User A sends connection request to User B
                ↓
User B accepts the connection
                ↓
UpdateConnection mutation is called
                ↓
Connection status updated to "Accepted"
                ↓
Circle counts updated
                ↓
Matrix relations updated
                ↓
Notification sent to User A (sender) ✅
                ↓
User A receives: "User B accepted your connection request!"
```

### Background Processing
The notification is sent in a **background thread** (non-blocking):
- The mutation returns immediately
- Notification is sent asynchronously via `GlobalNotificationService`
- Uses Firebase Cloud Messaging (FCM) to deliver push notifications
- Retries up to 3 times if delivery fails
- Logs all notification attempts in PostgreSQL

---

## Verification Checklist

To verify notifications are working:

1. ✅ **Code exists**: Notification code is present in UpdateConnection mutation
2. ✅ **Template exists**: "connection_accepted" template is defined
3. ✅ **Service exists**: GlobalNotificationService is implemented
4. ✅ **Recipient check**: Sender's device_id is checked before sending
5. ✅ **Error handling**: Try-catch block prevents mutation failure if notification fails

### What Could Prevent Notifications

1. **Missing device_id**: If sender doesn't have a device_id in their profile
2. **Invalid device_id**: If the FCM token is expired or invalid
3. **Service URL issue**: If NOTIFICATION_SERVICE_URL is not configured
4. **Network issues**: If the notification service is unreachable

---

## Testing the Notification

### Manual Test Steps

1. **User A** sends connection request to **User B**
2. **User B** accepts the connection via GraphQL mutation:
   ```graphql
   mutation {
     updateConnection(input: {
       uid: "connection_uid_here"
       connectionStatus: Accepted
     }) {
       success
       message
       connection {
         uid
         connectionStatus
       }
     }
   }
   ```
3. **User A** should receive push notification:
   - Title: "User B accepted your connection request!"
   - Body: "Start a conversation now."

### Check Logs

Look for these log messages:
```
🚀 Notification thread started for connection_accepted
📨 Sending connection_accepted notification to 1 recipients
📋 Title: 'User B accepted your connection request!'
📋 Body: 'Start a conversation now.'
✅ Sent to user_uid - FCM Response: {...}
```

### Database Verification

Check `UserNotification` table in PostgreSQL:
```sql
SELECT * FROM notification_usernotification 
WHERE notification_type = 'connection_accepted' 
ORDER BY created_at DESC 
LIMIT 10;
```

---

## Additional Notes

### V2 Implementation
There's also a `UpdateConnectionV2` mutation that uses the same notification logic for the newer connection system (ConnectionV2 with CircleV2).

### Old Code
The old notification code using `NotificationService` is commented out but preserved for reference. It can be safely removed after confirming the new system works.

### Related Notifications
- `new_connection_request`: Sent when connection request is created
- `connection_rejected`: Sent when connection request is rejected

---

## Conclusion

✅ **The notification system is properly implemented and should be working.**

The notification is sent to the correct recipient (the person who sent the request) when their connection request is accepted. If notifications are not being received, the issue is likely:

1. Device token (device_id) not registered or expired
2. Notification service configuration issue
3. FCM service connectivity issue

Check the application logs and database records to diagnose any delivery issues.
