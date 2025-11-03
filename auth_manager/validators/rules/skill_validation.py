import re
from auth_manager.validators.rules.regex_patterns import (
    SKILL_FROM_PATTERN,
    SKILL_WHAT_PATTERN,
)


def validate_skill_input(from_field, what_field):
    """
    Validates the create skill form input with two fields: From and What.
    
    Args:
        from_field (str): Source/Institution field
        what_field (str): Skill/Expertise field
    
    Returns:
        dict: Validation result with format:
            - {"valid": false, "error": "<reason>"} if invalid
            - {"valid": true, "message": "Skill input is valid."} if valid
    
    Validation Rules:
        From (Source/Institution):
        - Must be a string
        - Minimum length: 2 characters
        - Maximum length: 100 characters
        - Should not contain only numbers or symbols (must have at least one letter)
        
        What (Skill/Expertise):
        - Must be a string
        - Minimum length: 2 characters
        - Maximum length: 100 characters
        - Should describe a real skill, expertise, or knowledge area
    """
    
    # Validate From field
    if not isinstance(from_field, str):
        return {"valid": False, "error": "From must be a string."}
    
    # Check if From is empty or whitespace
    if not from_field or not from_field.strip():
        return {"valid": False, "error": "From field must not be empty."}
    
    # Strip whitespace for length validation
    from_stripped = from_field.strip()
    
    # Check minimum length
    if len(from_stripped) < 2:
        return {"valid": False, "error": "From must be at least 2 characters long."}
    
    # Check maximum length
    if len(from_stripped) > 100:
        return {"valid": False, "error": "From must not exceed 100 characters."}
    
    # Check if From contains only numbers or symbols (must have at least one letter)
    if not re.match(SKILL_FROM_PATTERN, from_stripped):
        return {"valid": False, "error": "From should not contain only numbers or symbols."}
    
    # Validate What field
    if not isinstance(what_field, str):
        return {"valid": False, "error": "What must be a string."}
    
    # Check if What is empty or whitespace
    if not what_field or not what_field.strip():
        return {"valid": False, "error": "What field must not be empty."}
    
    # Strip whitespace for length validation
    what_stripped = what_field.strip()
    
    # Check minimum length
    if len(what_stripped) < 2:
        return {"valid": False, "error": "What must be at least 2 characters long."}
    
    # Check maximum length
    if len(what_stripped) > 100:
        return {"valid": False, "error": "What must not exceed 100 characters."}
    
    # Check if What matches the pattern
    if not re.match(SKILL_WHAT_PATTERN, what_stripped):
        return {"valid": False, "error": "What contains invalid characters."}
    
    # If all validations pass
    return {"valid": True, "message": "Skill input is valid."}


def validate_skill_from(from_field):
    """
    Validates only the From (Source/Institution) field.
    
    Args:
        from_field (str): Source/Institution field
    
    Returns:
        bool: True if valid
    
    Raises:
        ValueError: If validation fails with detailed error message
    """
    if not isinstance(from_field, str):
        raise ValueError("From must be a string.")
    
    if not from_field or not from_field.strip():
        raise ValueError("From field must not be empty.")
    
    from_stripped = from_field.strip()
    
    if len(from_stripped) < 2:
        raise ValueError("From must be at least 2 characters long.")
    
    if len(from_stripped) > 100:
        raise ValueError("From must not exceed 100 characters.")
    
    if not re.match(SKILL_FROM_PATTERN, from_stripped):
        raise ValueError("From should not contain only numbers or symbols.")
    
    return True


def validate_skill_what(what_field):
    """
    Validates only the What (Skill/Expertise) field.
    
    Args:
        what_field (str): Skill/Expertise field
    
    Returns:
        bool: True if valid
    
    Raises:
        ValueError: If validation fails with detailed error message
    """
    if not isinstance(what_field, str):
        raise ValueError("What must be a string.")
    
    if not what_field or not what_field.strip():
        raise ValueError("What field must not be empty.")
    
    what_stripped = what_field.strip()
    
    if len(what_stripped) < 2:
        raise ValueError("What must be at least 2 characters long.")
    
    if len(what_stripped) > 100:
        raise ValueError("What must not exceed 100 characters.")
    
    if not re.match(SKILL_WHAT_PATTERN, what_stripped):
        raise ValueError("What contains invalid characters.")
    
    return True

