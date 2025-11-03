import re
from auth_manager.validators.rules.regex_patterns import (
    EDUCATION_SCHOOL_NAME_PATTERN,
    EDUCATION_DEGREE_PATTERN,
    EDUCATION_FIELD_OF_STUDY_PATTERN,
)


def validate_education_input(school_name, degree, field_of_study):
    """
    Validates the create education form input with three fields: School Name, Degree, and Field of Study.
    
    Args:
        school_name (str): School/Institution name
        degree (str): Degree/Diploma/Learning title
        field_of_study (str): Subject/Specialization/Study area
    
    Returns:
        dict: Validation result with format:
            - {"valid": false, "error": "<reason>"} if invalid
            - {"valid": true, "message": "Education input is valid."} if valid
    
    Validation Rules:
        School Name (From/Source/Institution):
        - Must be a string
        - Minimum length: 2 characters
        - Maximum length: 100 characters
        - Should not contain only symbols or numbers (must have at least one letter)
        - Should represent an educational institution
        
        Degree (What/Experience/Learning):
        - Must be a string
        - Minimum length: 2 characters
        - Maximum length: 100 characters
        - Should represent a valid academic degree, diploma, or learning title
        
        Field of Study:
        - Must be a string
        - Minimum length: 2 characters
        - Maximum length: 50 characters
        - Should describe a subject, specialization, or study area
    """
    
    # Validate School Name
    if not isinstance(school_name, str):
        return {"valid": False, "error": "schoolName must be a string."}
    
    # Check if School Name is empty or whitespace
    if not school_name or not school_name.strip():
        return {"valid": False, "error": "schoolName field must not be empty."}
    
    # Strip whitespace for length validation
    school_name_stripped = school_name.strip()
    
    # Check minimum length
    if len(school_name_stripped) < 2:
        return {"valid": False, "error": "schoolName must be at least 2 characters long."}
    
    # Check maximum length
    if len(school_name_stripped) > 100:
        return {"valid": False, "error": "schoolName must not exceed 100 characters."}
    
    # Check if School Name contains only numbers or symbols (must have at least one letter)
    if not re.match(EDUCATION_SCHOOL_NAME_PATTERN, school_name_stripped):
        return {"valid": False, "error": "schoolName should not contain only numbers or symbols."}
    
    # Validate Degree
    if not isinstance(degree, str):
        return {"valid": False, "error": "degree must be a string."}
    
    # Check if Degree is empty or whitespace
    if not degree or not degree.strip():
        return {"valid": False, "error": "degree field must not be empty."}
    
    # Strip whitespace for length validation
    degree_stripped = degree.strip()
    
    # Check minimum length
    if len(degree_stripped) < 2:
        return {"valid": False, "error": "degree must be at least 2 characters long."}
    
    # Check maximum length
    if len(degree_stripped) > 100:
        return {"valid": False, "error": "degree must not exceed 100 characters."}
    
    # Check if Degree matches the pattern
    if not re.match(EDUCATION_DEGREE_PATTERN, degree_stripped):
        return {"valid": False, "error": "degree contains invalid characters."}
    
    # Validate Field of Study
    if not isinstance(field_of_study, str):
        return {"valid": False, "error": "fieldOfStudy must be a string."}
    
    # Check if Field of Study is empty or whitespace
    if not field_of_study or not field_of_study.strip():
        return {"valid": False, "error": "fieldOfStudy field must not be empty."}
    
    # Strip whitespace for length validation
    field_of_study_stripped = field_of_study.strip()
    
    # Check minimum length
    if len(field_of_study_stripped) < 2:
        return {"valid": False, "error": "fieldOfStudy must be at least 2 characters long."}
    
    # Check maximum length (note: 50 characters, not 100)
    if len(field_of_study_stripped) > 50:
        return {"valid": False, "error": "fieldOfStudy must not exceed 50 characters."}
    
    # Check if Field of Study matches the pattern
    if not re.match(EDUCATION_FIELD_OF_STUDY_PATTERN, field_of_study_stripped):
        return {"valid": False, "error": "fieldOfStudy contains invalid characters."}
    
    # If all validations pass
    return {"valid": True, "message": "Education input is valid."}


def validate_school_name(school_name):
    """
    Validates only the School Name field.
    
    Args:
        school_name (str): School/Institution name
    
    Returns:
        bool: True if valid
    
    Raises:
        ValueError: If validation fails with detailed error message
    """
    if not isinstance(school_name, str):
        raise ValueError("schoolName must be a string.")
    
    if not school_name or not school_name.strip():
        raise ValueError("schoolName field must not be empty.")
    
    school_name_stripped = school_name.strip()
    
    if len(school_name_stripped) < 2:
        raise ValueError("schoolName must be at least 2 characters long.")
    
    if len(school_name_stripped) > 100:
        raise ValueError("schoolName must not exceed 100 characters.")
    
    if not re.match(EDUCATION_SCHOOL_NAME_PATTERN, school_name_stripped):
        raise ValueError("schoolName should not contain only numbers or symbols.")
    
    return True


def validate_degree(degree):
    """
    Validates only the Degree field.
    
    Args:
        degree (str): Degree/Diploma/Learning title
    
    Returns:
        bool: True if valid
    
    Raises:
        ValueError: If validation fails with detailed error message
    """
    if not isinstance(degree, str):
        raise ValueError("degree must be a string.")
    
    if not degree or not degree.strip():
        raise ValueError("degree field must not be empty.")
    
    degree_stripped = degree.strip()
    
    if len(degree_stripped) < 2:
        raise ValueError("degree must be at least 2 characters long.")
    
    if len(degree_stripped) > 100:
        raise ValueError("degree must not exceed 100 characters.")
    
    if not re.match(EDUCATION_DEGREE_PATTERN, degree_stripped):
        raise ValueError("degree contains invalid characters.")
    
    return True


def validate_field_of_study(field_of_study):
    """
    Validates only the Field of Study field.
    
    Args:
        field_of_study (str): Subject/Specialization/Study area
    
    Returns:
        bool: True if valid
    
    Raises:
        ValueError: If validation fails with detailed error message
    """
    if not isinstance(field_of_study, str):
        raise ValueError("fieldOfStudy must be a string.")
    
    if not field_of_study or not field_of_study.strip():
        raise ValueError("fieldOfStudy field must not be empty.")
    
    field_of_study_stripped = field_of_study.strip()
    
    if len(field_of_study_stripped) < 2:
        raise ValueError("fieldOfStudy must be at least 2 characters long.")
    
    if len(field_of_study_stripped) > 50:
        raise ValueError("fieldOfStudy must not exceed 50 characters.")
    
    if not re.match(EDUCATION_FIELD_OF_STUDY_PATTERN, field_of_study_stripped):
        raise ValueError("fieldOfStudy contains invalid characters.")
    
    return True

