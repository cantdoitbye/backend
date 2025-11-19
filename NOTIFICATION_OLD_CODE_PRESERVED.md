# Old Notification Code - Preservation Strategy

## 📋 Overview

All old notification code has been **commented out** (not deleted) to allow for easy reversion if needed. Once the new GlobalNotificationService is confirmed to be working correctly in production, the commented code can be safely removed.

---

## 🔍 Where to Find Commented Code

All old notification code is marked with clear comments:

```python
# === OLD NOTIFICATION CODE (COMMENTED - CAN BE REMOVED AFTER TESTING) ===
# [old code here]

# === NEW NOTIFICATION CODE (USING GlobalNotificationService) ===
[new code here]
```

---

## 📁 Files with Commented Old Code

### 1. **post/graphql/mutation.py**

#### CreatePost Mutation (Lines 216-229)
```python
# === OLD NOTIFICATION CODE (COMMENTED - CAN BE REMOVED AFTER TESTING) ===
# if followers:
#     notification_service = NotificationService()
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
#     try:
#         loop.run_until_complete(notification_service.notifyNewPost(...))
#     finally:
#         loop.close()
```

---

### 2. **connection/graphql/mutations.py**

#### CreateConnection (V1) Mutation (Lines 154-167)
```python
# === OLD NOTIFICATION CODE (COMMENTED - CAN BE REMOVED AFTER TESTING) ===
# receiver_profile = receiver.profile.single()
# if receiver_profile and receiver_profile.device_id:
#     notification_service = NotificationService()
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
#     try:
#         loop.run_until_complete(notification_service.notifyConnectionRequest(...))
#     finally:
#         loop.close()
```

#### UpdateConnection (V1) - Accepted (Lines 365-378)
```python
# === OLD NOTIFICATION CODE (COMMENTED - CAN BE REMOVED AFTER TESTING) ===
# sender_profile = sender.profile.single()
# if sender_profile and sender_profile.device_id:
#     notification_service = NotificationService()
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
#     try:
#         loop.run_until_complete(notification_service.notifyConnectionAccepted(...))
#     finally:
#         loop.close()
```

#### UpdateConnection (V1) - Rejected (Lines 408-421)
```python
# === OLD NOTIFICATION CODE (COMMENTED - CAN BE REMOVED AFTER TESTING) ===
# sender_profile = sender.profile.single()
# if sender_profile and sender_profile.device_id:
#     notification_service = NotificationService()
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
#     try:
#         loop.run_until_complete(notification_service.notifyConnectionRejected(...))
#     finally:
#         loop.close()
```

---

### 3. **community/graphql/mutations.py**

#### CreateCommunityPost Mutation (Lines 4050-4065)
```python
# === OLD NOTIFICATION CODE (COMMENTED - CAN BE REMOVED AFTER TESTING) ===
# if members_to_notify:
#     notification_service = NotificationService()
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
#     try:
#         loop.run_until_complete(notification_service.notifyCommunityPost(...))
#     finally:
#         loop.close()
```

---

### 4. **story/graphql/mutation.py**

#### CreateStory Mutation (Lines 148-161)
```python
# === OLD NOTIFICATION CODE (COMMENTED - CAN BE REMOVED AFTER TESTING) ===
# if followers:
#     notification_service = NotificationService()
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
#     try:
#         loop.run_until_complete(notification_service.notifyNewStory(...))
#     finally:
#         loop.close()
```

---

## 🔄 How to Revert (If Needed)

If you need to revert to old notification system:

1. **Uncomment the old code** - Remove the `#` from old code lines
2. **Comment out the new code** - Add `#` to new GlobalNotificationService code
3. **Test** - Verify old notifications work
4. **Deploy** - Push changes to production

### Example Reversion:
```python
# === OLD NOTIFICATION CODE (ACTIVE) ===
if followers:
    notification_service = NotificationService()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(notification_service.notifyNewPost(...))
    finally:
        loop.close()

# === NEW NOTIFICATION CODE (COMMENTED - HAVING ISSUES) ===
# if recipients:
#     try:
#         from notification.global_service import GlobalNotificationService
#         service = GlobalNotificationService()
#         service.send(...)
#     except Exception as e:
#         logger.error(f"Failed: {e}")
```

---

## ✅ When to Remove Old Code

Remove the commented old code once you've confirmed:

1. ✅ **Notifications working correctly** in production for at least 1-2 weeks
2. ✅ **No reported issues** from users about missing notifications
3. ✅ **Django Admin shows** notifications being sent successfully
4. ✅ **Error rates are low** (check logs and notification stats)
5. ✅ **Team agrees** old code is no longer needed

---

## 🗑️ How to Remove Old Code

Once confirmed working, use this command to find and review all commented old code:

```bash
# Find all old notification comments
grep -n "OLD NOTIFICATION CODE" post/graphql/mutation.py connection/graphql/mutations.py community/graphql/mutations.py story/graphql/mutation.py
```

Then manually remove the commented sections in each file.

---

## 📊 Summary Table

| File | Mutation | Old Code Lines | Status |
|------|----------|---------------|--------|
| `post/graphql/mutation.py` | CreatePost | 216-229 | 💬 Commented |
| `connection/graphql/mutations.py` | CreateConnection (V1) | 154-167 | 💬 Commented |
| `connection/graphql/mutations.py` | UpdateConnection (V1) - Accepted | 365-378 | 💬 Commented |
| `connection/graphql/mutations.py` | UpdateConnection (V1) - Rejected | 408-421 | 💬 Commented |
| `community/graphql/mutations.py` | CreateCommunityPost | 4050-4065 | 💬 Commented |
| `story/graphql/mutation.py` | CreateStory | 148-161 | 💬 Commented |

**Total Commented Code Blocks:** 6

---

## 🔒 Safety Features

### Why This Approach is Safe:

1. **Easy Reversion:** Just uncomment old code and comment new code
2. **Reference Available:** Can compare old vs new implementation
3. **No Data Loss:** Old logic is preserved exactly as it was
4. **Team Confidence:** Everyone can see what was replaced
5. **Audit Trail:** Clear history of what changed

### Additional Safety Measures:

- ✅ All new code wrapped in try-except blocks
- ✅ Errors logged but don't break mutations
- ✅ Device ID validation before sending
- ✅ Self-notification prevention
- ✅ Database logging of all notifications

---

## 📝 Next Steps

### Immediate:
1. ✅ Old code commented out (DONE)
2. ✅ New code active (DONE)
3. ⏳ Test in staging/development
4. ⏳ Monitor Django Admin for notifications

### Short-term (1-2 weeks):
1. ⏳ Deploy to production
2. ⏳ Monitor error rates
3. ⏳ Collect user feedback
4. ⏳ Check notification success rates

### Long-term (After confirmed working):
1. ⏳ Remove commented old code
2. ⏳ Clean up imports (remove unused NotificationService)
3. ⏳ Update documentation
4. ⏳ Archive this preservation document

---

## 🎯 Recommendation

**Keep the commented code for at least 2-4 weeks** after production deployment. This gives enough time to:
- Verify all notification types work correctly
- Catch any edge cases
- Monitor error rates
- Gather user feedback

Once you're confident the new system is stable, remove the commented code to keep the codebase clean.

---

**Status: Old code preserved as comments - Ready for safe testing and rollback if needed! ✅**


