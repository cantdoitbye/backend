# opportunity/notification_templates.py

"""
Notification Templates for Opportunity Module.

This file contains notification template definitions for opportunity-related events.
These templates should be added to notification/notification_templates.py in the
main notification module.

Usage: Copy these templates to notification/notification_templates.py
"""

# ========== ADD THESE TO notification/notification_templates.py ==========

OPPORTUNITY_NOTIFICATION_TEMPLATES = {
    # ========== NEW OPPORTUNITY POSTED ==========
    "new_opportunity_posted": {
        "title": "{username} posted a new job opportunity",
        "body": "{role} at {location} ({job_type})",
        "click_action": "opportunity_detail",
        "data_fields": ["username", "role", "location", "job_type", "opportunity_id"],
        "deep_link": "ooumph://opportunity/{opportunity_id}",
        "priority": "normal"
    },
    
    # ========== OPPORTUNITY COMMENT ==========
    "opportunity_comment": {
        "title": "{username} commented on your job posting",
        "body": "{comment_preview}",
        "click_action": "opportunity_detail",
        "data_fields": ["username", "comment_preview", "opportunity_id", "comment_id"],
        "deep_link": "ooumph://opportunity/{opportunity_id}?comment={comment_id}",
        "priority": "high"
    },
    
    # ========== OPPORTUNITY LIKE ==========
    "opportunity_like": {
        "title": "{username} liked your job posting",
        "body": "{role} - {location}",
        "click_action": "opportunity_detail",
        "data_fields": ["username", "role", "location", "opportunity_id"],
        "deep_link": "ooumph://opportunity/{opportunity_id}",
        "priority": "normal"
    },
    
    # ========== OPPORTUNITY SHARE ==========
    "opportunity_share": {
        "title": "{username} shared your job posting",
        "body": "{role} at {location}",
        "click_action": "opportunity_detail",
        "data_fields": ["username", "role", "location", "opportunity_id"],
        "deep_link": "ooumph://opportunity/{opportunity_id}",
        "priority": "normal"
    },
    
    # ========== OPPORTUNITY MENTION ==========
    "opportunity_mention": {
        "title": "{username} mentioned you in a job posting",
        "body": "{role} - {mention_context}",
        "click_action": "opportunity_detail",
        "data_fields": ["username", "role", "mention_context", "opportunity_id"],
        "deep_link": "ooumph://opportunity/{opportunity_id}",
        "priority": "high"
    },
    
    # ========== OPPORTUNITY CLOSED ==========
    "opportunity_closed": {
        "title": "Job opportunity closed",
        "body": "{role} at {location} is no longer accepting applications",
        "click_action": "opportunity_detail",
        "data_fields": ["role", "location", "opportunity_id"],
        "deep_link": "ooumph://opportunity/{opportunity_id}",
        "priority": "low"
    },
    
    # ========== OPPORTUNITY EXPIRING SOON ==========
    "opportunity_expiring_soon": {
        "title": "Your job posting is expiring soon",
        "body": "{role} expires in {days_remaining} days",
        "click_action": "opportunity_detail",
        "data_fields": ["role", "days_remaining", "opportunity_id"],
        "deep_link": "ooumph://opportunity/{opportunity_id}",
        "priority": "normal"
    },
    
    # ========== FUTURE: APPLICATION SUBMITTED ==========
    # Uncomment when implementing applicant tracking
    # "opportunity_application_submitted": {
    #     "title": "New application received",
    #     "body": "{applicant_name} applied for {role}",
    #     "click_action": "application_detail",
    #     "data_fields": ["applicant_name", "role", "opportunity_id", "application_id"],
    #     "deep_link": "ooumph://opportunity/{opportunity_id}/application/{application_id}",
    #     "priority": "high"
    # },
}


# ========== INSTRUCTIONS FOR INTEGRATION ==========
"""
INTEGRATION STEPS:

1. Open notification/notification_templates.py

2. Add the OPPORTUNITY_NOTIFICATION_TEMPLATES dictionary to NOTIFICATION_TEMPLATES:

   NOTIFICATION_TEMPLATES = {
       # ... existing templates ...
       
       # Opportunity notifications
       **OPPORTUNITY_NOTIFICATION_TEMPLATES,
   }

3. That's it! The GlobalNotificationService will now support opportunity events.

USAGE EXAMPLE in mutations:

from notification.global_service import GlobalNotificationService

service = GlobalNotificationService()
service.send(
    event_type="new_opportunity_posted",
    recipients=[{'device_id': '...', 'uid': '...'}],
    username=creator.username,
    role=opportunity.role,
    location=opportunity.location,
    job_type=opportunity.job_type,
    opportunity_id=opportunity.uid
)
"""
