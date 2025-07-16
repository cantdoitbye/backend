import re
from graphql import GraphQLError
from auth_manager.validators.rules.regex_patterns import PASSWORD_PATTERN

# def validate_password(password):
#     """
#     Validates a password for the following:
#     - At least 8 characters
#     - At least one lowercase letter
#     - At least one uppercase letter
#     - At least one digit
#     - At least one special character
#     """
#     print("Password Pattern:------------", PASSWORD_PATTERN)
#     print("password",password)
#     if not re.match(PASSWORD_PATTERN, password):
#         raise GraphQLError(
#             "Invalid password. Password must be at least 8 characters long, "
#             "contain at least one lowercase letter, one uppercase letter, one digit, "
#             "and one special character."
#         )
#     return True



COMMON_PASSWORDS = [
    "password123", "123456", "123456789", "qwerty", "abc123", "password1", "12345", "letmein", "welcome", "admin"
]

# Password Validation Function
def validate_password(password):
    if len(password) < 6 or len(password) > 50:
        raise ValueError("Password must be at least 6 characters long and no more than 50 characters.")
    if password in COMMON_PASSWORDS:
        raise ValueError("Password is too common or easily guessable.")
    if not re.match(PASSWORD_PATTERN, password):
        # Check for specific reasons why it failed:
        if not re.search(r'[a-z]', password):  # Lowercase missing
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r'[A-Z]', password):  # Uppercase missing
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r'\d', password):     # Digit missing
            raise ValueError("Password must contain at least one digit.")
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:"\'<>.,?/|\\~`]', password):  # Special char missing
            raise ValueError("Password must contain at least one special character.")
        if ' ' in password:  # Space check
            raise ValueError("Password must not contain spaces.")
        # Handle repeated or sequential characters
        if re.search(r"(.)\1{2,}", password):  # Repeated characters check
            raise ValueError("Password must not contain repeated characters.")
        if re.search(r"(012|123|234|345|456|567|678|789|890|abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)", password):  # Sequential characters check
            raise ValueError("Password must not contain sequential characters.")
    return True

