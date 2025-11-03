import random
from auth_manager.models import Profile
from django.contrib.auth.models import User

def generate_unique_indian_mobile():
    """
    Generate a unique Indian mobile number.
    
    Indian mobile numbers:
    - Start with country code +91
    - Have 10 digits after country code
    - First digit after country code is typically 6, 7, 8, or 9
    - Format: +91XXXXXXXXXX
    
    Returns:
        str: Unique Indian mobile number in format +91XXXXXXXXXX
    """
    # Indian mobile number prefixes (first digit after +91)
    valid_prefixes = ['6', '7', '8', '9']
    
    max_attempts = 1000  # Prevent infinite loops
    
    for _ in range(max_attempts):
        # Generate random 10-digit mobile number
        first_digit = random.choice(valid_prefixes)
        remaining_digits = ''.join([str(random.randint(0, 9)) for _ in range(9)])
        mobile_number = f"+91{first_digit}{remaining_digits}"
        
        # Check if this number already exists in Neo4j Profile nodes
        existing_profile = Profile.nodes.filter(phone_number=mobile_number).first_or_none()
        if not existing_profile:
            return mobile_number
    
    # Fallback if all attempts failed (highly unlikely)
    raise ValueError("Unable to generate unique mobile number after maximum attempts")

def generate_unique_username(base_name, max_length=30):
    """
    Generate a unique username based on the user's name.
    
    Args:
        base_name (str): Base name to create username from
        max_length (int): Maximum length for username
        
    Returns:
        str: Unique username
    """
    # Handle None input
    if base_name is None:
        base_name = "user"
    
    # Clean base name - remove spaces, special chars, convert to lowercase
    clean_base = ''.join(c.lower() for c in str(base_name) if c.isalnum())[:20]
    
    # If clean_base is empty after cleaning, use a default
    if not clean_base:
        clean_base = "user"
    
    max_attempts = 1000
    
    for attempt in range(max_attempts):
        if attempt == 0:
            # First try without any suffix
            username = clean_base[:max_length]
        else:
            # Add random numbers
            suffix = str(random.randint(100, 9999))
            # Ensure we have space for the suffix
            base_length = max_length - len(suffix)
            if base_length < 1:
                # If max_length is too small, use just the suffix with 'u' prefix
                username = f"u{suffix}"[:max_length]
            else:
                username = f"{clean_base[:base_length]}{suffix}"
        
        # Ensure username is not empty and has minimum length
        if not username:
            username = f"user{random.randint(1000, 9999)}"
        
        # Check if username is unique in Django User model
        if username and len(username) > 0 and not User.objects.filter(username=username).exists():
            return username
    
    # Fallback - generate a completely random username
    fallback_username = f"user{random.randint(10000, 99999)}"
    return fallback_username

def generate_realistic_indian_data():
    """
    Generate realistic Indian user data for bot accounts.
    
    Returns:
        dict: Dictionary containing realistic Indian user data
    """
    indian_cities = [
        "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Kolkata", 
        "Pune", "Ahmedabad", "Jaipur", "Lucknow", "Kanpur", "Nagpur",
        "Indore", "Thane", "Bhopal", "Visakhapatnam", "Patna", "Vadodara",
        "Ghaziabad", "Ludhiana", "Agra", "Nashik", "Faridabad", "Meerut"
    ]
    
    indian_states = [
        "Maharashtra", "Delhi", "Karnataka", "Telangana", "Tamil Nadu", 
        "West Bengal", "Gujarat", "Rajasthan", "Uttar Pradesh", "Madhya Pradesh",
        "Andhra Pradesh", "Bihar", "Punjab", "Haryana", "Assam", "Odisha"
    ]
    
    # Common Indian designations
    designations = [
        "Software Engineer", "Senior Software Engineer", "Product Manager",
        "Data Scientist", "Business Analyst", "Marketing Manager", 
        "Sales Executive", "HR Manager", "Financial Analyst", "Consultant",
        "Team Lead", "Project Manager", "UI/UX Designer", "DevOps Engineer",
        "Quality Assurance Engineer", "Content Writer", "Digital Marketer"
    ]
    
    # Common Indian companies (mix of Indian and global)
    companies = [
        "Tata Consultancy Services", "Infosys", "Wipro", "HCL Technologies",
        "Tech Mahindra", "Accenture", "IBM", "Microsoft", "Google", "Amazon",
        "Flipkart", "Paytm", "Zomato", "Swiggy", "Ola", "Uber", "BYJU'S",
        "Reliance Industries", "HDFC Bank", "ICICI Bank", "Axis Bank"
    ]
    
    return {
        'city': random.choice(indian_cities),
        'state': random.choice(indian_states),
        'designation': random.choice(designations),
        'company': random.choice(companies),
        'lives_in': f"{random.choice(indian_cities)}, India"
    }
