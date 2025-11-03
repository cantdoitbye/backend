import re
from auth_manager.validators.rules.regex_patterns import (
    EXPERIENCE_COMPANY_NAME_PATTERN,
    EXPERIENCE_TITLE_PATTERN,
    EXPERIENCE_DESCRIPTION_PATTERN,
)


def validate_experience_input(company_name, title, description):
    """
    Validates the create experience form input with three fields: Company Name, Title, and Description.
    
    Args:
        company_name (str): Company/Organization/Institution name
        title (str): Job title/Position/Role
        description (str): Work summary/Responsibilities/Experience details
    
    Returns:
        dict: Validation result with format:
            - {"valid": false, "error": "<reason>"} if invalid
            - {"valid": true, "message": "Experience input is valid."} if valid
    
    Validation Rules:
        Company Name (From/Source/Institution):
        - Must be a string
        - Minimum length: 2 characters
        - Maximum length: 100 characters
        - Should not contain only symbols or numbers (must have at least one letter)
        - Should represent a valid company, organization, or institution name
        
        Title (What/Experience/Learning):
        - Must be a string
        - Minimum length: 2 characters
        - Maximum length: 100 characters
        - Should describe the job title, position, or role held
        
        Description:
        - Must be a string
        - Minimum length: 5 characters
        - Maximum length: 200 characters
        - Should summarize the key work, responsibilities, or experience details
    """
    
    # Validate Company Name
    if not isinstance(company_name, str):
        return {"valid": False, "error": "companyName must be a string."}
    
    # Check if Company Name is empty or whitespace
    if not company_name or not company_name.strip():
        return {"valid": False, "error": "companyName field must not be empty."}
    
    # Strip whitespace for length validation
    company_name_stripped = company_name.strip()
    
    # Check minimum length
    if len(company_name_stripped) < 2:
        return {"valid": False, "error": "companyName must be at least 2 characters long."}
    
    # Check maximum length
    if len(company_name_stripped) > 100:
        return {"valid": False, "error": "companyName must not exceed 100 characters."}
    
    # Check if Company Name contains only numbers or symbols (must have at least one letter)
    if not re.match(EXPERIENCE_COMPANY_NAME_PATTERN, company_name_stripped):
        return {"valid": False, "error": "companyName should not contain only numbers or symbols."}
    
    # Validate Title
    if not isinstance(title, str):
        return {"valid": False, "error": "title must be a string."}
    
    # Check if Title is empty or whitespace
    if not title or not title.strip():
        return {"valid": False, "error": "title field must not be empty."}
    
    # Strip whitespace for length validation
    title_stripped = title.strip()
    
    # Check minimum length
    if len(title_stripped) < 2:
        return {"valid": False, "error": "title must be at least 2 characters long."}
    
    # Check maximum length
    if len(title_stripped) > 100:
        return {"valid": False, "error": "title must not exceed 100 characters."}
    
    # Check if Title matches the pattern
    if not re.match(EXPERIENCE_TITLE_PATTERN, title_stripped):
        return {"valid": False, "error": "title contains invalid characters."}
    
    # Validate Description
    if not isinstance(description, str):
        return {"valid": False, "error": "description must be a string."}
    
    # Check if Description is empty or whitespace
    if not description or not description.strip():
        return {"valid": False, "error": "description field must not be empty."}
    
    # Strip whitespace for length validation
    description_stripped = description.strip()
    
    # Check minimum length (note: 5 characters, not 2)
    if len(description_stripped) < 5:
        return {"valid": False, "error": "description must be at least 5 characters long."}
    
    # Check maximum length
    if len(description_stripped) > 200:
        return {"valid": False, "error": "description must not exceed 200 characters."}
    
    # Check if Description matches the pattern
    if not re.match(EXPERIENCE_DESCRIPTION_PATTERN, description_stripped):
        return {"valid": False, "error": "description contains invalid characters."}
    
    # If all validations pass
    return {"valid": True, "message": "Experience input is valid."}


def validate_company_name(company_name):
    """
    Validates only the Company Name field.
    
    Args:
        company_name (str): Company/Organization/Institution name
    
    Returns:
        bool: True if valid
    
    Raises:
        ValueError: If validation fails with detailed error message
    """
    if not isinstance(company_name, str):
        raise ValueError("companyName must be a string.")
    
    if not company_name or not company_name.strip():
        raise ValueError("companyName field must not be empty.")
    
    company_name_stripped = company_name.strip()
    
    if len(company_name_stripped) < 2:
        raise ValueError("companyName must be at least 2 characters long.")
    
    if len(company_name_stripped) > 100:
        raise ValueError("companyName must not exceed 100 characters.")
    
    if not re.match(EXPERIENCE_COMPANY_NAME_PATTERN, company_name_stripped):
        raise ValueError("companyName should not contain only numbers or symbols.")
    
    return True


def validate_title(title):
    """
    Validates only the Title field.
    
    Args:
        title (str): Job title/Position/Role
    
    Returns:
        bool: True if valid
    
    Raises:
        ValueError: If validation fails with detailed error message
    """
    if not isinstance(title, str):
        raise ValueError("title must be a string.")
    
    if not title or not title.strip():
        raise ValueError("title field must not be empty.")
    
    title_stripped = title.strip()
    
    if len(title_stripped) < 2:
        raise ValueError("title must be at least 2 characters long.")
    
    if len(title_stripped) > 100:
        raise ValueError("title must not exceed 100 characters.")
    
    if not re.match(EXPERIENCE_TITLE_PATTERN, title_stripped):
        raise ValueError("title contains invalid characters.")
    
    return True


def validate_description(description):
    """
    Validates only the Description field.
    
    Args:
        description (str): Work summary/Responsibilities/Experience details
    
    Returns:
        bool: True if valid
    
    Raises:
        ValueError: If validation fails with detailed error message
    """
    if not isinstance(description, str):
        raise ValueError("description must be a string.")
    
    if not description or not description.strip():
        raise ValueError("description field must not be empty.")
    
    description_stripped = description.strip()
    
    if len(description_stripped) < 5:
        raise ValueError("description must be at least 5 characters long.")
    
    if len(description_stripped) > 200:
        raise ValueError("description must not exceed 200 characters.")
    
    if not re.match(EXPERIENCE_DESCRIPTION_PATTERN, description_stripped):
        raise ValueError("description contains invalid characters.")
    
    return True

