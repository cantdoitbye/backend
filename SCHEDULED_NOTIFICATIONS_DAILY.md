# Daily Scheduled Notifications - Quick Setup

## 🚀 Quick Start

### Test the command (dry run):
```bash
python manage.py send_scheduled_notifications --dry-run
```

### Run the command manually:
```bash
python manage.py send_scheduled_notifications
```

### Set up daily cron job:
```bash
# Edit crontab
crontab -e

# Add this line to run daily at 10 AM:
0 10 * * * cd /path/to/your/project && python manage.py send_scheduled_notifications

# Or if using virtual environment:
0 10 * * * cd /path/to/your/project && /path/to/venv/bin/python manage.py send_scheduled_notifications
```

---

## 📋 What It Does

This single command sends all scheduled notifications once per day:

1. **Pending Connection Requests** - Users with requests older than 24 hours
2. **Profile Completion Reminders** - New users (last 7 days) with incomplete profiles
3. **Trending Topics** - Topics matching user interests
4. **Community Suggestions** - For users in fewer than 3 communities
5. **New User Notifications** - Notify about new users with shared interests

---

## 🧪 Testing

### Dry Run (recommended first):
```bash
python manage.py send_scheduled_notifications --dry-run
```

This shows what would be sent without actually sending notifications.

### Check the output:
```
Starting scheduled notifications...

📬 Checking for pending connection requests...
   Would send to john_doe: 3 pending requests
   Would send to jane_smith: 1 pending requests
   ✓ Sent 2 pending request reminders

👤 Checking for incomplete profiles...
   Would send profile reminder to new_user_123
   ✓ Sent 1 profile reminders

🔥 Checking for trending topics...
   Would send trending topic "AI & Machine Learning" to tech_enthusiast
   ✓ Sent 1 trending topic notifications

🏘️  Checking for community suggestions...
   Would suggest communities to solo_user
   ✓ Sent 1 community suggestions

👋 Checking for new users...
   Would notify existing_user about new user fresh_member
   ✓ Sent 1 new user notifications

✅ Scheduled notifications complete. Total sent: 6
```

---

## ⚙️ Cron Setup Examples

### Daily at 10 AM:
```bash
0 10 * * * cd /path/to/project && python manage.py send_scheduled_notifications
```

### Daily at 9 AM and 6 PM:
```bash
0 9,18 * * * cd /path/to/project && python manage.py send_scheduled_notifications
```

### Every Monday at 10 AM:
```bash
0 10 * * 1 cd /path/to/project && python manage.py send_scheduled_notifications
```

### With logging:
```bash
0 10 * * * cd /path/to/project && python manage.py send_scheduled_notifications >> /var/log/notifications.log 2>&1
```

---

## 🔧 Customization

Edit `notification/management/commands/send_scheduled_notifications.py` to:

- Change time windows (24 hours → 48 hours)
- Adjust limits (50 users → 100 users)
- Add new notification types
- Modify selection criteria

---

## 📊 Monitoring

### Check if cron is running:
```bash
# View cron logs
tail -f /var/log/cron

# Or system log
tail -f /var/log/syslog | grep CRON
```

### Check notification database:
```sql
SELECT 
    notification_type,
    COUNT(*) as count,
    MAX(created_at) as last_sent
FROM user_notification 
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY notification_type;
```

---

## 🚨 Troubleshooting

### Cron not running?
```bash
# Check cron service
sudo service cron status

# Verify your crontab
crontab -l

# Test manually first
python manage.py send_scheduled_notifications --dry-run
```

### No notifications sent?
- Check if users have `device_id` in their profiles
- Verify notification templates exist
- Run with `--dry-run` to see what would be sent
- Check Django logs for errors

### Database connection issues?
```bash
# Test database connection
python manage.py shell -c "from auth_manager.models import Users; print(Users.nodes.count())"
```

---

## ✅ Ready to Use!

1. Test with dry-run: `python manage.py send_scheduled_notifications --dry-run`
2. Run manually once: `python manage.py send_scheduled_notifications`
3. Set up cron job: `crontab -e`
4. Monitor logs and database

**That's it! Your daily notifications are ready to go.** 🎉
