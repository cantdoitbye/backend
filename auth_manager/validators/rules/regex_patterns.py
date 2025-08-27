# These are reference regular expressions. After the validation for the authentication model is completed, they will be optimized for use in Django models or directly in a Neo4j model, if supported.

# Regex pattern for validating email addresses
EMAIL_PATTERN = r'^(?!.*\.\.)[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'


# PASSWORD_PATTERN = (
#     r'^(?=.*[a-z])'  # At least one lowercase letter
#     r'(?=.*[A-Z])'  # At least one uppercase letter
#     r'(?=.*\d)'  # At least one digit
#     r'(?=.*[@$!%*#?&])'  # At least one special character
#     r'[A-Za-z\d@$!%*#?&]{8,16}$'  # Minimum 8 characters
# )


PASSWORD_PATTERN = (
    r'^(?=.*[a-z])'                # At least one lowercase letter
    r'(?=.*[A-Z])'                 # At least one uppercase letter
    r'(?=.*\d)'                    # At least one digit
    r'(?=.*[!@#$%^&*()_+\-=\[\]{};:"\'<>.,?/|\\~`])' # At least one special character
    r'(?!.*(.)\1{2,})'             # No repeated characters
    r'(?!.*(?:012|123|234|345|456|567|678|789|890|abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz))'  # No sequential characters
    r'(?=\S+$)'                    # No spaces
    r'.{8,50}$'                    # Between 8 and 50 characters long
)




# Matches usernames containing alphanumeric characters and underscores,
# with a length between 6 and 10 characters.
USERNAME_PATTERN = r"^[a-zA-Z0-9_]{3,9}$"
# USERNAME_PATTERN = r"^[a-zA-Z0-9_]{4,10}$"

# Matches job titles of any characters (letters, numbers, or special characters),
# with a length between 3 and 24 characters.
JOB_TITLE_PATTERN = r"^.{3,24}$"


# Matches descriptions of any characters (letters, numbers, or special characters),
# with a length between 12 and 80 characters.
DESCRIPTION_PATTERN = r"^.{12,80}$"


# Detects HTML tags, such as <b>, <div>, <script>, etc.
HTML_PATTERN = r"<[^>]+>"

# Validates that the input meets the criteria for a valid first name:
VALID_FIRST_NAME_PATTERN = r'^[A-Za-z]{2,30}$'


VALID_LAST_NAME_PATTERN = r"^[A-Za-zÀ-ÖØ-öø-ÿ' -]{2,50}$"


ALLOWED_GENDER_VALUES = {"male", "female", "non-binary", "agender"}


BIO_PATTERN = r"^(?!.*<[^>]+>)[A-Za-z0-9\s!#.,'\"-🌲💻\u00C0-\u017F]{20,500}$"


DESIGNATION_PATTERN = r"^[A-Za-z0-9\s]{1,50}$"


CONTACt_NUMBER_PATTERN = r"^\+?[0-9\s\-().]{10,15}$"


