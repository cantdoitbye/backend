from post_office import mail
from auth_manager.enums.otp_purpose_enum import OtpPurposeEnum
def send_otp_email(user_email, otp_code,purpose):

    if purpose==OtpPurposeEnum.EMAIL_VERIFICATION.value:
        mail.send(
            user_email,
            'noreply@ooumph.com',
            template='otp',
            context={'otp_code': otp_code}
        )
    elif purpose == OtpPurposeEnum.FORGET_PASSWORD.value:

        mail.send(
            user_email,
            'noreply@ooumph.com',
            template='forget_password',
            context={'otp_code': otp_code}
        )




# def send_otp_email(user_email, otp_code):
#     subject = "Your OTP Code"
#     html_content = f"""
#     <!DOCTYPE html>
#     <html>
#     <head>
#         <title>Your OTP Code</title>
#     </head>
#     <body>
#         <h1>Your OTP Code</h1>
#         <p>Your OTP code is {otp_code}</p>
#     </body>
#     </html>
#     """
#     text_content = f"Your OTP code is {otp_code}"

#     mail.send(
#         user_email,
#         'noreply@xyz.com',
#         subject=subject,
#         message=text_content,
#         html_message=html_content
#     )
