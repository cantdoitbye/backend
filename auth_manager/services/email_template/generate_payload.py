import json
import requests
from auth_manager.services.email_template.email_utility import render_verification_email,render_forget_email


def send_rendered_email(api_url, api_key, first_name, otp_code, user_email):
    rendered_html = render_verification_email(first_name, otp_code, user_email)

    dynamic_vars = {
        "userName": first_name,
        "userEmail": user_email,
        "userCount": 12500,
        "storageStats": 4.2,
        "countdownTimer": "48:00:00",
        "dashboardLink": "https://ooumphmedia.com/dashboard",
        "social": {
            "twitter": "#",
            "discord": "#",
            "telegram": "#"
        }
    }

    payload = {
        "receiver": {
            "name": dynamic_vars["userName"],
            "email": dynamic_vars["userEmail"]
        },
        "subject": f"⏣ Welcome {dynamic_vars['userName']}",
        "raw_html": rendered_html,
        "template_type": "Dynamic",
        "dynamic_vars": dynamic_vars
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "X-CyberSync-Version": "2024.1"
    }

    try:
        response = requests.post(api_url, data=json.dumps(payload), headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending email: {e}")
        return None

def send_rendered_forget_email(api_url, api_key, first_name, otp_code, user_email):
    rendered_html = render_forget_email(first_name, otp_code, user_email)

    dynamic_vars = {
        "userName": first_name,
        "userEmail": user_email,
        "userCount": 12500,
        "storageStats": 4.2,
        "countdownTimer": "48:00:00",
        "dashboardLink": "https://ooumphmedia.com/dashboard",
        "social": {
            "twitter": "#",
            "discord": "#",
            "telegram": "#"
        }
    }

    payload = {
        "receiver": {
            "name": dynamic_vars["userName"],
            "email": dynamic_vars["userEmail"]
        },
        "subject": f"⏣ Welcome {dynamic_vars['userName']}",
        "raw_html": rendered_html,
        "template_type": "Dynamic",
        "dynamic_vars": dynamic_vars
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "X-CyberSync-Version": "2024.1"
    }

    try:
        response = requests.post(api_url, data=json.dumps(payload), headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending email: {e}")
        return None