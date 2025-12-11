"""
Notification Templates for Ooumph App
=====================================

This file contains all notification templates for the Ooumph app.
Each template defines the structure for a specific notification type.

Updated format with deep_link and web_link support.

Template Structure:
{
    "event_type": {
        "title": "Notification title with {placeholders}",
        "body": "Notification body with {placeholders}",
        "image_url": "{optional_image_url}",  # Optional
        "click_action": "/path/to/{resource}",
        "deep_link": "ooumph://path/to/{resource}",
        "web_link": "https://app.ooumph.com/path/to/{resource}",
        "priority": "high|normal|low|urgent"
    }
}

Priorities:
- urgent: Critical system alerts, security issues
- high: User interactions, new content from connections
- normal: General updates, reminders
- low: Background notifications, suggestions
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


# Base URL for web links (can be configured)
WEB_BASE_URL = "https://app.ooumph.com"


NOTIFICATION_TEMPLATES = {
    
   
    # =========================================================================
    # 3. FEED & CONTENT INTERACTIONS
    # =========================================================================
    
    "new_post_from_connection": {
        "title": "{username} just posted something new!",
        "body": "Check it out.",
        "image_url": "{post_image_url}",
        "click_action": "/post/{post_id}",
        "deep_link": "ooumph://post/{post_id}",
        "web_link": f"{WEB_BASE_URL}/post/{{post_id}}",
        "priority": "high"
    },
    
    "new_comment_on_post": {
        "title": "{username} commented on your post",
        "body": "See what they said!",
        "click_action": "/post/{post_id}/comments",
        "deep_link": "ooumph://post/{post_id}/comments",
        "web_link": f"{WEB_BASE_URL}/post/{{post_id}}/comments",
        "priority": "high"
    },
    
    "post_comment": {
        "title": "New comment from {username}",
        "body": "{comment_text}",
        "click_action": "/post/{post_id}/comments",
        "deep_link": "ooumph://post/{post_id}/comments",
        "web_link": f"{WEB_BASE_URL}/post/{{post_id}}/comments",
        "priority": "high"
    },
    
    "comment_vibe_reaction": {
        "title": "{username} vibed with your comment!",
        "body": "Tap to view their reaction.",
        "click_action": "/post/{post_id}/comments",
        "deep_link": "ooumph://post/{post_id}/comments",
        "web_link": f"{WEB_BASE_URL}/post/{{post_id}}/comments",
        "priority": "high"
    },
    
    "vibe_reaction_on_post": {
        "title": "{username} vibed with your post!",
        "body": "Tap to view their reaction.",
        "click_action": "/post/{post_id}/reactions",
        "deep_link": "ooumph://post/{post_id}/reactions",
        "web_link": f"{WEB_BASE_URL}/post/{{post_id}}/reactions",
        "priority": "high"
    },
    
    "new_story_from_connection": {
        "title": "{username} just shared a new story!",
        "body": "Tap to view.",
        "image_url": "{story_thumbnail_url}",
        "click_action": "/story/{story_id}",
        "deep_link": "ooumph://story/{story_id}",
        "web_link": f"{WEB_BASE_URL}/story/{{story_id}}",
        "priority": "high"
    },
    
    # =========================================================================
    # 4. PROFILE & CONNECTION UPDATES
    # =========================================================================
    
    "profile_edit_reminder": {
        "title": "Complete your profile!",
        "body": "Enhance your profile to stand out in the community!",
        "click_action": "/profile/edit",
        "deep_link": "ooumph://profile/edit",
        "web_link": f"{WEB_BASE_URL}/profile/edit",
        "priority": "normal"
    },
    
    "new_connection_request": {
        "title": "{username} wants to connect with you",
        "body": "Accept or decline now.",
        "click_action": "/connections/requests",
        "deep_link": "ooumph://connections/requests",
        "web_link": f"{WEB_BASE_URL}/connections/requests",
        "priority": "high"
    },
    
    "connection_accepted": {
        "title": "{username} accepted your connection request!",
        "body": "Start a conversation now.",
        "click_action": "/profile/{user_id}",
        "deep_link": "ooumph://profile/{user_id}",
        "web_link": f"{WEB_BASE_URL}/profile/{{user_id}}",
        "priority": "high"
    },
    
    "connection_rejected": {
        "title": "Connection request declined",
        "body": "{username} declined your connection request.",
        "click_action": "/connections",
        "deep_link": "ooumph://connections",
        "web_link": f"{WEB_BASE_URL}/connections",
        "priority": "normal"
    },
    
  
    "special_moment_added_background": {
        "title": "{name} has been added to your profile",
        "body": "Open the app to view the moment!",
        "click_action": "/profile/special-moments",
        "deep_link": "ooumph://profile/special-moments",
        "web_link": f"{WEB_BASE_URL}/profile/special-moments",
        "priority": "normal"
    },
    
    "special_moment_added_active": {
        "title": "You've successfully added {name} to your profile",
        "body": "Let the connection begin!",
        "click_action": "/profile/special-moments/{moment_id}",
        "deep_link": "ooumph://profile/special-moments/{moment_id}",
        "web_link": f"{WEB_BASE_URL}/profile/special-moments/{{moment_id}}",
        "priority": "normal"
    },
    
    "achievement_added": {
        "title": "Achievement Unlocked: {achievement_name}!",
        "body": "Keep it up!",
        "image_url": "{achievement_icon}",
        "click_action": "/profile/achievements/{achievement_id}",
        "deep_link": "ooumph://profile/achievements/{achievement_id}",
        "web_link": f"{WEB_BASE_URL}/profile/achievements/{{achievement_id}}",
        "priority": "high"
    },
    
    "education_added": {
        "title": "Education Updated: {degree_name} at {institution_name}!",
        "body": "Great move!",
        "click_action": "/profile/education",
        "deep_link": "ooumph://profile/education",
        "web_link": f"{WEB_BASE_URL}/profile/education",
        "priority": "normal"
    },
    
    "experience_added": {
        "title": "New Work Experience: {job_title} at {company_name}!",
        "body": "Keep building your journey!",
        "click_action": "/profile/experience",
        "deep_link": "ooumph://profile/experience",
        "web_link": f"{WEB_BASE_URL}/profile/experience",
        "priority": "normal"
    },
    
    "skill_added": {
        "title": "Skill Added: {skill_name}!",
        "body": "{skill_name} is now on your profile!",
        "click_action": "/profile/skills",
        "deep_link": "ooumph://profile/skills",
        "web_link": f"{WEB_BASE_URL}/profile/skills",
        "priority": "normal"
    },
    
    "note_saved": {
        "title": "Note Saved: '{note_title}'",
        "body": "'{note_title}' has been added!",
        "click_action": "/profile/notes/{note_id}",
        "deep_link": "ooumph://profile/notes/{note_id}",
        "web_link": f"{WEB_BASE_URL}/profile/notes/{{note_id}}",
        "priority": "normal"
    },
    
   
    "profile_viewed": {
        "title": "Someone just checked out your profile!",
        "body": "See who's interested.",
        "click_action": "/profile/views",
        "deep_link": "ooumph://profile/views",
        "web_link": f"{WEB_BASE_URL}/profile/views",
        "priority": "normal"
    },
    
  
    
    "vibe_sent_to_profile": {
        "title": "You just received a vibe!",
        "body": "Check it out!",
        "click_action": "/profile/vibes",
        "deep_link": "ooumph://profile/vibes",
        "web_link": f"{WEB_BASE_URL}/profile/vibes",
        "priority": "high"
    },
    
 
    
    # =========================================================================
    # 5. COMMUNITY INTERACTIONS
    # =========================================================================
    
    "new_sibling_community": {
        "title": "New Community Available!",
        "body": "A new sibling community, {community_name}, has been created. Explore now!",
        "image_url": "{community_icon}",
        "click_action": "/community/{community_id}",
        "deep_link": "ooumph://community/{community_id}",
        "web_link": f"{WEB_BASE_URL}/community/{{community_id}}",
        "priority": "normal"
    },
    
    "new_child_community": {
        "title": "New Community Added!",
        "body": "A child community, {community_name}, is now available. Join the conversation!",
        "image_url": "{community_icon}",
        "click_action": "/community/{community_id}",
        "deep_link": "ooumph://community/{community_id}",
        "web_link": f"{WEB_BASE_URL}/community/{{community_id}}",
        "priority": "normal"
    },
    
    "community_role_change": {
        "title": "Role Update!",
        "body": "Your role in {community_name} has been updated. Check out your new permissions.",
        "click_action": "/community/{community_id}/settings",
        "deep_link": "ooumph://community/{community_id}/settings",
        "web_link": f"{WEB_BASE_URL}/community/{{community_id}}/settings",
        "priority": "high"
    },
    
    "new_members_joined": {
        "title": "New Members Joined!",
        "body": "{username} joined {community_name}. Say hello!",
        "click_action": "/community/{community_id}/members",
        "deep_link": "ooumph://community/{community_id}/members",
        "web_link": f"{WEB_BASE_URL}/community/{{community_id}}/members",
        "priority": "normal"
    },
    
 
    
    "new_community_post": {
        "title": "New Post Alert!",
        "body": "{username} shared a new post in {community_name}. Join the discussion!",
        "image_url": "{post_image_url}",
        "click_action": "/community/{community_id}/post/{post_id}",
        "deep_link": "ooumph://community/{community_id}/post/{post_id}",
        "web_link": f"{WEB_BASE_URL}/community/{{community_id}}/post/{{post_id}}",
        "priority": "high"
    },
    
    "community_post_reaction": {
        "title": "New Reaction!",
        "body": "{username} reacted to your post in {community_name}. See their response!",
        "click_action": "/community/{community_id}/post/{post_id}",
        "deep_link": "ooumph://community/{community_id}/post/{post_id}",
        "web_link": f"{WEB_BASE_URL}/community/{{community_id}}/post/{{post_id}}",
        "priority": "high"
    },
    
    "community_post_comment": {
        "title": "New Comment!",
        "body": "{username} commented on your post in {community_name}. Reply now!",
        "click_action": "/community/{community_id}/post/{post_id}/comments",
        "deep_link": "ooumph://community/{community_id}/post/{post_id}/comments",
        "web_link": f"{WEB_BASE_URL}/community/{{community_id}}/post/{{post_id}}/comments",
        "priority": "high"
    },
        
    "community_post_mention": {
        "title": "You Were Mentioned!",
        "body": "{username} mentioned you in {community_name}. Check it out!",
        "click_action": "/community/{community_id}/post/{post_id}",
        "deep_link": "ooumph://community/{community_id}/post/{post_id}",
        "web_link": f"{WEB_BASE_URL}/community/{{community_id}}/post/{{post_id}}",
        "priority": "high"
    },
    
    "community_event_reminder": {
        "title": "Upcoming Event!",
        "body": "{event_name} in {community_name} is starting soon. Get ready to join!",
        "click_action": "/community/{community_id}/event/{event_id}",
        "deep_link": "ooumph://community/{community_id}/event/{event_id}",
        "web_link": f"{WEB_BASE_URL}/community/{{community_id}}/event/{{event_id}}",
        "priority": "high"
    },
    
    "community_goal_created": {
        "title": "New Community Goal: {goal_name}!",
        "body": "Get involved now!",
        "click_action": "/community/{community_id}/goal/{goal_id}",
        "deep_link": "ooumph://community/{community_id}/goal/{goal_id}",
        "web_link": f"{WEB_BASE_URL}/community/{{community_id}}/goal/{{goal_id}}",
        "priority": "normal"
    },
    
    "community_achievement_unlocked": {
        "title": "Congrats!",
        "body": "You unlocked {achievement_name} in {community_name}!",
        "image_url": "{achievement_icon}",
        "click_action": "/community/{community_id}/achievements",
        "deep_link": "ooumph://community/{community_id}/achievements",
        "web_link": f"{WEB_BASE_URL}/community/{{community_id}}/achievements",
        "priority": "high"
    },
    
    "community_affiliation_created": {
        "title": "New Partnership!",
        "body": "{community_name} is now affiliated with {affiliation_entity}!",
        "click_action": "/community/{community_id}/affiliations",
        "deep_link": "ooumph://community/{community_id}/affiliations",
        "web_link": f"{WEB_BASE_URL}/community/{{community_id}}/affiliations",
        "priority": "normal"
    },
    
    "user_joined_community": {
        "title": "Welcome {username} to {community_name}!",
        "body": "You are now part of {community_name}.",
        "image_url": "{community_icon}",
        "click_action": "/community/{community_id}",
        "deep_link": "ooumph://community/{community_id}",
        "web_link": f"{WEB_BASE_URL}/community/{{community_id}}",
        "priority": "normal"
    },
    
    # =========================================================================
    # 6. STORY & MEDIA UPLOADS
    # =========================================================================
    
    "new_story_available": {
        "title": "New Story Alert!",
        "body": "{username} just posted a new story. Watch it before it disappears!",
        "image_url": "{story_thumbnail_url}",
        "click_action": "/story/{story_id}",
        "deep_link": "ooumph://story/{story_id}",
        "web_link": f"{WEB_BASE_URL}/story/{{story_id}}",
        "priority": "high"
    },
    
    "story_reaction": {
        "title": "Story Love!",
        "body": "{username} reacted to your story! Tap to see their reaction.",
        "click_action": "/story/{story_id}/reactions",
        "deep_link": "ooumph://story/{story_id}/reactions",
        "web_link": f"{WEB_BASE_URL}/story/{{story_id}}/reactions",
        "priority": "high"
    },
    
    "story_mention": {
        "title": "You Were Mentioned!",
        "body": "{username} mentioned you in their story. Check it out now!",
        "click_action": "/story/{story_id}",
        "deep_link": "ooumph://story/{story_id}",
        "web_link": f"{WEB_BASE_URL}/story/{{story_id}}",
        "priority": "high"
    },
    
  
    
    # =========================================================================
    # 7. NOTIFICATIONS & REQUESTS
    # =========================================================================
    
    "pending_connection_requests": {
        "title": "You Have Requests!",
        "body": "You have {request_count} new connection requests waiting. Approve or decline now!",
        "click_action": "/connections/requests",
        "deep_link": "ooumph://connections/requests",
        "web_link": f"{WEB_BASE_URL}/connections/requests",
        "priority": "high"
    },
    
  
  
    
    # =========================================================================
    # 8. CHAT & MESSAGING
    # =========================================================================
    
    "new_message": {
        "title": "New Message!",
        "body": "{sender_name}: {message_preview}",
        "click_action": "/chat/{chat_id}",
        "deep_link": "ooumph://chat/{chat_id}",
        "web_link": f"{WEB_BASE_URL}/chat/{{chat_id}}",
        "priority": "high"
    },
    
    "unread_messages": {
        "title": "Unread Chats!",
        "body": "You have {unread_count} unread messages waiting. Catch up now!",
        "click_action": "/chat",
        "deep_link": "ooumph://chat",
        "web_link": f"{WEB_BASE_URL}/chat",
        "priority": "normal"
    },
    
    "group_chat_mention": {
        "title": "You Were Mentioned!",
        "body": "{username} mentioned you in {group_name}. See what they said!",
        "click_action": "/chat/{chat_id}",
        "deep_link": "ooumph://chat/{chat_id}",
        "web_link": f"{WEB_BASE_URL}/chat/{{chat_id}}",
        "priority": "high"
    },
    
    "new_group_chat_created": {
        "title": "New Group!",
        "body": "You have been added to {group_name}. Join the conversation!",
        "click_action": "/chat/{chat_id}",
        "deep_link": "ooumph://chat/{chat_id}",
        "web_link": f"{WEB_BASE_URL}/chat/{{chat_id}}",
        "priority": "high"
    },
    
    # =========================================================================
    # 9. DISCOVERY & TRENDING
    # =========================================================================
    
    "trending_topic_matching_interest": {
        "title": "Hot Topic!",
        "body": "{topic_name} is trending in your network. Join the discussion now!",
        "click_action": "/trending/{topic_id}",
        "deep_link": "ooumph://trending/{topic_id}",
        "web_link": f"{WEB_BASE_URL}/trending/{{topic_id}}",
        "priority": "normal"
    },
    
    "new_user_in_network": {
        "title": "New Connection Opportunity!",
        "body": "{username} just joined! Connect and explore shared interests.",
        "click_action": "/profile/{user_id}",
        "deep_link": "ooumph://profile/{user_id}",
        "web_link": f"{WEB_BASE_URL}/profile/{{user_id}}",
        "priority": "normal"
    },
    
    "suggested_community": {
        "title": "Explore More!",
        "body": "You might like {community_name}. Tap to discover new discussions!",
        "image_url": "{community_icon}",
        "click_action": "/community/{community_id}",
        "deep_link": "ooumph://community/{community_id}",
        "web_link": f"{WEB_BASE_URL}/community/{{community_id}}",
        "priority": "normal"
    },
    
    # =========================================================================
    # 10. AUTHENTICATION & SECURITY
    # =========================================================================
    
    "password_reset_success": {
        "title": "Password Reset Successful!",
        "body": "Your password has been changed successfully. You can now log in with your new password.",
        "click_action": "/login",
        "deep_link": "ooumph://login",
        "web_link": f"{WEB_BASE_URL}/login",
        "priority": "high"
    },
    
    "signup_completed": {
        "title": "Welcome to Ooumph, {username}!",
        "body": "Your account has been created successfully. Start exploring and connecting!",
        "click_action": "/home",
        "deep_link": "ooumph://home",
        "web_link": f"{WEB_BASE_URL}/home",
        "priority": "high"
    },

     # =========================================================================
    # 11. opportunity 
    # =========================================================================
        
    "opportunity_comment": {
        "title": "{username} commented on your opportunity",
        "body": "{comment_text}",
        "data": {
            "type": "opportunity_comment",
            "opportunity_id": "{opportunity_id}",
            "comment_id": "{comment_id}",
            "username": "{username}"
        },
        "sound": "default",
        "priority": "high"
    },
    
    "opportunity_comment_reply": {
        "title": "{username} replied to your comment",
        "body": "{comment_text}",
        "data": {
            "type": "opportunity_comment_reply",
            "opportunity_id": "{opportunity_id}",
            "comment_id": "{comment_id}",
            "username": "{username}"
        },
        "sound": "default",
        "priority": "high"
    },
    
    "opportunity_like": {
        "title": "{username} sent a vibe to your opportunity",
        "body": "Received {vibe_name} for {role}",
        "data": {
            "type": "opportunity_like",
            "opportunity_id": "{opportunity_id}",
            "username": "{username}",
            "vibe_name": "{vibe_name}"
        },
        "sound": "default",
        "priority": "default"
    },
    
    "opportunity_share": {
        "title": "{username} shared your opportunity",
        "body": "{role} at {location}",
        "data": {
            "type": "opportunity_share",
            "opportunity_id": "{opportunity_id}",
            "username": "{username}",
            "role": "{role}",
            "location": "{location}"
        },
        "sound": "default",
        "priority": "default"
    },

     "opportunity_application": {
        "title": "{username} applied for your opportunity",
        "body": "New application for {role}",
        "data": {
            "type": "opportunity_application",
            "opportunity_id": "{opportunity_id}",
            "username": "{username}",
            "role": "{role}",
            "room_id": "{room_id}"
        },
        "sound": "default",
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
        dict: Formatted notification with title, body, click_action, deep_link, web_link, priority, and data
        
    Example:
        >>> format_notification(
        ...     "community_achievement_unlocked",
        ...     achievement_name="Super Contributor",
        ...     community_name="TechClub",
        ...     community_id="123",
        ...     achievement_id="achv_987",
        ...     achievement_icon="https://cdn.example.com/achievements/super.png"
        ... )
        {
            "title": "Congrats!",
            "body": "You unlocked Super Contributor in TechClub!",
            "image_url": "https://cdn.example.com/achievements/super.png",
            "click_action": "/community/123/achievements",
            "deep_link": "ooumph://community/123/achievements",
            "web_link": "https://app.ooumph.com/community/123/achievements",
            "priority": "high",
            "data": {
                "achievement_id": "achv_987",
                "achievement_name": "Super Contributor",
                "community_id": "123",
                "community_name": "TechClub",
                "achievement_icon": "https://cdn.example.com/achievements/super.png"
            }
        }
        
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
                # Replace placeholders with values
                formatted[key] = value.format(**{k: v for k, v in template_vars.items() if v is not None})
            except KeyError:
                # If a required placeholder is missing, keep the original
                formatted[key] = value
        else:
            formatted[key] = value
    
    # Remove image_url if it wasn't provided or is still a placeholder
    if 'image_url' in formatted:
        if formatted['image_url'].startswith('{') or not template_vars.get('image_url'):
            del formatted['image_url']
    
    # Add data payload with all variables
    formatted['data'] = template_vars
    
    return formatted
