# 🔄 Migration Guide: Adding deep_link and web_link Fields

## 📋 **Overview**

Added `deep_link` and `web_link` as separate database fields in the `UserNotification` model for better accessibility in GraphQL queries.

---

## ✅ **Changes Made**

### **1. Database Model Updated**
**File:** `notification/models.py`

**Added Fields:**
```python
deep_link = models.CharField(
    max_length=500, 
    null=True, 
    blank=True, 
    help_text='Deep link for mobile app (e.g., ooumph://post/123)'
)
web_link = models.URLField(
    max_length=500, 
    null=True, 
    blank=True, 
    help_text='Web link for browser (e.g., https://app.ooumph.com/post/123)'
)
```

---

### **2. GlobalNotificationService Updated**
**File:** `notification/global_service.py`

**Updated to store deep_link and web_link:**
```python
notification = UserNotification.objects.create(
    # ... other fields
    deep_link=notification_data.get('deep_link'),
    web_link=notification_data.get('web_link'),
    # ... other fields
)
```

---

### **3. GraphQL Type Updated**
**File:** `notification/graphql/types.py`

**Added to UserNotificationType:**
```python
fields = (
    # ... other fields
    'deep_link',
    'web_link',
    # ... other fields
)
```

---

### **4. Migration Created**
**File:** `notification/migrations/0002_add_deep_link_web_link.py`

---

## 🚀 **How to Apply Migration**

### **Step 1: Run Migration**

#### **Using Docker:**
```bash
docker-compose exec web python manage.py migrate notification
```

#### **Using Local Python:**
```bash
python manage.py migrate notification
```

---

### **Step 2: Verify Migration**

```bash
# Check migration status
docker-compose exec web python manage.py showmigrations notification

# Should show:
# notification
#  [X] 0001_initial
#  [X] 0002_add_deep_link_web_link
```

---

### **Step 3: Restart Server**

```bash
docker-compose restart web
```

---

## 🧪 **Testing**

### **Test 1: Check Database Schema**

```bash
docker-compose exec db psql -U your_db_user -d your_db_name

# In psql:
\d notification_usernotification

# Should show deep_link and web_link columns
```

---

### **Test 2: Test GraphQL Query**

```graphql
query {
  myNotifications(page: 1, pageSize: 5) {
    notifications {
      id
      title
      body
      clickAction
      deepLink
      webLink
      data
    }
  }
}
```

**Expected Response:**
```json
{
  "data": {
    "myNotifications": {
      "notifications": [
        {
          "id": 123,
          "title": "John Doe just posted something new!",
          "body": "Check it out.",
          "clickAction": "/post/456",
          "deepLink": "ooumph://post/456",
          "webLink": "https://app.ooumph.com/post/456",
          "data": {
            "post_id": "456",
            "username": "John Doe"
          }
        }
      ]
    }
  }
}
```

---

### **Test 3: Create New Notification**

```python
# Test in Django shell
docker-compose exec web python manage.py shell

from notification.global_service import GlobalNotificationService

service = GlobalNotificationService()
service.send(
    event_type="new_post_from_connection",
    recipients=[{
        'device_id': 'test_device_id',
        'uid': 'test_user_uid'
    }],
    username="Test User",
    post_id="test_post_123"
)

# Check database
from notification.models import UserNotification
notif = UserNotification.objects.latest('created_at')
print(f"Deep Link: {notif.deep_link}")
print(f"Web Link: {notif.web_link}")
```

---

## 📊 **Data Migration (Optional)**

If you have existing notifications and want to populate deep_link and web_link from the data field:

### **Create Data Migration Script:**

```python
# notification/migrations/0003_populate_deep_web_links.py

from django.db import migrations
import json


def populate_links(apps, schema_editor):
    """
    Populate deep_link and web_link from data field for existing notifications
    """
    UserNotification = apps.get_model('notification', 'UserNotification')
    
    updated_count = 0
    for notification in UserNotification.objects.all():
        data = notification.data or {}
        
        # Extract deep_link and web_link from data if they exist
        deep_link = data.get('deep_link')
        web_link = data.get('web_link')
        
        if deep_link or web_link:
            notification.deep_link = deep_link
            notification.web_link = web_link
            notification.save(update_fields=['deep_link', 'web_link'])
            updated_count += 1
    
    print(f"Updated {updated_count} notifications with deep_link/web_link")


def reverse_populate(apps, schema_editor):
    """
    Reverse migration - move links back to data field
    """
    UserNotification = apps.get_model('notification', 'UserNotification')
    
    for notification in UserNotification.objects.all():
        if notification.deep_link or notification.web_link:
            data = notification.data or {}
            if notification.deep_link:
                data['deep_link'] = notification.deep_link
            if notification.web_link:
                data['web_link'] = notification.web_link
            notification.data = data
            notification.save(update_fields=['data'])


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0002_add_deep_link_web_link'),
    ]

    operations = [
        migrations.RunPython(populate_links, reverse_populate),
    ]
```

**Run it:**
```bash
docker-compose exec web python manage.py migrate notification
```

---

## 🔍 **Verification Queries**

### **Check Existing Notifications:**

```sql
-- Check if deep_link and web_link are populated
SELECT 
    id,
    notification_type,
    click_action,
    deep_link,
    web_link,
    created_at
FROM notification_usernotification
ORDER BY created_at DESC
LIMIT 10;
```

### **Count Notifications with Links:**

```sql
SELECT 
    COUNT(*) as total,
    COUNT(deep_link) as with_deep_link,
    COUNT(web_link) as with_web_link
FROM notification_usernotification;
```

---

## 📱 **Mobile App Integration**

Now your mobile app can directly access deep_link:

```javascript
// React Native example
const { data } = useQuery(GET_NOTIFICATIONS);

data.myNotifications.notifications.map(notification => (
  <TouchableOpacity 
    onPress={() => {
      // Use deep_link directly!
      Linking.openURL(notification.deepLink);
    }}
  >
    <Text>{notification.title}</Text>
  </TouchableOpacity>
));
```

---

## 🌐 **Web App Integration**

Web app can use web_link:

```javascript
// React example
const { data } = useQuery(GET_NOTIFICATIONS);

data.myNotifications.notifications.map(notification => (
  <a href={notification.webLink}>
    {notification.title}
  </a>
));
```

---

## ⚠️ **Important Notes**

### **Backward Compatibility**
- Old notifications without deep_link/web_link will have `null` values
- The `data` field still contains all information as backup
- No breaking changes to existing code

### **New Notifications**
- All new notifications will automatically have deep_link and web_link populated
- GlobalNotificationService handles this automatically
- No code changes needed in mutations

---

## 🐛 **Troubleshooting**

### **Issue 1: Migration Fails**

**Error:**
```
django.db.utils.ProgrammingError: column "deep_link" already exists
```

**Solution:**
```bash
# Check current migrations
docker-compose exec web python manage.py showmigrations notification

# If 0002 is already applied, skip it
docker-compose exec web python manage.py migrate notification --fake 0002
```

---

### **Issue 2: Fields Not Showing in GraphQL**

**Solution:**
1. Restart server: `docker-compose restart web`
2. Refresh Postman schema
3. Clear GraphQL cache

---

### **Issue 3: Null Values in Existing Notifications**

**Solution:**
Run the data migration script (0003_populate_deep_web_links.py) to populate from existing data field.

---

## ✅ **Verification Checklist**

- [ ] Migration applied successfully
- [ ] Database columns exist (deep_link, web_link)
- [ ] GraphQL query returns deep_link and web_link
- [ ] New notifications have deep_link and web_link populated
- [ ] Mobile app can access deep_link
- [ ] Web app can access web_link
- [ ] Server restarted
- [ ] Postman schema refreshed

---

## 🎯 **Summary**

**Before:**
```json
{
  "clickAction": "/post/123",
  "data": {
    "deep_link": "ooumph://post/123",
    "web_link": "https://app.ooumph.com/post/123"
  }
}
```

**After:**
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

**Benefits:**
✅ Direct access to deep_link and web_link  
✅ No need to parse data JSON field  
✅ Better type safety in GraphQL  
✅ Cleaner mobile/web app integration  
✅ Backward compatible  

---

**Status:** ✅ **READY TO MIGRATE**

**Run:**
```bash
docker-compose exec web python manage.py migrate notification
docker-compose restart web
```

Then test in Postman! 🚀
