# These are reference regular expressions. After the validation for the authentication model is completed, they will be optimized for use in Django models or directly in a Neo4j model, if supported.

import re

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
# with a length between 3 and 9 characters.
USERNAME_PATTERN = r"^[a-zA-Z0-9_]{6,15}$"

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


# Bio pattern: allows letters, numbers, spaces, emojis, and common punctuation
# Blocks HTML tags for security
# Common punctuation: !"#$%&'()*+,-./:;<=>?@[\]^_`{|}~
BIO_PATTERN = re.compile(
    r"^(?!.*<[^>]+>)[A-Za-z0-9\s!\"#$%&'()*+,\-./:;<=>?@\[\\\]^_`{|}~"
    r"\u2600-\u26FF"  # Miscellaneous Symbols
    r"\u2700-\u27BF"  # Dingbats
    r"\u200D"  # Zero-Width Joiner (ZWJ) - for complex emoji sequences
    r"\uFE00-\uFE0F"  # Variation Selectors (VS15, VS16) - for emoji variations
    r"\u20E3"  # Combining Enclosing Keycap - for keycap emojis like 2️⃣
    r"\U0001F300-\U0001F5FF"  # Miscellaneous Symbols and Pictographs
    r"\U0001F600-\U0001F64F"  # Emoticons
    r"\U0001F680-\U0001F6FF"  # Transport and Map Symbols
    r"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
    r"\U0001FA00-\U0001FA6F"  # Chess Symbols
    r"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
    r"]{1,200}$",
    re.UNICODE
)


# Designation pattern: allows letters, numbers, spaces, emojis, and common punctuation
# Common punctuation: !"#$%&'()*+,-./:;<=>?@[\]^_`{|}~
DESIGNATION_PATTERN = re.compile(
    r"^[A-Za-z0-9\s!\"#$%&'()*+,\-./:;<=>?@\[\\\]^_`{|}~"
    r"\u2600-\u26FF"  # Miscellaneous Symbols
    r"\u2700-\u27BF"  # Dingbats
    r"\u200D"  # Zero-Width Joiner (ZWJ) - for complex emoji sequences
    r"\uFE00-\uFE0F"  # Variation Selectors (VS15, VS16) - for emoji variations
    r"\u20E3"  # Combining Enclosing Keycap - for keycap emojis like 2️⃣
    r"\U0001F300-\U0001F5FF"  # Miscellaneous Symbols and Pictographs
    r"\U0001F600-\U0001F64F"  # Emoticons
    r"\U0001F680-\U0001F6FF"  # Transport and Map Symbols
    r"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
    r"\U0001FA00-\U0001FA6F"  # Chess Symbols
    r"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
    r"]{2,100}$",
    re.UNICODE
)


CONTACt_NUMBER_PATTERN = r"^\+?[0-9\s\-().]{10,15}$"


# Skill validation patterns
# Matches strings that are not only numbers or symbols (must contain at least one letter)
SKILL_FROM_PATTERN = r"^(?=.*[A-Za-z])[\w\s\-.'&,()]{2,100}$"
SKILL_WHAT_PATTERN = r"^[\w\s\-.'&,()]{2,100}$"


# Education validation patterns
# School name must contain at least one letter and not be only symbols/numbers
EDUCATION_SCHOOL_NAME_PATTERN = r"^(?=.*[A-Za-z])[\w\s\-.'&,()]{2,100}$"
# Degree pattern allows various degree formats
EDUCATION_DEGREE_PATTERN = r"^[\w\s\-.'&,()]{2,100}$"
# Field of study pattern
EDUCATION_FIELD_OF_STUDY_PATTERN = r"^[\w\s\-.'&,()]{2,50}$"


# Experience validation patterns
# Company name must contain at least one letter and not be only symbols/numbers
EXPERIENCE_COMPANY_NAME_PATTERN = r"^(?=.*[A-Za-z])[\w\s\-.'&,()]{2,100}$"
# Title pattern for job title/position/role
EXPERIENCE_TITLE_PATTERN = r"^[\w\s\-.'&,()]{2,100}$"
# Description pattern (5-200 characters)
EXPERIENCE_DESCRIPTION_PATTERN = r"^[\w\s\-.'&,()!@#$%^*+=:;\"?/<>]{5,200}$"


# Story validation patterns (1-50 or 1-100 characters, very permissive)
# Story title pattern (1-50 characters)
STORY_TITLE_PATTERN = r"^.{1,50}$"
# Story content pattern (1-50 characters)
STORY_CONTENT_PATTERN = r"^.{1,50}$"
# Story captions pattern (1-100 characters)
STORY_CAPTIONS_PATTERN = r"^.{1,100}$"


