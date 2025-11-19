"""
Notification Templates for Ooumph App
=====================================

This file contains all notification templates for the Ooumph app.
Each template defines the structure for a specific notification type.

Template Structure:
{
    "event_type": {
        "title": "Notification title with {placeholders}",
        "body": "Notification body with {placeholders}",
        "click_action": "/path/to/{resource}",
        "priority": "high|normal|low|urgent",
        "image_url": "{optional_image_url}"  # Optional
    }
}

Priorities:
- urgent: Critical system alerts, security issues
- high: User interactions, new content from connections
- normal: General updates, reminders
- low: Background notifications, suggestions

All notifications (except onboarding) from Ooumph App Notifications.html
Total: 128+ notification templates
"""

from enum import Enum


class NotificationEventType(str, Enum):
    """
    Enum for notification event types.
    This validates event types at runtime.
    """
    def _generate_next_value_(name, start, count, last_values):
        return name
    
    @classmethod
    def _missing_(cls, value):
        """Allow string values to be used directly"""
        return value

NOTIFICATION_TEMPLATES = {
    
    # =========================================================================
    # 3. FEED & CONTENT INTERACTIONS
    # =========================================================================
    
    "new_post_from_connection": {
        "title": "{username} just posted!",
        "body": "Check out their latest post now.",
        "click_action": "/post/{post_id}",
        "priority": "high",
        "image_url": "{post_image_url}"
    },
    
    "new_comment_on_post": {
        "title": "{username} commented on your post",
        "body": "See what they said!",
        "click_action": "/post/{post_id}/comments",
        "priority": "high"
    },
    
    "post_comment": {
        "title": "New comment from {username}",
        "body": '"{comment_text}"',
        "click_action": "/post/{post_id}/comments",
        "priority": "high"
    },
    
    "vibe_reaction_on_post": {
        "title": "{username} vibed with your post!",
        "body": "Tap to view their reaction.",
        "click_action": "/post/{post_id}/reactions",
        "priority": "high"
    },
    
    "new_story_from_connection": {
        "title": "{username} shared a new story",
        "body": "Watch it before it disappears!",
        "click_action": "/story/{story_id}",
        "priority": "high",
        "image_url": "{story_thumbnail_url}"
    },
    
    "vibe_analytics": {
        "title": "Your post is getting noticed!",
        "body": "Check out your vibe analytics.",
        "click_action": "/post/{post_id}/analytics",
        "priority": "normal"
    },
    
    # =========================================================================
    # 4. PROFILE & CONNECTION UPDATES
    # =========================================================================
    
    "profile_edit_reminder": {
        "title": "Update Your Profile!",
        "body": "Enhance your profile to stand out in the community.",
        "click_action": "/profile/edit",
        "priority": "normal"
    },
    
    "new_connection_request": {
        "title": "New Connection Request!",
        "body": "{username} wants to connect with you. Review the request now!",
        "click_action": "/connections/requests",
        "priority": "high"
    },
    
    "connection_accepted": {
        "title": "You're Now Connected!",
        "body": "{username} accepted your connection request. Start a conversation now!",
        "click_action": "/connections/{connection_id}",
        "priority": "high"
    },
    
    "mutual_connection_added": {
        "title": "New Mutual Connection!",
        "body": "You and {username} now share a mutual connection. Say hi!",
        "click_action": "/connections/mutual",
        "priority": "normal"
    },
    
    "special_moment_added_background": {
        "title": "{name} has been added to your profile",
        "body": "Open the app to view the moment!",
        "click_action": "/profile/special-moments",
        "priority": "normal"
    },
    
    "special_moment_added_active": {
        "title": "Special Moment Created!",
        "body": "You've successfully added {name} to your profile. Let the connection begin!",
        "click_action": "/profile/special-moments/{moment_id}",
        "priority": "normal"
    },
    
    "achievement_added": {
        "title": "Achievement Unlocked: {achievement_name}!",
        "body": "Keep it up!",
        "click_action": "/profile/achievements/{achievement_id}",
        "priority": "high",
        "image_url": "{achievement_icon}"
    },
    
    "education_added": {
        "title": "Education Updated!",
        "body": "{degree_name} at {institution_name}",
        "click_action": "/profile/education",
        "priority": "normal"
    },
    
    "experience_added": {
        "title": "New Work Experience!",
        "body": "{job_title} at {company_name}",
        "click_action": "/profile/experience",
        "priority": "normal"
    },
    
    "skill_added": {
        "title": "Skill Added!",
        "body": "{skill_name} is now on your profile!",
        "click_action": "/profile/skills",
        "priority": "normal"
    },
    
    "note_saved": {
        "title": "Note Saved!",
        "body": "'{note_title}' has been added!",
        "click_action": "/profile/notes/{note_id}",
        "priority": "normal"
    },
    
    "sub_relation_updated": {
        "title": "Sub-relation Updated!",
        "body": "{sub_relation_name} has been changed.",
        "click_action": "/profile/relationships",
        "priority": "normal"
    },
    
    "profile_viewed": {
        "title": "Someone checked out your profile!",
        "body": "See who's interested in connecting.",
        "click_action": "/profile/views",
        "priority": "normal"
    },
    
    "profile_viewed_multiple": {
        "title": "Your profile is getting noticed!",
        "body": "{view_count} people viewed your profile recently.",
        "click_action": "/profile/views",
        "priority": "normal"
    },
    
    "vibe_received": {
        "title": "You received a vibe!",
        "body": "Check it out!",
        "click_action": "/profile/vibes",
        "priority": "high"
    },
    
    "multiple_vibes_received": {
        "title": "You're popular!",
        "body": "Many users sent you vibes!",
        "click_action": "/profile/vibes",
        "priority": "high"
    },
    
    # =========================================================================
    # 5. COMMUNITY INTERACTIONS
    # =========================================================================
    
    "new_sibling_community": {
        "title": "New Community Available!",
        "body": "A new sibling community, {community_name}, has been created. Explore now!",
        "click_action": "/community/{community_id}",
        "priority": "normal",
        "image_url": "{community_icon}"
    },
    
    "new_child_community": {
        "title": "New Community Added!",
        "body": "A child community, {community_name}, is now available. Join the conversation!",
        "click_action": "/community/{community_id}",
        "priority": "normal",
        "image_url": "{community_icon}"
    },
    
    "community_role_change": {
        "title": "Role Update!",
        "body": "Your role in {community_name} has been updated. Check out your new permissions.",
        "click_action": "/community/{community_id}/settings",
        "priority": "high"
    },
    
    "new_members_joined": {
        "title": "New Members Joined!",
        "body": "{member_count} new members have joined {community_name}. Say hello!",
        "click_action": "/community/{community_id}/members",
        "priority": "normal"
    },
    
    "community_announcement": {
        "title": "Community Update!",
        "body": "{community_name} has a new announcement. Tap to read more.",
        "click_action": "/community/{community_id}/announcements",
        "priority": "high"
    },
    
    "new_community_post": {
        "title": "New Post Alert!",
        "body": "{username} shared a new post in {community_name}. Join the discussion!",
        "click_action": "/community/{community_id}/post/{post_id}",
        "priority": "high",
        "image_url": "{post_image_url}"
    },
    
    "community_post_reaction": {
        "title": "New Reaction!",
        "body": "{username} reacted to your post in {community_name}. See their response!",
        "click_action": "/community/{community_id}/post/{post_id}",
        "priority": "high"
    },
    
    "community_post_comment": {
        "title": "New Comment!",
        "body": "{username} commented on your post in {community_name}. Reply now!",
        "click_action": "/community/{community_id}/post/{post_id}/comments",
        "priority": "high"
    },
    
    "community_post_mention": {
        "title": "You Were Mentioned!",
        "body": "{username} mentioned you in {community_name}. Check it out!",
        "click_action": "/community/{community_id}/post/{post_id}",
        "priority": "high"
    },
    
    "community_event_reminder": {
        "title": "Upcoming Event!",
        "body": "{event_name} in {community_name} is starting soon. Get ready to join!",
        "click_action": "/community/{community_id}/event/{event_id}",
        "priority": "high"
    },
    
    "community_goal_created": {
        "title": "New Community Goal!",
        "body": "{goal_name} - Get involved now!",
        "click_action": "/community/{community_id}/goal/{goal_id}",
        "priority": "normal"
    },
    
    "community_achievement_unlocked": {
        "title": "Congrats!",
        "body": "You unlocked {achievement_name} in {community_name}!",
        "click_action": "/community/{community_id}/achievements",
        "priority": "high",
        "image_url": "{achievement_icon}"
    },
    
    "community_affiliation": {
        "title": "Welcome {username}!",
        "body": "You are now part of {community_name}.",
        "click_action": "/community/{community_id}",
        "priority": "normal",
        "image_url": "{community_icon}"
    },
    
    "join_community_reminder": {
        "title": "Discover Communities!",
        "body": "Join communities that match your interests and engage with like-minded people!",
        "click_action": "/communities/discover",
        "priority": "normal"
    },
    
    "create_community_reminder": {
        "title": "Start Your Own Community!",
        "body": "Create a personal, business, or interest-based community today!",
        "click_action": "/community/create",
        "priority": "normal"
    },
    
    "incomplete_community_goal": {
        "title": "Goal Reminder!",
        "body": "You haven't contributed to {goal_name} yet! Help now!",
        "click_action": "/community/{community_id}/goal/{goal_id}",
        "priority": "normal"
    },
    
    "pending_community_approval": {
        "title": "Request Pending!",
        "body": "Your request to join {community_name} is still pending!",
        "click_action": "/community/{community_id}",
        "priority": "normal"
    },
    
    # =========================================================================
    # 6. STORY & MEDIA UPLOADS
    # =========================================================================
    
    "new_story_available": {
        "title": "New Story Alert!",
        "body": "{username} just posted a new story. Watch it before it disappears!",
        "click_action": "/story/{story_id}",
        "priority": "high",
        "image_url": "{story_thumbnail_url}"
    },
    
    "story_reaction": {
        "title": "Story Love!",
        "body": "{username} reacted to your story! Tap to see their reaction.",
        "click_action": "/story/{story_id}/reactions",
        "priority": "high"
    },
    
    "story_mention": {
        "title": "You Were Mentioned!",
        "body": "{username} mentioned you in their story. Check it out now!",
        "click_action": "/story/{story_id}",
        "priority": "high"
    },
    
    "story_expiring_soon": {
        "title": "Last Chance!",
        "body": "Your story is about to disappear! Save it or repost before it's gone.",
        "click_action": "/story/{story_id}",
        "priority": "normal"
    },
    
    "story_upload_reminder": {
        "title": "Share Your Story!",
        "body": "Let your friends know what you're up to today!",
        "click_action": "/story/create",
        "priority": "normal"
    },
    
    # =========================================================================
    # 7. NOTIFICATIONS & REQUESTS
    # =========================================================================
    
    "pending_connection_requests": {
        "title": "You Have Requests!",
        "body": "You have {request_count} new connection requests waiting. Approve or decline now!",
        "click_action": "/connections/requests",
        "priority": "high"
    },
    
    "community_invitation_received": {
        "title": "Join a New Community!",
        "body": "{username} invited you to join {community_name}. Tap to accept!",
        "click_action": "/community/{community_id}/invitation",
        "priority": "high"
    },
    
    "community_request_accepted": {
        "title": "Request Approved!",
        "body": "Your request to join {community_name} has been accepted. Start engaging now!",
        "click_action": "/community/{community_id}",
        "priority": "high"
    },
    
    "friend_request_accepted": {
        "title": "New Connection!",
        "body": "{username} accepted your connection request. Say hi!",
        "click_action": "/connections/{connection_id}",
        "priority": "high"
    },
    
    "event_invitation_received": {
        "title": "You're Invited!",
        "body": "{username} invited you to {event_name}. Tap to RSVP!",
        "click_action": "/event/{event_id}",
        "priority": "high"
    },
    
    "pending_invites_reminder": {
        "title": "You're Invited!",
        "body": "Join {community_name} and be part of the discussion!",
        "click_action": "/community/{community_id}",
        "priority": "normal"
    },
    
    # =========================================================================
    # 8. CHAT & MESSAGING
    # =========================================================================
    
    "new_message": {
        "title": "New Message!",
        "body": "{sender_name}: {message_preview}",
        "click_action": "/chat/{chat_id}",
        "priority": "high"
    },
    
    "unread_messages": {
        "title": "Unread Chats!",
        "body": "You have {unread_count} unread messages waiting. Catch up now!",
        "click_action": "/chat",
        "priority": "normal"
    },
    
    "group_chat_mention": {
        "title": "You Were Mentioned!",
        "body": "{username} mentioned you in {group_name}. See what they said!",
        "click_action": "/chat/{chat_id}",
        "priority": "high"
    },
    
    "new_group_chat_created": {
        "title": "New Group!",
        "body": "You have been added to {group_name}. Join the conversation!",
        "click_action": "/chat/{chat_id}",
        "priority": "high"
    },
    
    "chat_engagement_reminder": {
        "title": "Start a Conversation!",
        "body": "Send a message to your connections and stay in touch!",
        "click_action": "/chat",
        "priority": "normal"
    },
    
    # =========================================================================
    # 9. DISCOVERY & TRENDING
    # =========================================================================
    
    "trending_topic_matching_interest": {
        "title": "Hot Topic!",
        "body": "{topic_name} is trending in your network. Join the discussion now!",
        "click_action": "/trending/{topic_id}",
        "priority": "normal"
    },
    
    "new_user_in_network": {
        "title": "New Connection Opportunity!",
        "body": "{username} just joined! Connect and explore shared interests.",
        "click_action": "/profile/{user_id}",
        "priority": "normal"
    },
    
    "suggested_community": {
        "title": "Explore More!",
        "body": "You might like {community_name}. Tap to discover new discussions!",
        "click_action": "/community/{community_id}",
        "priority": "normal",
        "image_url": "{community_icon}"
    },
    
    "explore_top_vibes": {
        "title": "See What's Trending!",
        "body": "Explore top vibes, hobbies, and trending discussions now!",
        "click_action": "/explore/trending",
        "priority": "normal"
    },
    
    "find_new_arrivals": {
        "title": "Meet New People!",
        "body": "Connect with new users who share your interests!",
        "click_action": "/discover/users",
        "priority": "normal"
    },
    
    # =========================================================================
    # 10. SETTINGS & PRIVACY
    # =========================================================================
    
    "privacy_settings_reminder": {
        "title": "Privacy Check!",
        "body": "Review your privacy settings to keep your data secure.",
        "click_action": "/settings/privacy",
        "priority": "normal"
    },
    
    "profile_visibility_change": {
        "title": "Profile Update!",
        "body": "Your profile is now {visibility_status}. Adjust your settings anytime.",
        "click_action": "/settings/privacy",
        "priority": "normal"
    },
    
    "account_security_alert": {
        "title": "Security Alert!",
        "body": "Unusual login detected. Review your login history for safety.",
        "click_action": "/settings/security",
        "priority": "urgent"
    },
    
    "new_feature_in_settings": {
        "title": "New Settings Available!",
        "body": "We've added new privacy controls. Check them out now!",
        "click_action": "/settings",
        "priority": "normal"
    },
    
    "general_settings_reminder": {
        "title": "Personalize Your Experience!",
        "body": "Update your settings for a customized experience!",
        "click_action": "/settings",
        "priority": "normal"
    },
    
    # =========================================================================
    # 11. APP UPDATES & SYSTEM
    # =========================================================================
    
    "new_app_version_available": {
        "title": "Ooumph Update Available!",
        "body": "Get the latest version with new features and improvements!",
        "click_action": "/app/update",
        "priority": "normal"
    },
    
    "mandatory_update_required": {
        "title": "Update Required!",
        "body": "To continue using Ooumph, please update to the latest version now!",
        "click_action": "/app/update",
        "priority": "urgent"
    },
    
    "new_features_added": {
        "title": "Exciting New Features!",
        "body": "Check out the latest features and enhancements in Ooumph!",
        "click_action": "/app/whats-new",
        "priority": "normal"
    },
    
    "security_update": {
        "title": "Stay Secure!",
        "body": "Update to the latest version for better security and protection!",
        "click_action": "/app/update",
        "priority": "high"
    },
    
    # =========================================================================
    # 12. ENGAGEMENT REMINDERS
    # =========================================================================
    
    "vibe_interaction_reminder": {
        "title": "Express Yourself!",
        "body": "React to posts and share your vibe!",
        "click_action": "/feed",
        "priority": "normal"
    },
    
    "commenting_reminder": {
        "title": "Join the Conversation!",
        "body": "Drop a comment and share your thoughts!",
        "click_action": "/feed",
        "priority": "normal"
    },
    
    "connection_flow_reminder": {
        "title": "Find Your Circle!",
        "body": "Start connecting with people who share your interests!",
        "click_action": "/connections/discover",
        "priority": "normal"
    },
    
    # =========================================================================
    # 13. INCOMPLETE ACTIONS
    # =========================================================================
    
    "achievement_incomplete": {
        "title": "Almost There!",
        "body": "Complete your achievement details for {achievement_name}.",
        "click_action": "/profile/achievements/edit/{achievement_id}",
        "priority": "normal"
    },
    
    "education_incomplete": {
        "title": "Don't Forget!",
        "body": "Complete your education details for {institution_name}!",
        "click_action": "/profile/education/edit/{education_id}",
        "priority": "normal"
    },
    
    "experience_incomplete": {
        "title": "Finish Your Update!",
        "body": "You started adding {job_title} at {company_name}. Complete it now!",
        "click_action": "/profile/experience/edit/{experience_id}",
        "priority": "normal"
    },
    
    "skill_incomplete": {
        "title": "Unsaved Changes!",
        "body": "You added {skill_name} but didn't save it. Finish updating your skills!",
        "click_action": "/profile/skills/edit",
        "priority": "normal"
    },
    
    "note_incomplete": {
        "title": "Unsaved Note!",
        "body": "Your draft note '{note_title}' is unsaved. Want to continue?",
        "click_action": "/profile/notes/edit/{note_id}",
        "priority": "normal"
    },
    
    "sub_relation_incomplete": {
        "title": "Unsaved Changes!",
        "body": "Your changes to {sub_relation_name} are not saved! Finish updating now.",
        "click_action": "/profile/relationships/edit",
        "priority": "normal"
    },
    
    "unfinished_task": {
        "title": "Task Reminder!",
        "body": "Your task {task_name} is still pending. Complete it now!",
        "click_action": "/tasks/{task_id}",
        "priority": "normal"
    },
    
    "missed_achievement": {
        "title": "You're So Close!",
        "body": "You're almost at {achievement_name}! Keep going!",
        "click_action": "/profile/achievements",
        "priority": "normal"
    },
    
    "vibe_with_incomplete_profile": {
        "title": "You Received a Vibe!",
        "body": "Complete your profile to connect!",
        "click_action": "/profile/edit",
        "priority": "high"
    },
}


def get_template(event_type: str) -> dict:
    """
    Get a notification template by event type.
    
    Args:
        event_type: The event type key
        
    Returns:
        dict: Template dictionary or None if not found
    """
    return NOTIFICATION_TEMPLATES.get(event_type)


def get_all_event_types() -> list:
    """
    Get a list of all available event types.
    
    Returns:
        list: List of all event type keys
    """
    return list(NOTIFICATION_TEMPLATES.keys())


def search_templates(keyword: str) -> dict:
    """
    Search for templates containing a keyword.
    
    Args:
        keyword: Search keyword
        
    Returns:
        dict: Dictionary of matching templates
    """
    keyword_lower = keyword.lower()
    return {
        event_type: template
        for event_type, template in NOTIFICATION_TEMPLATES.items()
        if keyword_lower in event_type.lower() or
           keyword_lower in template.get('title', '').lower() or
           keyword_lower in template.get('body', '').lower()
    }


def format_notification(event_type, **template_vars):
    """
    Format a notification template with variables.
    
    Args:
        event_type: Notification event type (string or NotificationEventType)
        **template_vars: Variables to fill in the template placeholders
        
    Returns:
        dict: Formatted notification with title, body, click_action, priority, etc.
        
    Raises:
        KeyError: If event_type is not found in templates
    """
    # Convert to string (handles both string and enum)
    event_key = str(event_type) if not isinstance(event_type, str) else event_type
    
    # Get template
    template = NOTIFICATION_TEMPLATES.get(event_key)
    if not template:
        raise KeyError(f"Notification template '{event_key}' not found")
    
    # Format template strings with provided variables
    formatted = {}
    for key, value in template.items():
        if isinstance(value, str) and '{' in value:
            try:
                # Replace placeholders with values, keep unfilled ones as is
                formatted[key] = value.format(**{k: v for k, v in template_vars.items() if v is not None})
            except KeyError as e:
                # If a required placeholder is missing, keep the original
                formatted[key] = value
        else:
            formatted[key] = value
    
    # Add data payload
    formatted['data'] = template_vars
    
    return formatted
