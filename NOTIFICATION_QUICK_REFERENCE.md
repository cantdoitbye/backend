# Quick Reference: Notification Mapping

This document provides a quick lookup table mapping each notification from the HTML file to its implementation details.

## Format
| Feature | API/Mutation | Event Type | File Location | Section in Guide |

---

## App Closed Notifications

### 1. Onboarding

| Feature | API/Mutation | Event Type | File Location | Guide Section |
|---------|--------------|------------|---------------|---------------|
| Welcome (First Install) | - | `welcome_first_install` | N/A (OS level) | 1.1 |
| Login Reminder | LoginUsingUsernameEmail | `login_success` | `auth_manager/graphql/mutations.py` | 1.1 |
| Forgot Password | ForgotPassword | `password_reset_initiated` | `auth_manager/graphql/mutations.py` | 1.2 |
| SignUp Incomplete | SignUp | `incomplete_signup` | `auth_manager/graphql/mutations.py` | 12.1 |

### 2. Areas of Interest

| Feature | API/Mutation | Event Type | File Location | Guide Section |
|---------|--------------|------------|---------------|---------------|
| Interest Selection | SelectInterests | `interest_selection_reminder` | Interest mutation file | 2.1 |

### 3. Feed & Content Interactions

| Feature | API/Mutation | Event Type | File Location | Guide Section |
|---------|--------------|------------|---------------|---------------|
| New Post in Feed | CreatePost | `new_post_from_connection` | `post/graphql/mutations.py` | 3.1 |
| Post Comment | CreateComment | `new_comment_on_post` | `post/graphql/mutations.py` | 3.1 |
| Vibe Reaction | CreateLike/Vibe | `vibe_reaction_on_post` | `post/graphql/mutations.py` | 3.2 |
| Story Added | CreateStory | `new_story_from_connection` | `story/graphql/mutations.py` | 3.3 |

### 4. Profile & Connection Updates

| Feature | API/Mutation | Event Type | File Location | Guide Section |
|---------|--------------|------------|---------------|---------------|
| Profile Edit Reminder | - | `incomplete_profile` | Scheduled task | 12.2 |
| New Connection Request | SendConnectionRequest | `new_connection_request` | `connection/graphql/mutations.py` | 4.1 |
| Connection Accepted | AcceptConnectionRequest | `connection_accepted` | `connection/graphql/mutations.py` | 4.2 |
| Mutual Connection Added | - | `mutual_connection_added` | `connection/graphql/mutations.py` | - |
| Special Moments Added | AddSpecialMoment | `special_moment_added` | `profile/graphql/mutations.py` | 4.4 |
| Achievement | AddAchievement | `achievement_added` | `profile/graphql/mutations.py` | 4.5 |
| Education | AddEducation | `education_added` | `profile/graphql/mutations.py` | 4.6 |
| Experience | AddExperience | `experience_added` | `profile/graphql/mutations.py` | 4.7 |
| Skills | AddSkill | `skill_added` | `profile/graphql/mutations.py` | 4.8 |
| Notes | AddNote | `note_added` | `profile/graphql/mutations.py` | 4.9 |
| Sub-Relation Update | UpdateSubRelation | `sub_relation_updated` | `profile/graphql/mutations.py` | - |
| Profile Viewed | ViewProfile | `profile_viewed` | `profile/graphql/queries.py` | 4.3 |
| Multiple Views | - | `multiple_profile_views` | Analytics/scheduled | - |
| Vibe Sent | SendVibe | `vibe_sent_to_profile` | `vibe_manager/graphql/mutations.py` | 4.10 |
| Multiple Vibes Received | - | `multiple_vibes_received` | Analytics/scheduled | - |

### 5. Community Interactions

| Feature | API/Mutation | Event Type | File Location | Guide Section |
|---------|--------------|------------|---------------|---------------|
| New Sibling Community | CreateCommunity | `new_sibling_community` | `community/graphql/mutations.py` | 5.1 |
| New Child Community | CreateCommunity | `new_child_community` | `community/graphql/mutations.py` | 5.2 |
| Community Role Change | UpdateMemberRole | `community_role_changed` | `community/graphql/mutations.py` | 5.3 |
| New Members Joined | JoinCommunity | `new_members_joined_community` | `community/graphql/mutations.py` | 5.4 |
| Important Community Announcement | CreateAnnouncement | `community_announcement` | `community/graphql/mutations.py` | 5.5 |
| New Community Post | CreateCommunityPost | `new_community_post` | `community/graphql/mutations.py` | 5.6 |
| Post Reaction | CreateCommunityPostReaction | `community_post_reaction` | `community/graphql/mutations.py` | 5.7 |
| Comment on User's Post | CreateCommunityPostComment | `community_post_comment` | `community/graphql/mutations.py` | 5.8 |
| Mention in Community Post | CreateCommunityPost | `mentioned_in_community_post` | `community/graphql/mutations.py` | 5.9 |
| Community Event Reminder | - | `community_event_reminder` | Scheduled task | 5.10 |
| Community Goal | CreateCommunityGoal | `community_goal_created` | `community/graphql/mutations.py` | 5.11 |
| Achievement | - | `community_achievement_unlocked` | Achievement check | 5.12 |
| Affiliation | JoinCommunity | `user_joined_community` | `community/graphql/mutations.py` | 5.13 |

### 6. Story & Media Uploads

| Feature | API/Mutation | Event Type | File Location | Guide Section |
|---------|--------------|------------|---------------|---------------|
| New Story Available | CreateStory | `new_story_available` | `story/graphql/mutations.py` | 6.1 |
| Story Reaction | CreateStoryReaction | `story_reaction` | `story/graphql/mutations.py` | 6.2 |
| Story Mention | CreateStory | `story_mention` | `story/graphql/mutations.py` | 6.3 |
| Story Expiring Soon | - | `story_expiring_soon` | Scheduled task | 6.4 |

### 7. Notifications & Requests

| Feature | API/Mutation | Event Type | File Location | Guide Section |
|---------|--------------|------------|---------------|---------------|
| Pending Requests | - | `pending_connection_requests` | Scheduled task | 7.1 |
| Community Invite | InviteToCommunity | `community_invite` | `community/graphql/mutations.py` | 7.2 |
| Request Accepted | ApproveJoinRequest | `community_request_accepted` | `community/graphql/mutations.py` | 7.3 |
| Event Invitation | InviteToEvent | `event_invitation` | Events mutation file | 7.4 |

### 8. Chat & Messaging

| Feature | API/Mutation | Event Type | File Location | Guide Section |
|---------|--------------|------------|---------------|---------------|
| New Message | SendMessage | `new_message` | `msg/graphql/mutations.py` | 8.1 |
| Unread Messages | - | `unread_messages` | Scheduled task | 8.2 |
| Group Chat Mention | SendGroupMessage | `group_chat_mention` | `msg/graphql/mutations.py` | 8.3 |
| New Group Chat Created | CreateGroupChat | `new_group_chat_created` | `msg/graphql/mutations.py` | 8.4 |

### 9. Search & Discovery

| Feature | API/Mutation | Event Type | File Location | Guide Section |
|---------|--------------|------------|---------------|---------------|
| Trending Topics | - | `trending_topic_matching_interest` | Recommendation engine | 9.1 |
| New Arrival in Network | - | `new_user_in_network` | After signup | 9.2 |
| Suggested Community | - | `suggested_community` | Recommendation engine | 9.3 |

### 10. Menu & Privacy Settings

| Feature | API/Mutation | Event Type | File Location | Guide Section |
|---------|--------------|------------|---------------|---------------|
| Privacy Update Reminder | - | `privacy_settings_reminder` | Scheduled task | 10.1 |
| Profile Visibility Change | UpdatePrivacySettings | `profile_visibility_changed` | `auth_manager/graphql/mutations.py` | 10.2 |
| Account Security Alert | - | `account_security_alert` | Security monitoring | 10.3 |
| New Feature in Settings | - | `new_feature_available` | Admin trigger | 10.4 |

---

## App Open Notifications (In-App)

### 1. Onboarding

| Feature | Event Type | File Location | Notes |
|---------|------------|---------------|-------|
| Splash Screen | `welcome_splash` | N/A | First time only |
| Login Success | `login_success` | `auth_manager/graphql/mutations.py` | Show feed |
| Forgot Password | `password_reset_success` | `auth_manager/graphql/mutations.py` | After reset |
| Sign Up Complete | `signup_complete` | `auth_manager/graphql/mutations.py` | Show tooltips |

### 2. Areas of Interest

| Feature | Event Type | File Location | Notes |
|---------|------------|---------------|-------|
| Interest Selection | `interest_selection_prompt` | Interest mutation | In-app prompt |

### 3-10. Other Sections
All other in-app notifications follow the same pattern as push notifications, but are delivered through the app's notification center/UI.

---

## Incomplete Process Notifications

| Feature | Event Type | Trigger | File Location |
|---------|------------|---------|---------------|
| Incomplete Splash Screen | `incomplete_onboarding` | User skips intro | Scheduled task |
| Incomplete Login | `login_reminder` | No login after signup | Scheduled task |
| Incomplete Password Reset | `password_reset_pending` | Started but not completed | Scheduled task |
| Incomplete Sign-Up | `incomplete_signup` | Form not submitted | Scheduled task |
| No Interests Selected | `interest_selection_reminder` | No interests after X days | Scheduled task |
| No Connections | `no_connections_yet` | No connections after signup | Scheduled task |
| No Posts | `first_post_encouragement` | No posts created | Scheduled task |
| No Story Uploaded | `first_story_encouragement` | No story created | Scheduled task |
| No Community Joined | `join_community_reminder` | No communities joined | Scheduled task |
| Incomplete Profile | `incomplete_profile` | Profile < 50% complete | Scheduled task |
| Incomplete Achievement | `incomplete_achievement` | Started but not added | Form state |
| Incomplete Education | `incomplete_education` | Started but not added | Form state |
| Incomplete Experience | `incomplete_experience` | Started but not added | Form state |
| Incomplete Skills | `incomplete_skills` | Started but not saved | Form state |
| Incomplete Notes | `incomplete_notes` | Draft not saved | Form state |
| Incomplete Goal | `community_goal_incomplete` | Not contributed | Scheduled task |
| Pending Approval | `community_request_pending` | Request awaiting approval | Status check |
| Missed Achievement | `achievement_almost_complete` | Close to unlocking | Progress check |
| Incomplete Registration | `community_registration_incomplete` | Started form | Form state |

---

## Version Update Notifications

| Feature | Event Type | Trigger | Priority |
|---------|------------|---------|----------|
| New Version Available | `new_app_version_available` | Version check | Normal |
| Mandatory Update | `mandatory_update_required` | Old version | Urgent |
| Security Update | `security_update_available` | Critical patch | High |
| New Features Added | `new_features_available` | Feature release | Normal |

---

## Implementation Priority

### High Priority (Implement First)
1. ✅ Login/Signup notifications
2. ✅ New comment on post
3. ✅ New message
4. ✅ Connection request
5. ✅ Connection accepted
6. ✅ Community post
7. ✅ Story from connection
8. ✅ Vibe/reaction on post

### Medium Priority
1. Community announcements
2. Event reminders
3. Profile viewed
4. Group chat mention
5. Story reactions
6. Community role change

### Low Priority
1. Trending topics
2. Suggested communities
3. Privacy reminders
4. Incomplete process reminders
5. Version updates

---

## Code Template for Each Notification

```python
# 1. Import at top of file
from notification.global_service import GlobalNotificationService

# 2. Inside mutation's mutate() method, after successful operation
try:
    # Check if recipient has device_id
    if recipient.device_id and recipient.uid != sender.uid:
        service = GlobalNotificationService()
        service.send(
            event_type="notification_event_type_here",
            recipients=[{
                'device_id': recipient.device_id,
                'uid': recipient.uid
            }],
            # Add template variables
            username=sender.username,
            other_var="value"
        )
except Exception as e:
    # Log but don't fail mutation
    logger.error(f"Notification error: {e}")
```

---

## Batch Notification Template

```python
# For notifying multiple users (e.g., community members)
from notification.global_service import GlobalNotificationService

try:
    # Collect all recipients
    recipients = []
    for member in members:
        if member.device_id:
            recipients.append({
                'device_id': member.device_id,
                'uid': member.uid
            })
    
    # Send to all at once
    if recipients:
        service = GlobalNotificationService()
        service.send(
            event_type="notification_event_type_here",
            recipients=recipients,
            # Template variables
            username=actor.username,
            other_var="value"
        )
except Exception as e:
    logger.error(f"Notification error: {e}")
```

---

## Checking Notification Status

### Django Admin
- URL: `/admin/notification/usernotification/`
- View all sent notifications
- Filter by user, type, status
- See timestamps and data

### Management Command
```bash
python manage.py notification_stats
```

### Programmatically
```python
from notification.models import UserNotification

# Get user's notifications
notifications = UserNotification.objects.filter(
    user_uid=user.uid,
    is_read=False
).order_by('-created_at')

# Mark as read
notification.is_read = True
notification.read_at = timezone.now()
notification.save()

# Get unread count
unread_count = UserNotification.objects.filter(
    user_uid=user.uid,
    is_read=False
).count()
```

---

## Summary

This quick reference provides:
- ✅ Complete mapping of all ~80 notifications
- ✅ Event type for each notification
- ✅ File location for implementation
- ✅ Section reference in main guide
- ✅ Implementation priority
- ✅ Code templates for quick copy-paste

Use this document to quickly find which notification to implement and where!
