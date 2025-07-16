from auth_manager.validators.rules.email_validation import validate_email
from auth_manager.validators.rules.password_validation import validate_password

def validate_create_user_inputs(email, password):
    """
    Validates user inputs for creating a user.
    """
    validate_email(email)
    validate_password(password)
    return True
