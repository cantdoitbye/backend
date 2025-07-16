from datetime import datetime
from graphql import GraphQLError

def validate_dob(dob_input, min_age=10, max_age=100):
    """
    Validates the date of birth (DOB) based on a minimum and maximum age range.
    Supports the "YYYY-MM-DD" and "YYYY-MM-DDTHH:MM:SS" formats or a datetime object.

    Args:
        dob_input (str or datetime): The date of birth as a string in "YYYY-MM-DD" or 
                                     "YYYY-MM-DDTHH:MM:SS" format, or a datetime object.
        min_age (int): The minimum allowed age (default is 10 years).
        max_age (int): The maximum allowed age (default is 100 years).

    Raises:
        GraphQLError: If the DOB is invalid or not within the age range.

    Returns:
        bool: True if the DOB is valid and falls within the age range.
    """
    try:
        # If the input is already a datetime object, use it directly
        if isinstance(dob_input, datetime):
            dob = dob_input
        else:
            # Try parsing the DOB string in ISO 8601 format
            try:
                dob = datetime.strptime(dob_input, "%Y-%m-%dT%H:%M:%S")
            except ValueError:
                # Fall back to parsing as "YYYY-MM-DD" if time is not provided
                dob = datetime.strptime(dob_input, "%Y-%m-%d")

        today = datetime.now()

        # Calculate the age in years
        age_in_years = (today - dob).days // 365

        # Check if the age is within the allowed range
        if not (min_age <= age_in_years <= max_age):
            raise GraphQLError(f"Age must be between {min_age} and {max_age} years.")
        return True
    except ValueError:
        raise GraphQLError("Invalid date format. Expected format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS.")
