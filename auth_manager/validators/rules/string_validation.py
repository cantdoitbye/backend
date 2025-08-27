import re
from graphql import GraphQLError
from auth_manager.validators.rules.regex_patterns import (
    USERNAME_PATTERN,
    JOB_TITLE_PATTERN,
    DESCRIPTION_PATTERN,
    HTML_PATTERN,
    VALID_FIRST_NAME_PATTERN,
    VALID_LAST_NAME_PATTERN,
    ALLOWED_GENDER_VALUES,
    BIO_PATTERN,
    DESIGNATION_PATTERN,
    CONTACt_NUMBER_PATTERN,
)

def validate_username(username):
    """
    Validates that the username is between 3 and 10 characters long.
    """
    if not re.match(USERNAME_PATTERN, username):
        raise GraphQLError("Invalid username. Must be between 6 and 10 characters.")
    return True


def validate_job_title(title):
    """
    Validates that the job title is between 3 and 24 characters long.
    """
    if not re.match(JOB_TITLE_PATTERN, title):
        raise GraphQLError("Invalid job title. Must be between 3 and 24 characters.")
    return True


def validate_description(description):
    """
    Validates that the description is between 12 and 80 characters long.
    """
    if not re.match(DESCRIPTION_PATTERN, description):
        raise GraphQLError("Invalid description. Must be between 12 and 80 characters.")
    return True


def validate_no_html(input_string):
    """
    Validates that the input does not contain HTML tags or improper string content.

    Args:
        input_string (str): The string to validate.

    Raises:
        GraphQLError: If the input contains HTML or is not a valid string.

    Returns:
        bool: True if the input is valid and does not contain HTML.
    """
    if not isinstance(input_string, str):
        raise GraphQLError("Invalid input. Expected a proper string.")
    
    # Check for HTML content using the imported regex pattern
    if re.search(HTML_PATTERN, input_string):
        raise GraphQLError("Invalid input. HTML content is not allowed.")

    return True



def validate_first_name(input_string):
    """
    Validates that the input meets the criteria for a valid first name:
    - Must only contain letters (A-Z, a-z).
    - Must be between 2 and 30 characters.
    - Must not contain HTML tags, numbers, spaces, or special characters.

    Args:
        input_string (str): The string to validate.

    Raises:
        GraphQLError: If the input is invalid.

    Returns:
        bool: True if the input is valid.
    """
    if not isinstance(input_string, str):
        raise GraphQLError("Invalid input. Expected a proper string.")

    # Check for valid first name pattern
    if not re.fullmatch(VALID_FIRST_NAME_PATTERN, input_string):
        raise GraphQLError(
            "Invalid input. First Name must be between 2 and 30 characters "
            "and contain only letters (A-Z, a-z)."
        )

    return True


def validate_last_name(input_string):
    """
    Validates that the input meets the criteria for a valid last name:
    - Must be between 2 and 50 characters.
    - Can contain letters (A-Z, a-z, Unicode characters with diacritics).
    - Allows spaces, hyphens, and apostrophes but no other special characters.
    - Should not consist only of whitespace.

    Args:
        input_string (str): The string to validate.

    Raises:
        GraphQLError: If the input is invalid.

    Returns:
        bool: True if the input is valid.
    """
    if not isinstance(input_string, str):
        raise GraphQLError("Invalid input. Expected a proper string.")

    # Check for whitespace-only input
    if input_string.strip() == "":
        raise GraphQLError("Invalid input. Last Name must not be empty or consist only of whitespace.")

    # Validate against regex pattern
    if not re.fullmatch(VALID_LAST_NAME_PATTERN, input_string):
        raise GraphQLError(
            "Invalid input. Last Name must be between 2 and 50 characters and can only contain letters, "
            "spaces, hyphens, or apostrophes."
        )

    return True




def validate_gender(input_string, is_optional=False):
    """
    Validates that the input meets the criteria for a valid gender:
    - Must be one of the predefined values (e.g., Male, Female, Non-Binary, Agender).
    - Must not contain special characters or numbers.
    - Must be case-insensitive.
    - Optionally, can be left empty if specified as optional.

    Args:
        input_string (str): The string to validate.
        is_optional (bool): Whether the gender field is optional.

    Raises:
        GraphQLError: If the input is invalid.

    Returns:
        bool: True if the input is valid.
    """
    if not isinstance(input_string, str):
        raise GraphQLError("Invalid input. Expected a proper string.")

    # Handle optional gender field
    if is_optional and input_string.strip() == "":
        return True  # Optional field can be empty

    # Check for empty string
    if input_string.strip() == "":
        raise GraphQLError("Invalid input. Gender field must not be empty.")

    # Normalize input to lowercase for case-insensitivity
    normalized_input = input_string.strip().lower()

    # Validate against predefined gender values
    if normalized_input not in ALLOWED_GENDER_VALUES:
        raise GraphQLError(
            f"Invalid input. Gender must be one of the following: {', '.join(ALLOWED_GENDER_VALUES)}."
        )

    return True




def validate_bio(input_string):
    """
    Validates the bio input field based on the following criteria:
    - Must meet minimum and maximum length requirements.
    - Should allow valid special characters and Unicode (e.g., emojis).
    - Should reject HTML tags to prevent XSS attacks.
    - Should reject disallowed punctuation (e.g., @).

    Args:
        input_string (str): The bio input to validate.

    Raises:
        GraphQLError: If the input is invalid.

    Returns:
        bool: True if the input is valid.
    """

    # Explanation of the pattern:
    # (?!.*<[^>]+>)     : Rejects HTML tags (negative lookahead).
    # [A-Za-z0-9\s!#.,'\"-🌲💻\u00C0-\u017F] : Allows alphanumeric, spaces, valid special characters, emojis, and Unicode.
    # {20,500}          : Enforces minimum length of 20 and maximum length of 500 characters.

    # Validate using regex
    if not re.fullmatch(BIO_PATTERN, input_string):
        raise GraphQLError(
            "Invalid input. Bio must be between 20 and 500 characters long, "
            "must not contain HTML tags, and can only include letters, numbers, "
            "spaces, valid special characters, emojis, and Unicode characters."
        )

    return True



def validate_designation(input_string, max_length=50):
    """
    Validates the designation field based on the following criteria:
    - Must not be empty.
    - Must only contain letters, spaces, and (if applicable) numbers in specific formats.
    - Must be at least 1 character long and not exceed the maximum length.
    - Should reject invalid special characters.
    - Case-insensitivity is implicit as all case formats are valid.

    Args:
        input_string (str): The designation input to validate.
        max_length (int): Maximum allowed length for the designation.

    Raises:
        GraphQLError: If the input is invalid.

    Returns:
        bool: True if the input is valid.
    """

    # Check for empty designation
    if not input_string.strip():
        raise GraphQLError("Invalid input. Designation field must not be empty.")

    # Check length constraints
    if len(input_string) > max_length:
        raise GraphQLError(f"Invalid input. Designation must not exceed {max_length} characters.")

    # Validate against the regex pattern
    if not re.fullmatch(DESIGNATION_PATTERN, input_string):
        raise GraphQLError(
            "Invalid input. Designation can only contain letters, spaces, and (if applicable) numbers."
        )

    return True




def validate_contact_number(input_string):
    """
    Validates the contact number field based on the following criteria:
    - Must not be empty.
    - Must follow valid local or international formats.
    - Allows country codes, spaces, parentheses, dashes, and periods.
    - Rejects input with invalid characters or incorrect lengths.

    Args:
        input_string (str): The contact number input to validate.

    Raises:
        GraphQLError: If the input is invalid.

    Returns:
        bool: True if the input is valid.
    """

    # Check for empty input
    if not input_string.strip():
        raise GraphQLError("Invalid input. Contact number field must not be empty.")

    # Validate against the regex pattern
    if not re.fullmatch(CONTACt_NUMBER_PATTERN, input_string):
        raise GraphQLError(
            "Invalid input. Contact number must be between 10 and 15 digits, "
            "and may include a country code, spaces, dashes, periods, or parentheses."
        )

    # Check for invalid characters (only numeric and allowed formatting characters)
    sanitized_input = re.sub(r"[^\d]", "", input_string)
    if not sanitized_input.isdigit():
        raise GraphQLError(
            "Invalid input. Contact number must only contain numeric characters after removing formatting."
        )

    # Check length of numeric content
    if len(sanitized_input) < 10 or len(sanitized_input) > 15:
        raise GraphQLError("Invalid input. Contact number must be between 10 and 15 digits.")

    return True