
from django.template.loader import render_to_string
from datetime import datetime

def render_verification_email(first_name, otp_code, user_email):
    context = {
        "userName": first_name,
        "userEmail": user_email,
        "first_name": first_name,
        "otp_code": otp_code,
        "expiration_minutes": 15,
        "company_name": "Ooumph",
        "current_year": datetime.now().year,
        "company_address": "M 2, C 170, Sitapur Rd, SBI Colony, Yojana, Jankipuram, Lucknow, Uttar Pradesh 226021",
        "support_email": "info@ooumph.com",
        "help_center_url": "https://ooumph.com/contact/",
        "privacy_policy_url": "https://ooumph.com/terms-and-conditions/",
        "greeting": "Welcome"
    }

    # print(render_to_string('email_verification.html', context))
    return render_to_string('email_verification.html', context)


def render_forget_email(first_name, otp_code, user_email):
    context = {
        "userName": first_name,
        "userEmail": user_email,
        "first_name": first_name,
        "otp_code": otp_code,
        "expiration_minutes": 15,
        "company_name": "Ooumph",
        "current_year": datetime.now().year,
        "company_address": "M 2, C 170, Sitapur Rd, SBI Colony, Yojana, Jankipuram, Lucknow, Uttar Pradesh 226021",
        "support_email": "info@ooumph.com",
        "help_center_url": "https://ooumph.com/contact/",
        "privacy_policy_url": "https://ooumph.com/terms-and-conditions/",
        "greeting": "Welcome"
    }

    # print(render_to_string('email_forget.html', context))
    return render_to_string('email_forget.html', context)