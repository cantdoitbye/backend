# import os
# import json
# from django.core.management.base import BaseCommand
# from django.template.loader import render_to_string
# from django.template import Template, Context
# import requests


# context = {
#             "userName": "John",
#             "userEmail": "john.doe@example.com",
#             "first_name": "John",
#             "otp_code": "A1B2C3",
#             "expiration_minutes": 15,
#             "company_name": "Ooumph",
#             "current_year": 2025,
#             "company_address": "123 Business Street",
#             "support_email": "support@company.com",
#             "help_center_url": "https://help.company.com",
#             "privacy_policy_url": "https://company.com/privacy",
#             "greeting": "Welcome"
#         }


# class Command(BaseCommand):
#     help = 'Send a test email using NotiSync service'

#     def render_email_template(self, context):
#         return render_to_string('email_verification.html', context)

#     # def generate_email_payload(self, dynamic_vars):
#     #     subject_template = Template(
#     #         "⏣ {{greeting}} {{userName}}, Initiate CyberSync Protocol [2024.1]"
#     #     )
#     #     rendered_subject = subject_template.render(Context(dynamic_vars))
#     #     rendered_html = self.render_email_template(dynamic_vars)

#     #     return {
#     #         "receiver": {
#     #             "name": dynamic_vars.get("userName", "User"),
#     #             "email": dynamic_vars.get("userEmail", "example@example.com")
#     #         },
#     #         "subject": rendered_subject,
#     #         "raw_html": rendered_html,
#     #         "template_type": "Dynamic",
#     #         "dynamic_vars": dynamic_vars
#     #     }

#     # def send_notisync_email(self, api_url, api_key, dynamic_vars):
#     #     payload = self.generate_email_payload(dynamic_vars)

#     #     headers = {
#     #         "Content-Type": "application/json",
#     #         "Authorization": f"Bearer {api_key}",
#     #         "X-CyberSync-Version": "2024.1"
#     #     }

#     #     try:
#     #         response = requests.post(api_url, data=json.dumps(payload, indent=2), headers=headers, timeout=10)
#     #         response.raise_for_status()
#     #         return response.json()
#     #     except requests.exceptions.RequestException as e:
#     #         error_msg = f"Email API Error: {str(e)}"
#     #         if hasattr(e, 'response') and e.response:
#     #             error_msg += f" | Status: {e.response.status_code}"
#     #             if e.response.text:
#     #                 error_msg += f" | Response: {e.response.text[:200]}"
#     #         raise Exception(error_msg)

#     # def handle(self, *args, **kwargs):
#     #     api_url = "https://api.notisync.dev/api/v1/send"
#     #     api_key = "your_api_key_here"  # Replace with actual key

    

#         # Optional: Print rendered template to debug
#     print(render_email_template(context))

#         # try:
#         #     response = self.send_notisync_email(api_url, api_key, context)
#         #     self.stdout.write(self.style.SUCCESS('Email sent successfully!'))
#         #     self.stdout.write(json.dumps(response, indent=2))
#         # except Exception as e:
#         #     self.stdout.write(self.style.ERROR(f'Failed to send email: {e}'))

import os
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string

class Command(BaseCommand):
    help = 'Render and print the email_verification.html with context'

    def handle(self, *args, **kwargs):
        context = {
            "userName": "John",
            "userEmail": "john.doe@example.com",
            "first_name": "John",
            "otp_code": "A1B2C3",
            "expiration_minutes": 15,
            "company_name": "Ooumph",
            "current_year": 2025,
            "company_address": "123 Business Street",
            "support_email": "support@company.com",
            "help_center_url": "https://help.company.com",
            "privacy_policy_url": "https://company.com/privacy",
            "greeting": "Welcome"
        }

        rendered_html = render_to_string('email_verification.html', context)
        self.stdout.write(rendered_html)
