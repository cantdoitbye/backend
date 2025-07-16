import re
from graphql import GraphQLError
from auth_manager.validators.rules.regex_patterns import EMAIL_PATTERN

def validate_email(email):
    """
    Validates an email address.
    """
    if not re.match(EMAIL_PATTERN, email):
        raise GraphQLError("Invalid email address.")
    return True