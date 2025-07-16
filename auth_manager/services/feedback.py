from post_office import mail

def send_feedback_email(user_email, image_url, feedback_message):
    # Define the context to pass to the email template
    context = {
        'image_url': image_url,
        'feedback_message': feedback_message
    }
    
    # Sending the email
    mail.send(
        user_email,
        'noreply@xyz.com',
        template='feedback',
        context=context
    )

    




