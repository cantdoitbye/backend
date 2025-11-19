# Notification Integration Guide for Ooumph App

This guide provides the exact code you need to add to each mutation/query file to implement all notifications from the Ooumph_App_Notifications.html file.

## Table of Contents
1. [Onboarding Notifications](#1-onboarding-notifications)
2. [Areas of Interest Notifications](#2-areas-of-interest-notifications)
3. [Feed & Content Interactions](#3-feed--content-interactions)
4. [Profile & Connection Updates](#4-profile--connection-updates)
5. [Community Interactions](#5-community-interactions)
6. [Story & Media Uploads](#6-story--media-uploads)
7. [Notifications & Requests](#7-notifications--requests)
8. [Chat & Messaging](#8-chat--messaging)
9. [Search & Discovery](#9-search--discovery)
10. [Menu & Privacy Settings](#10-menu--privacy-settings)

---

## How to Use This Guide

For each mutation, you'll find:
- **Location**: The file path where the code should be added
- **Event Type**: The notification template key
- **Code Snippet**: Exact code to add
- **Placement**: Where in the mutation to add the code

### Basic Pattern

```python
from notification.global_service import GlobalNotificationService

# Inside your mutation's mutate method:
service = GlobalNotificationService()
service.send(
    event_type="notification_event_type",
    recipients=[{'device_id': '...', 'uid': '...'}],
    # Template variables
    username="...",
    other_var="..."
)
```

---

## 1. Onboarding Notifications

### 1.1 Login Success Notification
**File**: `auth_manager/graphql/mutations.py` (LoginUsingUsernameEmail mutation)
**Event Type**: `login_success`

```python
# After successful login, before returning the response
from notification.global_service import GlobalNotificationService

if user.device_id:
    service = GlobalNotificationService()
    service.send(
        event_type="login_success",
        recipients=[{
            'device_id': user.device_id,
            'uid': user.uid
        }],
        username=user.username
    )
```

### 1.2 Password Reset Notification
**File**: `auth_manager/graphql/mutations.py` (ForgotPassword mutation)
**Event Type**: `password_reset_initiated`

```python
# After sending reset email
from notification.global_service import GlobalNotificationService

if user.device_id:
    service = GlobalNotificationService()
    service.send(
        event_type="password_reset_initiated",
        recipients=[{
            'device_id': user.device_id,
            'uid': user.uid
        }],
        username=user.username
    )
```

### 1.3 Signup Complete Notification
**File**: `auth_manager/graphql/mutations.py` (SignUp mutation)
**Event Type**: `signup_complete`

```python
# After successful signup
from notification.global_service import GlobalNotificationService

if user.device_id:
    service = GlobalNotificationService()
    service.send(
        event_type="signup_complete",
        recipients=[{
            'device_id': user.device_id,
            'uid': user.uid
        }],
        username=user.username
    )
```

---

## 2. Areas of Interest Notifications

### 2.1 Interest Selection Reminder
**File**: `auth_manager/graphql/mutations.py` or separate interest mutation
**Event Type**: `interest_selection_reminder`

```python
# After user hasn't selected interests (check in a scheduled task or after login)
from notification.global_service import GlobalNotificationService

if user.device_id and not user.has_selected_interests:
    service = GlobalNotificationService()
    service.send(
        event_type="interest_selection_reminder",
        recipients=[{
            'device_id': user.device_id,
            'uid': user.uid
        }],
        username=user.username
    )
```

---

## 3. Feed & Content Interactions

### 3.1 New Post Comment Notification
**File**: `post/graphql/mutations.py` (CreateComment mutation)
**Event Type**: `new_comment_on_post`

```python
# After creating comment successfully
from notification.global_service import GlobalNotificationService

# Get post creator
post_creator = post.creator.get()

if post_creator.device_id and post_creator.uid != commenter.uid:
    service = GlobalNotificationService()
    service.send(
        event_type="new_comment_on_post",
        recipients=[{
            'device_id': post_creator.device_id,
            'uid': post_creator.uid
        }],
        username=commenter.username,
        comment_text=comment.text[:100],
        post_id=post.uid,
        comment_id=comment.uid
    )
```

### 3.2 Vibe Reaction on Post
**File**: `post/graphql/mutations.py` (CreateLike or Vibe mutation)
**Event Type**: `vibe_reaction_on_post`

```python
# After creating vibe/like
from notification.global_service import GlobalNotificationService

# Get post creator
post_creator = post.creator.get()

if post_creator.device_id and post_creator.uid != user.uid:
    service = GlobalNotificationService()
    service.send(
        event_type="vibe_reaction_on_post",
        recipients=[{
            'device_id': post_creator.device_id,
            'uid': post_creator.uid
        }],
        username=user.username,
        post_id=post.uid,
        vibe_type=vibe.vibe_type  # or like type
    )
```

### 3.3 New Story from Connection
**File**: `story/graphql/mutations.py` (CreateStory mutation)
**Event Type**: `new_story_from_connection`

```python
# After creating story successfully
from notification.global_service import GlobalNotificationService

# Get all connections
connections = user.connections.all()
recipients = []

for connection in connections:
    if connection.device_id:
        recipients.append({
            'device_id': connection.device_id,
            'uid': connection.uid
        })

if recipients:
    service = GlobalNotificationService()
    service.send(
        event_type="new_story_from_connection",
        recipients=recipients,
        username=user.username,
        story_id=story.uid
    )
```

---

## 4. Profile & Connection Updates

### 4.1 New Connection Request
**File**: `connection/graphql/mutations.py` (SendConnectionRequest mutation)
**Event Type**: `new_connection_request`

```python
# After sending connection request
from notification.global_service import GlobalNotificationService

if receiver.device_id:
    service = GlobalNotificationService()
    service.send(
        event_type="new_connection_request",
        recipients=[{
            'device_id': receiver.device_id,
            'uid': receiver.uid
        }],
        username=sender.username,
        connection_id=connection.uid,
        sender_id=sender.uid
    )
```

### 4.2 Connection Request Accepted
**File**: `connection/graphql/mutations.py` (AcceptConnectionRequest mutation)
**Event Type**: `connection_accepted`

```python
# After accepting connection request
from notification.global_service import GlobalNotificationService

# Notify the sender that their request was accepted
if sender.device_id:
    service = GlobalNotificationService()
    service.send(
        event_type="connection_accepted",
        recipients=[{
            'device_id': sender.device_id,
            'uid': sender.uid
        }],
        username=accepter.username,
        connection_id=connection.uid
    )
```

### 4.3 Profile Viewed
**File**: `profile/graphql/queries.py` or mutations (ViewProfile mutation)
**Event Type**: `profile_viewed`

```python
# After viewing a profile
from notification.global_service import GlobalNotificationService

# Track the view
if profile_owner.device_id and viewer.uid != profile_owner.uid:
    service = GlobalNotificationService()
    service.send(
        event_type="profile_viewed",
        recipients=[{
            'device_id': profile_owner.device_id,
            'uid': profile_owner.uid
        }],
        username=viewer.username,
        viewer_id=viewer.uid
    )
```

### 4.4 Special Moment Added
**File**: `profile/graphql/mutations.py` (AddSpecialMoment mutation)
**Event Type**: `special_moment_added`

```python
# After adding special moment
from notification.global_service import GlobalNotificationService

if user.device_id:
    service = GlobalNotificationService()
    service.send(
        event_type="special_moment_added",
        recipients=[{
            'device_id': user.device_id,
            'uid': user.uid
        }],
        username=user.username,
        moment_name=moment.name,
        moment_id=moment.uid
    )
```

### 4.5 Achievement Added
**File**: `profile/graphql/mutations.py` (AddAchievement mutation)
**Event Type**: `achievement_added`

```python
# After adding achievement
from notification.global_service import GlobalNotificationService

if user.device_id:
    service = GlobalNotificationService()
    service.send(
        event_type="achievement_added",
        recipients=[{
            'device_id': user.device_id,
            'uid': user.uid
        }],
        username=user.username,
        achievement_name=achievement.name,
        achievement_id=achievement.uid
    )
```

### 4.6 Education Added/Updated
**File**: `profile/graphql/mutations.py` (AddEducation mutation)
**Event Type**: `education_added`

```python
# After adding/updating education
from notification.global_service import GlobalNotificationService

if user.device_id:
    service = GlobalNotificationService()
    service.send(
        event_type="education_added",
        recipients=[{
            'device_id': user.device_id,
            'uid': user.uid
        }],
        username=user.username,
        degree_name=education.degree,
        institution_name=education.institution,
        education_id=education.uid
    )
```

### 4.7 Experience Added/Updated
**File**: `profile/graphql/mutations.py` (AddExperience mutation)
**Event Type**: `experience_added`

```python
# After adding/updating experience
from notification.global_service import GlobalNotificationService

if user.device_id:
    service = GlobalNotificationService()
    service.send(
        event_type="experience_added",
        recipients=[{
            'device_id': user.device_id,
            'uid': user.uid
        }],
        username=user.username,
        job_title=experience.job_title,
        company_name=experience.company_name,
        experience_id=experience.uid
    )
```

### 4.8 Skill Added
**File**: `profile/graphql/mutations.py` (AddSkill mutation)
**Event Type**: `skill_added`

```python
# After adding skill
from notification.global_service import GlobalNotificationService

if user.device_id:
    service = GlobalNotificationService()
    service.send(
        event_type="skill_added",
        recipients=[{
            'device_id': user.device_id,
            'uid': user.uid
        }],
        username=user.username,
        skill_name=skill.name,
        skill_id=skill.uid
    )
```

### 4.9 Note Added
**File**: `profile/graphql/mutations.py` (AddNote mutation)
**Event Type**: `note_added`

```python
# After adding note
from notification.global_service import GlobalNotificationService

if user.device_id:
    service = GlobalNotificationService()
    service.send(
        event_type="note_added",
        recipients=[{
            'device_id': user.device_id,
            'uid': user.uid
        }],
        username=user.username,
        note_title=note.title,
        note_id=note.uid
    )
```

### 4.10 Vibe Sent to Profile
**File**: `vibe_manager/graphql/mutations.py` (SendVibe mutation)
**Event Type**: `vibe_sent_to_profile`

```python
# After sending vibe to profile
from notification.global_service import GlobalNotificationService

if receiver.device_id and sender.uid != receiver.uid:
    service = GlobalNotificationService()
    service.send(
        event_type="vibe_sent_to_profile",
        recipients=[{
            'device_id': receiver.device_id,
            'uid': receiver.uid
        }],
        username=sender.username,
        vibe_type=vibe.vibe_type,
        vibe_id=vibe.uid
    )
```

---

## 5. Community Interactions

### 5.1 New Sibling Community
**File**: `community/graphql/mutations.py` (CreateCommunity mutation - sibling type)
**Event Type**: `new_sibling_community`

```python
# After creating sibling community
from notification.global_service import GlobalNotificationService

# Get parent community members
parent_members = parent_community.members.all()
recipients = []

for member in parent_members:
    if member.device_id:
        recipients.append({
            'device_id': member.device_id,
            'uid': member.uid
        })

if recipients:
    service = GlobalNotificationService()
    service.send(
        event_type="new_sibling_community",
        recipients=recipients,
        community_name=new_community.name,
        community_id=new_community.uid,
        parent_community_name=parent_community.name
    )
```

### 5.2 New Child Community
**File**: `community/graphql/mutations.py` (CreateCommunity mutation - child type)
**Event Type**: `new_child_community`

```python
# After creating child community
from notification.global_service import GlobalNotificationService

# Get parent community members
parent_members = parent_community.members.all()
recipients = []

for member in parent_members:
    if member.device_id:
        recipients.append({
            'device_id': member.device_id,
            'uid': member.uid
        })

if recipients:
    service = GlobalNotificationService()
    service.send(
        event_type="new_child_community",
        recipients=recipients,
        community_name=new_community.name,
        community_id=new_community.uid,
        parent_community_name=parent_community.name
    )
```

### 5.3 Community Role Changed
**File**: `community/graphql/mutations.py` (UpdateMemberRole mutation)
**Event Type**: `community_role_changed`

```python
# After changing member role
from notification.global_service import GlobalNotificationService

if member.device_id:
    service = GlobalNotificationService()
    service.send(
        event_type="community_role_changed",
        recipients=[{
            'device_id': member.device_id,
            'uid': member.uid
        }],
        community_name=community.name,
        new_role=new_role.name,
        community_id=community.uid
    )
```

### 5.4 New Members Joined Community
**File**: `community/graphql/mutations.py` (JoinCommunity mutation)
**Event Type**: `new_members_joined_community`

```python
# After member joins - notify existing members
from notification.global_service import GlobalNotificationService

# Get existing community members (excluding the new member)
existing_members = community.members.exclude(uid=new_member.uid)
recipients = []

for member in existing_members:
    if member.device_id:
        recipients.append({
            'device_id': member.device_id,
            'uid': member.uid
        })

if recipients:
    service = GlobalNotificationService()
    service.send(
        event_type="new_members_joined_community",
        recipients=recipients,
        username=new_member.username,
        community_name=community.name,
        community_id=community.uid,
        member_count=1  # or batch count if multiple joined
    )
```

### 5.5 Community Announcement
**File**: `community/graphql/mutations.py` (CreateAnnouncement mutation)
**Event Type**: `community_announcement`

```python
# After creating announcement
from notification.global_service import GlobalNotificationService

# Get all community members
members = community.members.all()
recipients = []

for member in members:
    if member.device_id:
        recipients.append({
            'device_id': member.device_id,
            'uid': member.uid
        })

if recipients:
    service = GlobalNotificationService()
    service.send(
        event_type="community_announcement",
        recipients=recipients,
        community_name=community.name,
        announcement_title=announcement.title[:50],
        community_id=community.uid,
        announcement_id=announcement.uid
    )
```

### 5.6 New Community Post
**File**: `community/graphql/mutations.py` (CreateCommunityPost mutation)
**Event Type**: `new_community_post`

```python
# After creating community post
from notification.global_service import GlobalNotificationService

# Get community members (excluding post creator)
members = community.members.exclude(uid=creator.uid)
recipients = []

for member in members:
    if member.device_id:
        recipients.append({
            'device_id': member.device_id,
            'uid': member.uid
        })

if recipients:
    service = GlobalNotificationService()
    service.send(
        event_type="new_community_post",
        recipients=recipients,
        username=creator.username,
        community_name=community.name,
        post_title=post.title[:50] if post.title else "New post",
        post_id=post.uid,
        community_id=community.uid
    )
```

### 5.7 Community Post Reaction
**File**: `community/graphql/mutations.py` (CreateCommunityPostReaction mutation)
**Event Type**: `community_post_reaction`

```python
# After reacting to community post
from notification.global_service import GlobalNotificationService

# Get post creator
post_creator = post.creator.get()

if post_creator.device_id and post_creator.uid != reactor.uid:
    service = GlobalNotificationService()
    service.send(
        event_type="community_post_reaction",
        recipients=[{
            'device_id': post_creator.device_id,
            'uid': post_creator.uid
        }],
        username=reactor.username,
        community_name=community.name,
        reaction_type=reaction.type,
        post_id=post.uid,
        community_id=community.uid
    )
```

### 5.8 Community Post Comment
**File**: `community/graphql/mutations.py` (CreateCommunityPostComment mutation)
**Event Type**: `community_post_comment`

```python
# After commenting on community post
from notification.global_service import GlobalNotificationService

# Get post creator
post_creator = post.creator.get()

if post_creator.device_id and post_creator.uid != commenter.uid:
    service = GlobalNotificationService()
    service.send(
        event_type="community_post_comment",
        recipients=[{
            'device_id': post_creator.device_id,
            'uid': post_creator.uid
        }],
        username=commenter.username,
        community_name=community.name,
        comment_text=comment.text[:100],
        post_id=post.uid,
        community_id=community.uid,
        comment_id=comment.uid
    )
```

### 5.9 Mentioned in Community Post
**File**: `community/graphql/mutations.py` (CreateCommunityPost or Comment with mentions)
**Event Type**: `mentioned_in_community_post`

```python
# After creating post/comment with mentions
from notification.global_service import GlobalNotificationService

# For each mentioned user
for mentioned_user in mentioned_users:
    if mentioned_user.device_id:
        service = GlobalNotificationService()
        service.send(
            event_type="mentioned_in_community_post",
            recipients=[{
                'device_id': mentioned_user.device_id,
                'uid': mentioned_user.uid
            }],
            username=author.username,
            community_name=community.name,
            post_id=post.uid,
            community_id=community.uid
        )
```

### 5.10 Community Event Reminder
**File**: `community/graphql/mutations.py` or scheduled task
**Event Type**: `community_event_reminder`

```python
# Before event starts (scheduled task)
from notification.global_service import GlobalNotificationService

# Get event participants
participants = event.participants.all()
recipients = []

for participant in participants:
    if participant.device_id:
        recipients.append({
            'device_id': participant.device_id,
            'uid': participant.uid
        })

if recipients:
    service = GlobalNotificationService()
    service.send(
        event_type="community_event_reminder",
        recipients=recipients,
        event_name=event.name,
        community_name=community.name,
        start_time=event.start_time.strftime("%H:%M"),
        event_id=event.uid,
        community_id=community.uid
    )
```

### 5.11 Community Goal Created
**File**: `community/graphql/mutations.py` (CreateCommunityGoal mutation)
**Event Type**: `community_goal_created`

```python
# After creating community goal
from notification.global_service import GlobalNotificationService

# Get all community members
members = community.members.all()
recipients = []

for member in members:
    if member.device_id:
        recipients.append({
            'device_id': member.device_id,
            'uid': member.uid
        })

if recipients:
    service = GlobalNotificationService()
    service.send(
        event_type="community_goal_created",
        recipients=recipients,
        goal_name=goal.name,
        community_name=community.name,
        goal_id=goal.uid,
        community_id=community.uid
    )
```

### 5.12 Community Achievement Unlocked
**File**: `community/graphql/mutations.py` or achievement check
**Event Type**: `community_achievement_unlocked`

```python
# After unlocking achievement
from notification.global_service import GlobalNotificationService

# Get all community members
members = community.members.all()
recipients = []

for member in members:
    if member.device_id:
        recipients.append({
            'device_id': member.device_id,
            'uid': member.uid
        })

if recipients:
    service = GlobalNotificationService()
    service.send(
        event_type="community_achievement_unlocked",
        recipients=recipients,
        achievement_name=achievement.name,
        community_name=community.name,
        achievement_id=achievement.uid,
        community_id=community.uid
    )
```

### 5.13 User Joined Community (Affiliation)
**File**: `community/graphql/mutations.py` (JoinCommunity mutation)
**Event Type**: `user_joined_community`

```python
# After joining community - notify the user
from notification.global_service import GlobalNotificationService

if user.device_id:
    service = GlobalNotificationService()
    service.send(
        event_type="user_joined_community",
        recipients=[{
            'device_id': user.device_id,
            'uid': user.uid
        }],
        username=user.username,
        community_name=community.name,
        community_id=community.uid
    )
```

---

## 6. Story & Media Uploads

### 6.1 New Story Available
**File**: `story/graphql/mutations.py` (CreateStory mutation)
**Event Type**: `new_story_available`

```python
# After creating story
from notification.global_service import GlobalNotificationService

# Get user's connections
connections = user.connections.all()
recipients = []

for connection in connections:
    if connection.device_id:
        recipients.append({
            'device_id': connection.device_id,
            'uid': connection.uid
        })

if recipients:
    service = GlobalNotificationService()
    service.send(
        event_type="new_story_available",
        recipients=recipients,
        username=user.username,
        story_id=story.uid
    )
```

### 6.2 Story Reaction
**File**: `story/graphql/mutations.py` (CreateStoryReaction mutation)
**Event Type**: `story_reaction`

```python
# After reacting to story
from notification.global_service import GlobalNotificationService

# Get story creator
story_creator = story.creator.get()

if story_creator.device_id and story_creator.uid != reactor.uid:
    service = GlobalNotificationService()
    service.send(
        event_type="story_reaction",
        recipients=[{
            'device_id': story_creator.device_id,
            'uid': story_creator.uid
        }],
        username=reactor.username,
        reaction_type=reaction.type,
        story_id=story.uid
    )
```

### 6.3 Story Mention
**File**: `story/graphql/mutations.py` (CreateStory with mentions)
**Event Type**: `story_mention`

```python
# After creating story with mentions
from notification.global_service import GlobalNotificationService

# For each mentioned user
for mentioned_user in mentioned_users:
    if mentioned_user.device_id:
        service = GlobalNotificationService()
        service.send(
            event_type="story_mention",
            recipients=[{
                'device_id': mentioned_user.device_id,
                'uid': mentioned_user.uid
            }],
            username=story_creator.username,
            story_id=story.uid
        )
```

### 6.4 Story Expiring Soon
**File**: Scheduled task or background job
**Event Type**: `story_expiring_soon`

```python
# Before story expires (1 hour before)
from notification.global_service import GlobalNotificationService

if story_creator.device_id:
    service = GlobalNotificationService()
    service.send(
        event_type="story_expiring_soon",
        recipients=[{
            'device_id': story_creator.device_id,
            'uid': story_creator.uid
        }],
        username=story_creator.username,
        story_id=story.uid,
        expires_in="1 hour"
    )
```

---

## 7. Notifications & Requests

### 7.1 Pending Connection Requests
**File**: Scheduled task or on login
**Event Type**: `pending_connection_requests`

```python
# Periodic check or on login
from notification.global_service import GlobalNotificationService

pending_count = user.pending_connection_requests.count()

if pending_count > 0 and user.device_id:
    service = GlobalNotificationService()
    service.send(
        event_type="pending_connection_requests",
        recipients=[{
            'device_id': user.device_id,
            'uid': user.uid
        }],
        username=user.username,
        request_count=pending_count
    )
```

### 7.2 Community Invite
**File**: `community/graphql/mutations.py` (InviteToCommunity mutation)
**Event Type**: `community_invite`

```python
# After inviting user to community
from notification.global_service import GlobalNotificationService

if invited_user.device_id:
    service = GlobalNotificationService()
    service.send(
        event_type="community_invite",
        recipients=[{
            'device_id': invited_user.device_id,
            'uid': invited_user.uid
        }],
        username=inviter.username,
        community_name=community.name,
        community_id=community.uid,
        invite_id=invite.uid
    )
```

### 7.3 Community Request Accepted
**File**: `community/graphql/mutations.py` (ApproveJoinRequest mutation)
**Event Type**: `community_request_accepted`

```python
# After approving join request
from notification.global_service import GlobalNotificationService

if requester.device_id:
    service = GlobalNotificationService()
    service.send(
        event_type="community_request_accepted",
        recipients=[{
            'device_id': requester.device_id,
            'uid': requester.uid
        }],
        community_name=community.name,
        community_id=community.uid
    )
```

### 7.4 Event Invitation
**File**: `community/graphql/mutations.py` or `events/graphql/mutations.py`
**Event Type**: `event_invitation`

```python
# After inviting to event
from notification.global_service import GlobalNotificationService

if invited_user.device_id:
    service = GlobalNotificationService()
    service.send(
        event_type="event_invitation",
        recipients=[{
            'device_id': invited_user.device_id,
            'uid': invited_user.uid
        }],
        username=inviter.username,
        event_name=event.name,
        event_id=event.uid
    )
```

---

## 8. Chat & Messaging

### 8.1 New Message Received
**File**: `msg/graphql/mutations.py` (SendMessage mutation)
**Event Type**: `new_message`

```python
# After sending message
from notification.global_service import GlobalNotificationService

if receiver.device_id and sender.uid != receiver.uid:
    service = GlobalNotificationService()
    service.send(
        event_type="new_message",
        recipients=[{
            'device_id': receiver.device_id,
            'uid': receiver.uid
        }],
        username=sender.username,
        message_preview=message.text[:100],
        chat_id=chat.uid,
        message_id=message.uid
    )
```

### 8.2 Unread Messages
**File**: Scheduled task or on app open
**Event Type**: `unread_messages`

```python
# Periodic check
from notification.global_service import GlobalNotificationService

unread_count = user.unread_messages_count()

if unread_count > 0 and user.device_id:
    service = GlobalNotificationService()
    service.send(
        event_type="unread_messages",
        recipients=[{
            'device_id': user.device_id,
            'uid': user.uid
        }],
        username=user.username,
        unread_count=unread_count
    )
```

### 8.3 Group Chat Mention
**File**: `msg/graphql/mutations.py` (SendGroupMessage with mentions)
**Event Type**: `group_chat_mention`

```python
# After sending group message with mention
from notification.global_service import GlobalNotificationService

for mentioned_user in mentioned_users:
    if mentioned_user.device_id and mentioned_user.uid != sender.uid:
        service = GlobalNotificationService()
        service.send(
            event_type="group_chat_mention",
            recipients=[{
                'device_id': mentioned_user.device_id,
                'uid': mentioned_user.uid
            }],
            username=sender.username,
            group_name=group.name,
            message_preview=message.text[:100],
            group_id=group.uid,
            message_id=message.uid
        )
```

### 8.4 New Group Chat Created
**File**: `msg/graphql/mutations.py` (CreateGroupChat mutation)
**Event Type**: `new_group_chat_created`

```python
# After creating group chat
from notification.global_service import GlobalNotificationService

# Notify all members except creator
for member in group_members:
    if member.device_id and member.uid != creator.uid:
        recipients = []
        recipients.append({
            'device_id': member.device_id,
            'uid': member.uid
        })

if recipients:
    service = GlobalNotificationService()
    service.send(
        event_type="new_group_chat_created",
        recipients=recipients,
        group_name=group.name,
        creator_name=creator.username,
        group_id=group.uid
    )
```

---

## 9. Search & Discovery

### 9.1 Trending Topic Matches Interest
**File**: Scheduled task or recommendation engine
**Event Type**: `trending_topic_matching_interest`

```python
# When trending topic matches user interest
from notification.global_service import GlobalNotificationService

if user.device_id:
    service = GlobalNotificationService()
    service.send(
        event_type="trending_topic_matching_interest",
        recipients=[{
            'device_id': user.device_id,
            'uid': user.uid
        }],
        topic_name=trending_topic.name,
        topic_id=trending_topic.uid
    )
```

### 9.2 New User in Network
**File**: Scheduled task or after user signs up
**Event Type**: `new_user_in_network`

```python
# After new user with matching interests joins
from notification.global_service import GlobalNotificationService

# Get users with matching interests
matching_users = get_users_with_matching_interests(new_user)
recipients = []

for user in matching_users:
    if user.device_id:
        recipients.append({
            'device_id': user.device_id,
            'uid': user.uid
        })

if recipients:
    service = GlobalNotificationService()
    service.send(
        event_type="new_user_in_network",
        recipients=recipients,
        username=new_user.username,
        user_id=new_user.uid
    )
```

### 9.3 Suggested Community
**File**: Recommendation engine or scheduled task
**Event Type**: `suggested_community`

```python
# When community matches user interests
from notification.global_service import GlobalNotificationService

if user.device_id:
    service = GlobalNotificationService()
    service.send(
        event_type="suggested_community",
        recipients=[{
            'device_id': user.device_id,
            'uid': user.uid
        }],
        community_name=suggested_community.name,
        community_id=suggested_community.uid
    )
```

---

## 10. Menu & Privacy Settings

### 10.1 Privacy Settings Reminder
**File**: Scheduled task
**Event Type**: `privacy_settings_reminder`

```python
# Periodic reminder
from notification.global_service import GlobalNotificationService

if user.device_id and not user.has_reviewed_privacy_recently():
    service = GlobalNotificationService()
    service.send(
        event_type="privacy_settings_reminder",
        recipients=[{
            'device_id': user.device_id,
            'uid': user.uid
        }],
        username=user.username
    )
```

### 10.2 Profile Visibility Changed
**File**: `auth_manager/graphql/mutations.py` (UpdatePrivacySettings mutation)
**Event Type**: `profile_visibility_changed`

```python
# After changing profile visibility
from notification.global_service import GlobalNotificationService

if user.device_id:
    service = GlobalNotificationService()
    service.send(
        event_type="profile_visibility_changed",
        recipients=[{
            'device_id': user.device_id,
            'uid': user.uid
        }],
        username=user.username,
        visibility_status=new_visibility  # "Public" or "Private"
    )
```

### 10.3 Account Security Alert
**File**: `auth_manager/graphql/mutations.py` or security monitoring
**Event Type**: `account_security_alert`

```python
# After detecting unusual activity
from notification.global_service import GlobalNotificationService

if user.device_id:
    service = GlobalNotificationService()
    service.send(
        event_type="account_security_alert",
        recipients=[{
            'device_id': user.device_id,
            'uid': user.uid
        }],
        username=user.username,
        activity_type="Unusual login detected"
    )
```

### 10.4 New Feature Available
**File**: Scheduled task or admin trigger
**Event Type**: `new_feature_available`

```python
# After releasing new feature
from notification.global_service import GlobalNotificationService

# Get all active users
active_users = Users.nodes.filter(is_active=True)
recipients = []

for user in active_users:
    if user.device_id:
        recipients.append({
            'device_id': user.device_id,
            'uid': user.uid
        })

if recipients:
    service = GlobalNotificationService()
    service.send(
        event_type="new_feature_available",
        recipients=recipients,
        feature_name="New Privacy Controls",
        feature_description="Enhanced privacy settings"
    )
```

---

## 11. Version Updates

### 11.1 New App Version Available
**File**: Scheduled task or version check
**Event Type**: `new_app_version_available`

```python
# After new version release
from notification.global_service import GlobalNotificationService

# Get all users with older versions
users_needing_update = get_users_with_old_version()
recipients = []

for user in users_needing_update:
    if user.device_id:
        recipients.append({
            'device_id': user.device_id,
            'uid': user.uid
        })

if recipients:
    service = GlobalNotificationService()
    service.send(
        event_type="new_app_version_available",
        recipients=recipients,
        version_number="2.5.0",
        update_type="optional"
    )
```

### 11.2 Mandatory Update Required
**File**: Version check or on app launch
**Event Type**: `mandatory_update_required`

```python
# For critical updates
from notification.global_service import GlobalNotificationService

if user.device_id and user.app_version < minimum_required_version:
    service = GlobalNotificationService()
    service.send(
        event_type="mandatory_update_required",
        recipients=[{
            'device_id': user.device_id,
            'uid': user.uid
        }],
        version_number="2.5.0",
        username=user.username
    )
```

---

## 12. Incomplete Processes

### 12.1 Incomplete Sign-Up
**File**: Scheduled task
**Event Type**: `incomplete_signup`

```python
# Check for incomplete signups
from notification.global_service import GlobalNotificationService

incomplete_users = get_users_with_incomplete_signup()

for user in incomplete_users:
    if user.device_id:
        service = GlobalNotificationService()
        service.send(
            event_type="incomplete_signup",
            recipients=[{
                'device_id': user.device_id,
                'uid': user.uid
            }],
            username=user.username
        )
```

### 12.2 Incomplete Profile
**File**: Scheduled task or on login
**Event Type**: `incomplete_profile`

```python
# Check for incomplete profiles
from notification.global_service import GlobalNotificationService

if user.device_id and not user.profile_complete:
    service = GlobalNotificationService()
    service.send(
        event_type="incomplete_profile",
        recipients=[{
            'device_id': user.device_id,
            'uid': user.uid
        }],
        username=user.username,
        completion_percentage=user.profile_completion_percentage()
    )
```

### 12.3 No Connections Yet
**File**: Scheduled task
**Event Type**: `no_connections_yet`

```python
# Check for users without connections
from notification.global_service import GlobalNotificationService

if user.device_id and user.connections.count() == 0:
    service = GlobalNotificationService()
    service.send(
        event_type="no_connections_yet",
        recipients=[{
            'device_id': user.device_id,
            'uid': user.uid
        }],
        username=user.username
    )
```

### 12.4 First Post Encouragement
**File**: Scheduled task
**Event Type**: `first_post_encouragement`

```python
# Check for users who haven't posted
from notification.global_service import GlobalNotificationService

if user.device_id and user.posts.count() == 0:
    service = GlobalNotificationService()
    service.send(
        event_type="first_post_encouragement",
        recipients=[{
            'device_id': user.device_id,
            'uid': user.uid
        }],
        username=user.username
    )
```

### 12.5 Community Goal Incomplete
**File**: Scheduled task or goal check
**Event Type**: `community_goal_incomplete`

```python
# Check for incomplete goal participation
from notification.global_service import GlobalNotificationService

if user.device_id and not user.has_contributed_to_goal(goal):
    service = GlobalNotificationService()
    service.send(
        event_type="community_goal_incomplete",
        recipients=[{
            'device_id': user.device_id,
            'uid': user.uid
        }],
        goal_name=goal.name,
        community_name=community.name,
        goal_id=goal.uid
    )
```

---

## Important Implementation Notes

### 1. Always Check Device ID
```python
if user.device_id:
    # Send notification
```

### 2. Don't Notify Self
```python
if recipient.uid != sender.uid:
    # Send notification
```

### 3. Batch Notifications for Multiple Recipients
```python
# Good: Single call for multiple recipients
service.send(
    event_type="...",
    recipients=[...],  # List of recipients
    ...
)

# Bad: Multiple calls
for recipient in recipients:
    service.send(...)  # Don't do this
```

### 4. Error Handling
```python
try:
    service = GlobalNotificationService()
    service.send(...)
except Exception as e:
    logger.error(f"Notification error: {e}")
    # Continue with mutation - don't fail on notification errors
```

### 5. Async Considerations
The service handles async internally, so you can call it synchronously:
```python
# This works fine
service.send(...)
# Notification sent in background
```

### 6. Import Location
Always import at the top of your mutation file:
```python
from notification.global_service import GlobalNotificationService
```

---

## Testing Your Notifications

### Test a Single Notification
```python
from notification.global_service import GlobalNotificationService

service = GlobalNotificationService()
service.send(
    event_type="new_comment_on_post",
    recipients=[{
        'device_id': 'your_test_device_id',
        'uid': 'test_user_uid'
    }],
    username="Test User",
    comment_text="Test comment",
    post_id="test_post_123"
)
```

### Check Django Admin
1. Go to Django Admin
2. Navigate to User Notifications
3. See all sent notifications
4. Check status, timestamps, and data

### View Notification Stats
```bash
python manage.py notification_stats
```

---

## Next Steps

1. **Run Migrations**
   ```bash
   python manage.py makemigrations notification
   python manage.py migrate notification
   ```

2. **Add Notifications to Mutations**
   - Start with high-priority notifications (comments, messages, connections)
   - Use this guide for exact code to add
   - Test each notification after adding

3. **Monitor Performance**
   - Check Django Admin for failed notifications
   - Review notification logs
   - Adjust batch sizes if needed

4. **Add More Templates**
   - If you need custom notifications, add to `notification/notification_templates.py`
   - Follow the existing pattern

---

## Summary

This guide provides ready-to-use code for **all** notification types from your HTML file. Each section includes:
- ✅ Exact file location
- ✅ Event type to use
- ✅ Complete code snippet
- ✅ Where to place the code

Simply copy and paste the relevant code into your mutation files, and the notification system will handle the rest!

For questions or issues, refer to:
- `notification/SIMPLE_USAGE.md` - Basic usage
- `notification/MIGRATION_EXAMPLES.md` - Migration from old services
- `notification/README.md` - Complete documentation
