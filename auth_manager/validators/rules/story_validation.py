import re
from auth_manager.validators.rules.regex_patterns import (
    STORY_TITLE_PATTERN,
    STORY_CONTENT_PATTERN,
    STORY_CAPTIONS_PATTERN,
)


def validate_story_input(title, content, captions):
    """
    Validates the create story form input with three fields: title, content, and captions.
    
    Args:
        title (str): Story title
        content (str): Story content
        captions (str): Story captions
    
    Returns:
        dict: Validation result with format:
            {
              "isValid": true/false,
              "errors": {
                "title": "Error message or empty string",
                "content": "Error message or empty string",
                "captions": "Error message or empty string"
              },
              "validatedData": {
                "title": "<trimmed title>",
                "content": "<trimmed content>",
                "captions": "<trimmed captions>"
              }
            }
    
    Validation Rules:
        Title:
        - Minimum length: 1 character (after trimming)
        - Maximum length: 50 characters (after trimming)
        - Trim extra spaces before counting
        
        Content:
        - Minimum length: 1 character (after trimming)
        - Maximum length: 50 characters (after trimming)
        - Trim extra spaces before counting
        
        Captions:
        - Minimum length: 1 character (after trimming)
        - Maximum length: 100 characters (after trimming)
        - Trim extra spaces before counting
    """
    
    # Initialize result structure
    result = {
        "isValid": True,
        "errors": {
            "title": "",
            "content": "",
            "captions": ""
        },
        "validatedData": {
            "title": "",
            "content": "",
            "captions": ""
        }
    }
    
    # Validate Title
    if not isinstance(title, str):
        result["isValid"] = False
        result["errors"]["title"] = "Title must be a string."
    else:
        title_trimmed = title.strip()
        result["validatedData"]["title"] = title_trimmed
        
        if len(title_trimmed) == 0:
            result["isValid"] = False
            result["errors"]["title"] = "Title must not be empty."
        elif len(title_trimmed) > 50:
            result["isValid"] = False
            result["errors"]["title"] = "Title must not exceed 50 characters."
        elif not re.match(STORY_TITLE_PATTERN, title_trimmed):
            result["isValid"] = False
            result["errors"]["title"] = "Title contains invalid characters."
    
    # Validate Content
    if not isinstance(content, str):
        result["isValid"] = False
        result["errors"]["content"] = "Content must be a string."
    else:
        content_trimmed = content.strip()
        result["validatedData"]["content"] = content_trimmed
        
        if len(content_trimmed) == 0:
            result["isValid"] = False
            result["errors"]["content"] = "Content must not be empty."
        elif len(content_trimmed) > 50:
            result["isValid"] = False
            result["errors"]["content"] = "Content must not exceed 50 characters."
        elif not re.match(STORY_CONTENT_PATTERN, content_trimmed):
            result["isValid"] = False
            result["errors"]["content"] = "Content contains invalid characters."
    
    # Validate Captions
    if not isinstance(captions, str):
        result["isValid"] = False
        result["errors"]["captions"] = "Captions must be a string."
    else:
        captions_trimmed = captions.strip()
        result["validatedData"]["captions"] = captions_trimmed
        
        if len(captions_trimmed) == 0:
            result["isValid"] = False
            result["errors"]["captions"] = "Captions must not be empty."
        elif len(captions_trimmed) > 100:
            result["isValid"] = False
            result["errors"]["captions"] = "Captions must not exceed 100 characters."
        elif not re.match(STORY_CAPTIONS_PATTERN, captions_trimmed):
            result["isValid"] = False
            result["errors"]["captions"] = "Captions contains invalid characters."
    
    return result


def validate_title(title):
    """
    Validates only the Title field.
    
    Args:
        title (str): Story title
    
    Returns:
        bool: True if valid
    
    Raises:
        ValueError: If validation fails with detailed error message
    """
    if not isinstance(title, str):
        raise ValueError("Title must be a string.")
    
    title_trimmed = title.strip()
    
    if len(title_trimmed) == 0:
        raise ValueError("Title must not be empty.")
    
    if len(title_trimmed) > 50:
        raise ValueError("Title must not exceed 50 characters.")
    
    if not re.match(STORY_TITLE_PATTERN, title_trimmed):
        raise ValueError("Title contains invalid characters.")
    
    return True


def validate_content(content):
    """
    Validates only the Content field.
    
    Args:
        content (str): Story content
    
    Returns:
        bool: True if valid
    
    Raises:
        ValueError: If validation fails with detailed error message
    """
    if not isinstance(content, str):
        raise ValueError("Content must be a string.")
    
    content_trimmed = content.strip()
    
    if len(content_trimmed) == 0:
        raise ValueError("Content must not be empty.")
    
    if len(content_trimmed) > 50:
        raise ValueError("Content must not exceed 50 characters.")
    
    if not re.match(STORY_CONTENT_PATTERN, content_trimmed):
        raise ValueError("Content contains invalid characters.")
    
    return True


def validate_captions(captions):
    """
    Validates only the Captions field.
    
    Args:
        captions (str): Story captions
    
    Returns:
        bool: True if valid
    
    Raises:
        ValueError: If validation fails with detailed error message
    """
    if not isinstance(captions, str):
        raise ValueError("Captions must be a string.")
    
    captions_trimmed = captions.strip()
    
    if len(captions_trimmed) == 0:
        raise ValueError("Captions must not be empty.")
    
    if len(captions_trimmed) > 100:
        raise ValueError("Captions must not exceed 100 characters.")
    
    if not re.match(STORY_CAPTIONS_PATTERN, captions_trimmed):
        raise ValueError("Captions contains invalid characters.")
    
    return True

