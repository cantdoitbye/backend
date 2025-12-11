import graphene
import re
from graphql import GraphQLError
from graphql.language import ast, location  # 


class Boolean(graphene.Scalar):
    """Custom Boolean Scalar that enforces length constraints and disallows special characters"""
    @classmethod
    def add_option(cls, field_name, mutation_name=None):
        """Create a new class with the specified field name and mutation name"""
        # Create a unique class name that includes the mutation name if provided
        class_name = f"Custom{field_name.title().replace('_', '')}Validator"
        if mutation_name:
            class_name = f"{class_name}_{mutation_name}"
            
        return type(class_name, (cls,), {'field_name': field_name, 'mutation_name': mutation_name})
    
    field_name = "value"
    mutation_name = None

    def raise_error(self, message):
        """Helper function to raise GraphQLError with custom extensions"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if self.mutation_name:
            path.append(self.mutation_name)
        path.append(self.field_name)
        raise GraphQLError(message, extensions=extensions, path=path)

    def parse_value(self, value):
        """Handles values when passed as variables"""
        if not isinstance(value, bool):
            self.raise_error(f"{self.field_name} must be a boolean.")
        return value

    @classmethod
    def parse_literal(cls, node, _variables=None):
        """Handles inline literals in GraphQL queries"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if hasattr(cls, 'mutation_name') and cls.mutation_name:
            path.append(cls.mutation_name)
        path.append(cls.field_name)
        if not isinstance(node, ast.BooleanValueNode):
            raise GraphQLError(f"{cls.field_name} must be a boolean.", extensions=extensions, path=path)

        return node.value


class Float(graphene.Scalar):
    """Custom Float Scalar that validates float values"""
    @classmethod
    def add_option(cls, field_name, mutation_name=None):
        """Create a new class with the specified field name and mutation name"""
        # Create a unique class name that includes the mutation name if provided
        class_name = f"Custom{field_name.title().replace('_', '')}Validator"
        if mutation_name:
            class_name = f"{class_name}_{mutation_name}"
            
        return type(class_name, (cls,), {'field_name': field_name, 'mutation_name': mutation_name})
    
    field_name = "value"
    mutation_name = None

    def raise_error(self, message):
        """Helper function to raise GraphQLError with custom extensions"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if self.mutation_name:
            path.append(self.mutation_name)
        path.append(self.field_name)
        raise GraphQLError(message, extensions=extensions, path=path)

    def parse_value(self, value):
        """Handles values when passed as variables"""
        if not isinstance(value, (int, float)):
            self.raise_error(f"{self.field_name} must be a number.")
        return float(value)

    @classmethod
    def parse_literal(cls, node, _variables=None):
        """Handles inline literals in GraphQL queries"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if hasattr(cls, 'mutation_name') and cls.mutation_name:
            path.append(cls.mutation_name)
        path.append(cls.field_name)
        
        if not isinstance(node, (ast.FloatValueNode, ast.IntValueNode)):
            raise GraphQLError(f"{cls.field_name} must be a number.", extensions=extensions, path=path)

        try:
            return float(node.value)
        except ValueError:
            raise GraphQLError(f"Invalid number format for {cls.field_name}.", extensions=extensions, path=path)


class String(graphene.Scalar):
    """Custom String Scalar that enforces length constraints and disallows special characters"""
    @classmethod
    def add_option(cls, field_name, mutation_name=None):
        """Create a new class with the specified field name and mutation name"""
        # Create a unique class name that includes the mutation name if provided
        class_name = f"Custom{field_name.title().replace('_', '')}Validator"
        if mutation_name:
            class_name = f"{class_name}_{mutation_name}"
            
        return type(class_name, (cls,), {'field_name': field_name, 'mutation_name': mutation_name})
    
    field_name = "value"
    mutation_name = None
  
    def raise_error(self, message):
        """Helper function to raise GraphQLError with custom extensions"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if self.mutation_name:
            path.append(self.mutation_name)
        path.append(self.field_name)
        raise GraphQLError(message, extensions=extensions, path=path)

    def parse_value(self, value):
        """Handles values when passed as variables"""
        # Allow None for optional fields
        if value is None:
            return None

        if not isinstance(value, str):
            self.raise_error(f"{self.field_name} must be a string.")
        return value

    @classmethod
    def parse_literal(cls, node, _variables=None):
        """Handles inline literals in GraphQL queries"""
        # Allow None for optional fields
        if node is None or (hasattr(node, 'value') and node.value is None):
            return None

        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if hasattr(cls, 'mutation_name') and cls.mutation_name:
            path.append(cls.mutation_name)
        path.append(cls.field_name)
        if not isinstance(node, ast.StringValueNode):
            raise GraphQLError(f"{cls.field_name} must be a string.", extensions=extensions, path=path)

        value = node.value

        return value

class NonSpecialCharacterString2_30(graphene.Scalar):
    """Custom String Scalar that enforces length constraints and allows letters with single spaces (for full names)"""

    MIN_LENGTH = 2
    MAX_LENGTH = 30
    # Allows letters with optional single spaces between words (no leading/trailing spaces, no multiple spaces)
    ALLOWED_PATTERN = re.compile(r"^[a-zA-Z]+(?: [a-zA-Z]+)*$")
    
    @classmethod
    def add_option(cls, field_name, mutation_name=None):
        """Create a new class with the specified field name and mutation name"""
        # Create a unique class name that includes the mutation name if provided
        class_name = f"Custom{field_name.title().replace('_', '')}Validator"
        if mutation_name:
            class_name = f"{class_name}_{mutation_name}"
            
        return type(class_name, (cls,), {'field_name': field_name, 'mutation_name': mutation_name})
    
    field_name = "value"
    mutation_name = None
  
    def raise_error(self, message):
        """Helper function to raise GraphQLError with custom extensions"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if self.mutation_name:
            path.append(self.mutation_name)
        path.append(self.field_name)
        raise GraphQLError(message, extensions=extensions, path=path)

    def parse_value(self, value):
        """Handles values when passed as variables"""
        # Allow None for optional fields
        if value is None:
            return None
            
        if not isinstance(value, str):
            self.raise_error(f"{self.field_name} must be a string.")
        
        # Trim leading and trailing whitespace
        value_trimmed = value.strip()
        
        if not (self.MIN_LENGTH <= len(value_trimmed) <= self.MAX_LENGTH):
            self.raise_error(f"String length must be between {self.MIN_LENGTH} and {self.MAX_LENGTH} characters.")
        if not self.ALLOWED_PATTERN.match(value_trimmed):
            self.raise_error(f"{self.field_name} must contain only letters with single spaces between words. No special characters or numbers allowed.")
        return value_trimmed

    @classmethod
    def parse_literal(cls, node, _variables=None):
        """Handles inline literals in GraphQL queries"""
        # Allow None for optional fields
        if node is None or (hasattr(node, 'value') and node.value is None):
            return None
            
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if hasattr(cls, 'mutation_name') and cls.mutation_name:
            path.append(cls.mutation_name)
        path.append(cls.field_name)
        if not isinstance(node, ast.StringValueNode):
            raise GraphQLError(f"{cls.field_name} must be a string.", extensions=extensions, path=path)

        # Trim leading and trailing whitespace
        value = node.value.strip()
        
        if not (cls.MIN_LENGTH <= len(value) <= cls.MAX_LENGTH):
            raise GraphQLError(
                f"String length must be between {cls.MIN_LENGTH} and {cls.MAX_LENGTH} characters.",
                extensions=extensions,
                path=path,

            )
        if not cls.ALLOWED_PATTERN.match(value):
            raise GraphQLError(
                f"{cls.field_name} must contain only letters with single spaces between words. No special characters or numbers allowed.",
                extensions=extensions,
                path=path,
            )
        return value


class SpaceSpecialCharacterString2_30(graphene.Scalar):
    """Custom String Scalar that enforces length constraints and allows letters with single spaces (for full names)"""

    MIN_LENGTH = 2
    MAX_LENGTH = 30
    # Allows letters with optional single spaces between words (no leading/trailing spaces, no multiple spaces)
    ALLOWED_PATTERN = re.compile(r"^[a-zA-ZÀ-ÖØ-öø-ÿ]+(?: [a-zA-ZÀ-ÖØ-öø-ÿ]+)*$")  # Includes Unicode letters
    
    @classmethod
    def add_option(cls, field_name, mutation_name=None):
        """Create a new class with the specified field name and mutation name"""
        # Create a unique class name that includes the mutation name if provided
        class_name = f"Custom{field_name.title().replace('_', '')}Validator"
        if mutation_name:
            class_name = f"{class_name}_{mutation_name}"
            
        return type(class_name, (cls,), {'field_name': field_name, 'mutation_name': mutation_name})
    
    field_name = "value"
    mutation_name = None
  
    def raise_error(self, message):
        """Helper function to raise GraphQLError with custom extensions"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if self.mutation_name:
            path.append(self.mutation_name)
        path.append(self.field_name)
        raise GraphQLError(message, extensions=extensions, path=path)

    def parse_value(self, value):
        """Handles values when passed as variables"""
        # Allow None for optional fields
        if value is None:
            return None
            
        if not isinstance(value, str):
            self.raise_error(f"{self.field_name} must be a string.")
        
        # Trim leading and trailing whitespace
        value_trimmed = value.strip()
        
        if not (self.MIN_LENGTH <= len(value_trimmed) <= self.MAX_LENGTH):
            self.raise_error(f"String length must be between {self.MIN_LENGTH} and {self.MAX_LENGTH} characters.")
        if not self.ALLOWED_PATTERN.match(value_trimmed):
            self.raise_error(f"{self.field_name} must contain only letters with single spaces between words. No special characters or numbers allowed.")
        return value_trimmed

    @classmethod
    def parse_literal(cls, node, _variables=None):
        """Handles inline literals in GraphQL queries"""
        # Allow None for optional fields
        if node is None or (hasattr(node, 'value') and node.value is None):
            return None
            
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if hasattr(cls, 'mutation_name') and cls.mutation_name:
            path.append(cls.mutation_name)
        path.append(cls.field_name)
        if not isinstance(node, ast.StringValueNode):
            raise GraphQLError(f"{cls.field_name} must be a string.", extensions=extensions, path=path)

        # Trim leading and trailing whitespace
        value = node.value.strip()
        
        if not (cls.MIN_LENGTH <= len(value) <= cls.MAX_LENGTH):
            raise GraphQLError(
                f"String length must be between {cls.MIN_LENGTH} and {cls.MAX_LENGTH} characters.",
                extensions=extensions,
                path=path,

            )
        if not cls.ALLOWED_PATTERN.match(value):
            raise GraphQLError(
                f"{cls.field_name} must contain only letters with single spaces between words. No special characters or numbers allowed.",
                extensions=extensions,
                path=path,
            )
        return value



class NonSpecialCharacterString2_50(graphene.Scalar):
    """Custom String Scalar that enforces length constraints and disallows special characters"""

    MIN_LENGTH = 2
    MAX_LENGTH = 50
    ALLOWED_PATTERN = re.compile(r"^[a-zA-Z]+$")  # Allows only letters, numbers, and spaces

    @classmethod
    def add_option(cls, field_name, mutation_name=None):
        """Create a new class with the specified field name and mutation name"""
        # Create a unique class name that includes the mutation name if provided
        class_name = f"Custom{field_name.title().replace('_', '')}Validator"
        if mutation_name:
            class_name = f"{class_name}_{mutation_name}"
            
        return type(class_name, (cls,), {'field_name': field_name, 'mutation_name': mutation_name})
    
    field_name = "value" 
    mutation_name = None

    def raise_error(self, message):
        """Helper function to raise GraphQLError with custom extensions"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if self.mutation_name:
            path.append(self.mutation_name)
        path.append(self.field_name)
        raise GraphQLError(message, extensions=extensions, path=path)

    def parse_value(self, value):
        """Handles values when passed as variables"""
        if not isinstance(value, str):
            self.raise_error(f"{self.field_name} must be a string.")
        if not (self.MIN_LENGTH <= len(value) <= self.MAX_LENGTH):
            self.raise_error(f"String length must be between {self.MIN_LENGTH} and {self.MAX_LENGTH} characters.")
        if not self.ALLOWED_PATTERN.match(value):
            self.raise_error(f"{self.field_name} must contain only letters. No special characters allowed.")
        return value

    @classmethod
    def parse_literal(cls, node, _variables=None):
        """Handles inline literals in GraphQL queries"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if hasattr(cls, 'mutation_name') and cls.mutation_name:
            path.append(cls.mutation_name)
        path.append(cls.field_name)
            
        if not isinstance(node, ast.StringValueNode):
            raise GraphQLError("Value must be a string.", extensions=extensions, path=path)

        value = node.value
        if not (2 <= len(value) <= 50):
            raise GraphQLError(
                f"String length must be between 2 and 50 characters.",
                extensions=extensions,
                path=path
            )
        if not re.match(r"^[a-zA-ZÀ-ÖØ-öø-ÿ]+$", value):
            raise GraphQLError(
                "Value must contain only letters. No special characters allowed.",
                extensions=extensions,
                path=path
            )
        return value
    

class NonSpecialCharacterString1_200(graphene.Scalar):
    """Custom String Scalar that enforces length constraints and allows letters, numbers, spaces, emojis, and common punctuation"""

    MIN_LENGTH = 1
    MAX_LENGTH = 200
    # Allows letters, numbers, spaces, emojis, and common punctuation (no HTML tags)
    ALLOWED_PATTERN = re.compile(
        r"^[a-zA-Z0-9\s!\"#$%&'()*+,\-./:;<=>?@\[\\\]^_`{|}~"
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
        r"]+$",
        re.UNICODE
    )
     
    @classmethod
    def add_option(cls, field_name, mutation_name=None):
        """Create a new class with the specified field name and mutation name"""
        # Create a unique class name that includes the mutation name if provided
        class_name = f"Custom{field_name.title().replace('_', '')}Validator"
        if mutation_name:
            class_name = f"{class_name}_{mutation_name}"
            
        return type(class_name, (cls,), {'field_name': field_name, 'mutation_name': mutation_name})
    
    field_name = "value" 
    mutation_name = None

    def raise_error(self, message):
        """Helper function to raise GraphQLError with custom extensions"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if self.mutation_name:
            path.append(self.mutation_name)
        path.append(self.field_name)
        raise GraphQLError(message, extensions=extensions, path=path)

    def parse_value(self, value):
        """Handles values when passed as variables"""
        # Allow None for optional fields
        if value is None:
            return None
            
        if not isinstance(value, str):
            self.raise_error(f"{self.field_name} must be a string.")
        
        # Trim whitespace
        value_trimmed = value.strip()
        
        # Reject whitespace-only comments
        if len(value_trimmed) == 0:
            self.raise_error(f"{self.field_name} cannot be empty or contain only whitespace.")
        
        if not (self.MIN_LENGTH <= len(value_trimmed) <= self.MAX_LENGTH):
            self.raise_error(f"{self.field_name} must be between {self.MIN_LENGTH} and {self.MAX_LENGTH} characters.")
        
        # Check for HTML tags
        if re.search(r"<[^>]+>", value_trimmed):
            self.raise_error("HTML tags are not allowed.")
        
        if not self.ALLOWED_PATTERN.match(value_trimmed):
            self.raise_error(f"{self.field_name} must contain only letters, numbers, spaces, emojis, and common punctuation.")
        return value_trimmed

    @classmethod
    def parse_literal(cls, node, _variables=None):
        """Handles inline literals in GraphQL queries"""
        # Allow None for optional fields
        if node is None or (hasattr(node, 'value') and node.value is None):
            return None
            
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if hasattr(cls, 'mutation_name') and cls.mutation_name:
            path.append(cls.mutation_name)
        path.append(cls.field_name)
            
        if not isinstance(node, ast.StringValueNode):
            raise GraphQLError("Value must be a string.", extensions=extensions, path=path)

        value = node.value.strip()
        
        # Reject whitespace-only comments
        if len(value) == 0:
            raise GraphQLError(
                f"Value cannot be empty or contain only whitespace.",
                extensions=extensions,
                path=path
            )
        
        if not (1 <= len(value) <= 200):
            raise GraphQLError(
                f"Value must be between 1 and 200 characters.",
                extensions=extensions,
                path=path
            )
        if re.search(r"<[^>]+>", value):  
            raise GraphQLError(
                "HTML tags are not allowed.",
                extensions=extensions,
                path=path
            )
        if not cls.ALLOWED_PATTERN.match(value):
            raise GraphQLError(
                "Value must contain only letters, numbers, spaces, emojis, and common punctuation.",
                extensions=extensions,
                path=path
            )
        return value
    


class NonSpecialCharacterString5_100(graphene.Scalar):
    """Custom String Scalar that enforces length constraints and allows letters, numbers, spaces, special characters, and emojis"""

    MIN_LENGTH = 5
    MAX_LENGTH = 100
    # Allows letters, numbers, spaces, common special characters, and emoji ranges (Unicode blocks)
    ALLOWED_PATTERN = re.compile(
        r"^[a-zA-Z0-9 !@#$%^&*()_+\-=\[\]{}|;':\",./<>?`~"
        r"\u00C0-\u017F"  # Latin Extended (accented characters)
        r"\u0100-\u024F"  # Latin Extended Additional
        r"\u1E00-\u1EFF"  # Latin Extended Additional
        r"\u2000-\u206F"  # General Punctuation
        r"\u2070-\u209F"  # Superscripts and Subscripts
        r"\u20A0-\u20CF"  # Currency Symbols
        r"\u2100-\u214F"  # Letterlike Symbols
        r"\u2190-\u21FF"  # Arrows
        r"\u2200-\u22FF"  # Mathematical Operators
        r"\u2300-\u23FF"  # Miscellaneous Technical
        r"\u2400-\u243F"  # Control Pictures
        r"\u2440-\u245F"  # Optical Character Recognition
        r"\u2460-\u24FF"  # Enclosed Alphanumerics
        r"\u2500-\u257F"  # Box Drawing
        r"\u2580-\u259F"  # Block Elements
        r"\u25A0-\u25FF"  # Geometric Shapes
        r"\u2600-\u26FF"  # Miscellaneous Symbols
        r"\u2700-\u27BF"  # Dingbats
        r"\U0001F000-\U0001F02F"  # Mahjong Tiles
        r"\U0001F030-\U0001F09F"  # Domino Tiles
        r"\U0001F0A0-\U0001F0FF"  # Playing Cards
        r"\U0001F100-\U0001F1FF"  # Enclosed Alphanumeric Supplement
        r"\U0001F200-\U0001F2FF"  # Enclosed Ideographic Supplement
        r"\U0001F300-\U0001F5FF"  # Miscellaneous Symbols and Pictographs
        r"\U0001F600-\U0001F64F"  # Emoticons
        r"\U0001F650-\U0001F67F"  # Ornamental Dingbats
        r"\U0001F680-\U0001F6FF"  # Transport and Map Symbols
        r"\U0001F700-\U0001F77F"  # Alchemical Symbols
        r"\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        r"\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        r"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        r"\U0001FA00-\U0001FA6F"  # Chess Symbols
        r"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        r"\u200D"  # Zero-Width Joiner (ZWJ) - for complex emoji sequences
        r"\uFE00-\uFE0F"  # Variation Selectors (VS15, VS16) - for emoji variations
        r"\u20E3"  # Combining Enclosing Keycap - for keycap emojis like 2️⃣
        r"]+$", re.UNICODE
    )
    
    @classmethod
    def add_option(cls, field_name, mutation_name=None):
        """Create a new class with the specified field name and mutation name"""
        # Create a unique class name that includes the mutation name if provided
        class_name = f"Custom{field_name.title().replace('_', '')}Validator"
        if mutation_name:
            class_name = f"{class_name}_{mutation_name}"
            
        return type(class_name, (cls,), {'field_name': field_name, 'mutation_name': mutation_name})
    
    field_name = "value" 
    mutation_name = None

    def raise_error(self, message):
        """Helper function to raise GraphQLError with custom extensions"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if self.mutation_name:
            path.append(self.mutation_name)
        path.append(self.field_name)
        raise GraphQLError(message, extensions=extensions, path=path)

    def parse_value(self, value):
        """Handles values when passed as variables"""
        if not isinstance(value, str):
            self.raise_error(f"{self.field_name} must be a string.")
        if not (self.MIN_LENGTH <= len(value) <= self.MAX_LENGTH):
            self.raise_error(f"String length must be between {self.MIN_LENGTH} and {self.MAX_LENGTH} characters.")
        if not self.__class__.ALLOWED_PATTERN.match(value):
            self.raise_error(f"{self.field_name} must contain only letters, numbers, spaces, special characters, and emojis.")
        return value

    @classmethod
    def parse_literal(cls, node, _variables=None):
        """Handles inline literals in GraphQL queries"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if hasattr(cls, 'mutation_name') and cls.mutation_name:
            path.append(cls.mutation_name)
        path.append(cls.field_name)
            
        if not isinstance(node, ast.StringValueNode):  # 
            raise GraphQLError("Value must be a string.", extensions=extensions, path=path)

        value = node.value
        if not (5 <= len(value) <= 100):
            raise GraphQLError(
                f"String length must be between 5 and 100 characters.",
                extensions=extensions,
                path=path
            )
        if re.search(r"<[^>]+>", value):  
            raise GraphQLError(
                "HTML tags are not allowed.",
                extensions=extensions,
                path=path
            )
        if not cls.ALLOWED_PATTERN.match(value):
            raise GraphQLError(
                "Value must contain only letters, numbers, spaces, special characters, and emojis.",
                extensions=extensions,
                path=path
            )
        return value
    
class NonSpecialCharacterString5_50(graphene.Scalar):
    """Custom String Scalar that enforces length constraints and disallows special characters"""

    MIN_LENGTH = 5
    MAX_LENGTH = 50
    ALLOWED_PATTERN = re.compile(r"^[a-zA-Z]+$")  # Allows only letters, numbers, and spaces

    @classmethod
    def add_option(cls, field_name, mutation_name=None):
        """Create a new class with the specified field name and mutation name"""
        # Create a unique class name that includes the mutation name if provided
        class_name = f"Custom{field_name.title().replace('_', '')}Validator"
        if mutation_name:
            class_name = f"{class_name}_{mutation_name}"
            
        return type(class_name, (cls,), {'field_name': field_name, 'mutation_name': mutation_name})
    
    field_name = "value" 
    
    def raise_error(self, message):
        """Helper function to raise GraphQLError with custom extensions"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if self.mutation_name:
            path.append(self.mutation_name)
        path.append(self.field_name)
        raise GraphQLError(message, extensions=extensions, path=path)

    def parse_value(self, value):
        """Handles values when passed as variables"""
        if not isinstance(value, str):
            self.raise_error(f"{self.field_name} must be a string.")
        if not (self.MIN_LENGTH <= len(value) <= self.MAX_LENGTH):
            self.raise_error(f"String length must be between {self.MIN_LENGTH} and {self.MAX_LENGTH} characters.")
        if not self.ALLOWED_PATTERN.match(value):
            self.raise_error(f"{self.field_name} must contain only letters. No special characters allowed.")
        return value

    @classmethod
    def parse_literal(cls, node, _variables=None):
        """Handles inline literals in GraphQL queries"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if hasattr(cls, 'mutation_name') and cls.mutation_name:
            path.append(cls.mutation_name)
        path.append(cls.field_name)
            
        if not isinstance(node, ast.StringValueNode):
            raise GraphQLError("Value must be a string.", extensions=extensions, path=path)

        value = node.value
        if not (5 <= len(value) <= 50):
            raise GraphQLError(
                f"String length must be between 5 and 50 characters.",
                extensions=extensions,
                path=path
            )
        if re.search(r"<[^>]+>", value):  
            raise GraphQLError(
                "HTML tags are not allowed.",
                extensions=extensions,
                path=path
            )
        return value


class NonSpecialCharacterString10_200(graphene.Scalar):
    """Custom String Scalar that enforces length constraints and allows letters, numbers, spaces, special characters, and emojis"""

    MIN_LENGTH = 10
    MAX_LENGTH = 200
    # Allows letters, numbers, spaces, common special characters, and emoji ranges (Unicode blocks)
    ALLOWED_PATTERN = re.compile(
        r"^[a-zA-Z0-9 !@#$%^&*()_+\-=\[\]{}|;':\",./<>?`~"
        r"\u00C0-\u017F"  # Latin Extended (accented characters)
        r"\u0100-\u024F"  # Latin Extended Additional
        r"\u1E00-\u1EFF"  # Latin Extended Additional
        r"\u2000-\u206F"  # General Punctuation
        r"\u2070-\u209F"  # Superscripts and Subscripts
        r"\u20A0-\u20CF"  # Currency Symbols
        r"\u2100-\u214F"  # Letterlike Symbols
        r"\u2190-\u21FF"  # Arrows
        r"\u2200-\u22FF"  # Mathematical Operators
        r"\u2300-\u23FF"  # Miscellaneous Technical
        r"\u2400-\u243F"  # Control Pictures
        r"\u2440-\u245F"  # Optical Character Recognition
        r"\u2460-\u24FF"  # Enclosed Alphanumerics
        r"\u2500-\u257F"  # Box Drawing
        r"\u2580-\u259F"  # Block Elements
        r"\u25A0-\u25FF"  # Geometric Shapes
        r"\u2600-\u26FF"  # Miscellaneous Symbols
        r"\u2700-\u27BF"  # Dingbats
        r"\U0001F000-\U0001F02F"  # Mahjong Tiles
        r"\U0001F030-\U0001F09F"  # Domino Tiles
        r"\U0001F0A0-\U0001F0FF"  # Playing Cards
        r"\U0001F100-\U0001F1FF"  # Enclosed Alphanumeric Supplement
        r"\U0001F200-\U0001F2FF"  # Enclosed Ideographic Supplement
        r"\U0001F300-\U0001F5FF"  # Miscellaneous Symbols and Pictographs
        r"\U0001F600-\U0001F64F"  # Emoticons
        r"\U0001F650-\U0001F67F"  # Ornamental Dingbats
        r"\U0001F680-\U0001F6FF"  # Transport and Map Symbols
        r"\U0001F700-\U0001F77F"  # Alchemical Symbols
        r"\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        r"\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        r"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        r"\U0001FA00-\U0001FA6F"  # Chess Symbols
        r"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        r"\u200D"  # Zero-Width Joiner (ZWJ) - for complex emoji sequences
        r"\uFE00-\uFE0F"  # Variation Selectors (VS15, VS16) - for emoji variations
        r"\u20E3"  # Combining Enclosing Keycap - for keycap emojis like 2️⃣
        r"]+$", re.UNICODE
    )

    @classmethod
    def add_option(cls, field_name, mutation_name=None):
        """Create a new class with the specified field name and mutation name"""
        # Create a unique class name that includes the mutation name if provided
        class_name = f"Custom{field_name.title().replace('_', '')}Validator"
        if mutation_name:
            class_name = f"{class_name}_{mutation_name}"
            
        return type(class_name, (cls,), {'field_name': field_name, 'mutation_name': mutation_name})
    
    field_name = "value"
    mutation_name = None

    def raise_error(self, message):
        """Helper function to raise GraphQLError with custom extensions"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if self.mutation_name:
            path.append(self.mutation_name)
        path.append(self.field_name)
        raise GraphQLError(message, extensions=extensions, path=path)

    def parse_value(self, value):
        """Handles values when passed as variables"""
        if not isinstance(value, str):
            self.raise_error(f"{self.field_name} must be a string.")
        if not (self.MIN_LENGTH <= len(value) <= self.MAX_LENGTH):
            self.raise_error(f"String length must be between {self.MIN_LENGTH} and {self.MAX_LENGTH} characters.")
        if not self.__class__.ALLOWED_PATTERN.match(value):
            self.raise_error(f"{self.field_name} must contain only letters, numbers, spaces, special characters, and emojis.")
        return value

    @classmethod
    def parse_literal(cls, node, _variables=None):
        """Handles inline literals in GraphQL queries"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if hasattr(cls, 'mutation_name') and cls.mutation_name:
            path.append(cls.mutation_name)
        path.append(cls.field_name)
            
        if not isinstance(node, ast.StringValueNode):
            raise GraphQLError("Value must be a string.", extensions=extensions, path=path)

        value = node.value
        if not (10 <= len(value) <= 200):
            raise GraphQLError(
                f"String length must be between 10 and 200 characters.",
                extensions=extensions,
                path=path
            )
        if re.search(r"<[^>]+>", value):  
            raise GraphQLError(
                "HTML tags are not allowed.",
                extensions=extensions,
                path=path
            )
        if not cls.ALLOWED_PATTERN.match(value):
            raise GraphQLError(
                "Value must contain only letters, numbers, spaces, special characters, and emojis.",
                extensions=extensions,
                path=path
            )
        return value


class NonSpecialCharacterString5_200(graphene.Scalar):
    """Custom String Scalar that enforces length constraints and allows letters, numbers, spaces, special characters, and emojis"""

    MIN_LENGTH = 5
    MAX_LENGTH = 200
    # Allows letters, numbers, spaces, common special characters, and emoji ranges (Unicode blocks)
    ALLOWED_PATTERN = re.compile(
        r"^[a-zA-Z0-9 !@#$%^&*()_+\-=\[\]{}|;':\",./<>?`~"
        r"\u00C0-\u017F"  # Latin Extended (accented characters)
        r"\u0100-\u024F"  # Latin Extended Additional
        r"\u1E00-\u1EFF"  # Latin Extended Additional
        r"\u2000-\u206F"  # General Punctuation
        r"\u2070-\u209F"  # Superscripts and Subscripts
        r"\u20A0-\u20CF"  # Currency Symbols
        r"\u2100-\u214F"  # Letterlike Symbols
        r"\u2190-\u21FF"  # Arrows
        r"\u2200-\u22FF"  # Mathematical Operators
        r"\u2300-\u23FF"  # Miscellaneous Technical
        r"\u2400-\u243F"  # Control Pictures
        r"\u2440-\u245F"  # Optical Character Recognition
        r"\u2460-\u24FF"  # Enclosed Alphanumerics
        r"\u2500-\u257F"  # Box Drawing
        r"\u2580-\u259F"  # Block Elements
        r"\u25A0-\u25FF"  # Geometric Shapes
        r"\u2600-\u26FF"  # Miscellaneous Symbols
        r"\u2700-\u27BF"  # Dingbats
        r"\U0001F000-\U0001F02F"  # Mahjong Tiles
        r"\U0001F030-\U0001F09F"  # Domino Tiles
        r"\U0001F0A0-\U0001F0FF"  # Playing Cards
        r"\U0001F100-\U0001F1FF"  # Enclosed Alphanumeric Supplement
        r"\U0001F200-\U0001F2FF"  # Enclosed Ideographic Supplement
        r"\U0001F300-\U0001F5FF"  # Miscellaneous Symbols and Pictographs
        r"\U0001F600-\U0001F64F"  # Emoticons
        r"\U0001F650-\U0001F67F"  # Ornamental Dingbats
        r"\U0001F680-\U0001F6FF"  # Transport and Map Symbols
        r"\U0001F700-\U0001F77F"  # Alchemical Symbols
        r"\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        r"\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        r"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        r"\U0001FA00-\U0001FA6F"  # Chess Symbols
        r"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        r"\u200D"  # Zero-Width Joiner (ZWJ) - for complex emoji sequences
        r"\uFE00-\uFE0F"  # Variation Selectors (VS15, VS16) - for emoji variations
        r"\u20E3"  # Combining Enclosing Keycap - for keycap emojis like 2️⃣
        r"]+$", re.UNICODE
    )

    @classmethod
    def add_option(cls, field_name, mutation_name=None):
        """Create a new class with the specified field name and mutation name"""
        # Create a unique class name that includes the mutation name if provided
        class_name = f"Custom{field_name.title().replace('_', '')}Validator"
        if mutation_name:
            class_name = f"{class_name}_{mutation_name}"

        return type(class_name, (cls,), {'field_name': field_name, 'mutation_name': mutation_name})

    field_name = "value"
    mutation_name = None

    def raise_error(self, message):
        """Helper function to raise GraphQLError with custom extensions"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if self.mutation_name:
            path.append(self.mutation_name)
        path.append(self.field_name)
        raise GraphQLError(message, extensions=extensions, path=path)

    def parse_value(self, value):
        """Handles values when passed as variables"""
        # Allow None for optional fields
        if value is None:
            return None

        if not isinstance(value, str):
            self.raise_error(f"{self.field_name} must be a string.")
        if not (self.MIN_LENGTH <= len(value) <= self.MAX_LENGTH):
            self.raise_error(f"String length must be between {self.MIN_LENGTH} and {self.MAX_LENGTH} characters.")
        if not self.__class__.ALLOWED_PATTERN.match(value):
            self.raise_error(f"{self.field_name} must contain only letters, numbers, spaces, special characters, and emojis.")
        return value

    @classmethod
    def parse_literal(cls, node, _variables=None):
        """Handles inline literals in GraphQL queries"""
        # Allow None for optional fields
        if node is None or (hasattr(node, 'value') and node.value is None):
            return None

        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if hasattr(cls, 'mutation_name') and cls.mutation_name:
            path.append(cls.mutation_name)
        path.append(cls.field_name)

        if not isinstance(node, ast.StringValueNode):
            raise GraphQLError("Value must be a string.", extensions=extensions, path=path)

        value = node.value
        if not (cls.MIN_LENGTH <= len(value) <= cls.MAX_LENGTH):
            raise GraphQLError(
                f"String length must be between {cls.MIN_LENGTH} and {cls.MAX_LENGTH} characters.",
                extensions=extensions,
                path=path
            )
        if re.search(r"<[^>]+>", value):
            raise GraphQLError(
                "HTML tags are not allowed.",
                extensions=extensions,
                path=path
            )
        if not cls.ALLOWED_PATTERN.match(value):
            raise GraphQLError(
                "Value must contain only letters, numbers, spaces, special characters, and emojis.",
                extensions=extensions,
                path=path
            )

        return value


class CreateCommunityDescriptionValidator(NonSpecialCharacterString10_200):
    """Custom validator for the 'description' field in CreateCommunity with specific error messages"""

    field_name = "description"
    mutation_name = "CreateCommunity"

    def raise_error(self, message):
        """Helper function to raise GraphQLError with custom extensions"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if self.mutation_name:
            path.append(self.mutation_name)
        path.append(self.field_name)
        raise GraphQLError(message, extensions=extensions, path=path)

    def parse_value(self, value):
        """Handles values when passed as variables"""
        if not isinstance(value, str):
            self.raise_error("description must be a string.")

        if not (self.MIN_LENGTH <= len(value) <= self.MAX_LENGTH):
            self.raise_error("description must be between 10 and 200 characters.")

        if not self.__class__.ALLOWED_PATTERN.match(value):
            self.raise_error("description must contain only letters, numbers, spaces, special characters, and emojis.")

        return value

    @classmethod
    def parse_literal(cls, node, _variables=None):
        """Handles inline literals in GraphQL queries"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if hasattr(cls, 'mutation_name') and cls.mutation_name:
            path.append(cls.mutation_name)
        path.append("description")

        if not isinstance(node, ast.StringValueNode):
            raise GraphQLError("description must be a string.", extensions=extensions, path=path)

        value = node.value
        if not (10 <= len(value) <= 200):
            raise GraphQLError(
                "description must be between 10 and 200 characters.",
                extensions=extensions,
                path=path
            )

        if re.search(r"<[^>]+>", value):
            raise GraphQLError(
                "HTML tags are not allowed.",
                extensions=extensions,
                path=path
            )

        if not cls.ALLOWED_PATTERN.match(value):
            raise GraphQLError(
                "description must contain only letters, numbers, spaces, special characters, and emojis.",
                extensions=extensions,
                path=path
            )

        return value


class CreateCommunityImageValidator(graphene.Scalar):
    """Custom validator for the 'image' field in CreateCommunity that allows null values"""

    field_name = "image"
    mutation_name = "CreateCommunity"

    def raise_error(self, message):
        """Helper function to raise GraphQLError with custom extensions"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if self.mutation_name:
            path.append(self.mutation_name)
        path.append(self.field_name)
        raise GraphQLError(message, extensions=extensions, path=path)

    def parse_value(self, value):
        """Handles values when passed as variables"""
        # Allow None for optional image field
        if value is None:
            return None

        if not isinstance(value, str):
            self.raise_error("image must be a string or null.")

        # Basic validation for image URLs or file paths
        if len(value.strip()) == 0:
            self.raise_error("image cannot be an empty string.")

        # Add any additional validation for image URLs if needed
        # For now, we'll allow any non-empty string as an image identifier
        return value

    @classmethod
    def parse_literal(cls, node, _variables=None):
        """Handles inline literals in GraphQL queries"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if hasattr(cls, 'mutation_name') and cls.mutation_name:
            path.append(cls.mutation_name)
        path.append("image")

        # Allow null values
        if node is None:
            return None

        if not isinstance(node, ast.StringValueNode):
            raise GraphQLError("image must be a string or null.", extensions=extensions, path=path)

        value = node.value
        if len(value.strip()) == 0:
            raise GraphQLError(
                "image cannot be an empty string.",
                extensions=extensions,
                path=path
            )

        return value


class SpecialCharacterString10_200(graphene.Scalar):
    """Custom String Scalar that enforces length constraints and allows letters, numbers, spaces, special characters, and emojis"""
    MIN_LENGTH = 10
    MAX_LENGTH = 200
    # Allows letters, numbers, spaces, common special characters, and emoji ranges (Unicode blocks)
    ALLOWED_PATTERN = re.compile(
        r"^[a-zA-Z0-9 !@#$%^&*()_+\-=\[\]{}|;':\",./<>?`~"
        r"\u00C0-\u017F"  # Latin Extended (accented characters)
        r"\u0100-\u024F"  # Latin Extended Additional
        r"\u1E00-\u1EFF"  # Latin Extended Additional
        r"\u2000-\u206F"  # General Punctuation
        r"\u2070-\u209F"  # Superscripts and Subscripts
        r"\u20A0-\u20CF"  # Currency Symbols
        r"\u2100-\u214F"  # Letterlike Symbols
        r"\u2190-\u21FF"  # Arrows
        r"\u2200-\u22FF"  # Mathematical Operators
        r"\u2300-\u23FF"  # Miscellaneous Technical
        r"\u2400-\u243F"  # Control Pictures
        r"\u2440-\u245F"  # Optical Character Recognition
        r"\u2460-\u24FF"  # Enclosed Alphanumerics
        r"\u2500-\u257F"  # Box Drawing
        r"\u2580-\u259F"  # Block Elements
        r"\u25A0-\u25FF"  # Geometric Shapes
        r"\u2600-\u26FF"  # Miscellaneous Symbols
        r"\u2700-\u27BF"  # Dingbats
        r"\U0001F000-\U0001F02F"  # Mahjong Tiles
        r"\U0001F030-\U0001F09F"  # Domino Tiles
        r"\U0001F0A0-\U0001F0FF"  # Playing Cards
        r"\U0001F100-\U0001F1FF"  # Enclosed Alphanumeric Supplement
        r"\U0001F200-\U0001F2FF"  # Enclosed Ideographic Supplement
        r"\U0001F300-\U0001F5FF"  # Miscellaneous Symbols and Pictographs
        r"\U0001F600-\U0001F64F"  # Emoticons
        r"\U0001F650-\U0001F67F"  # Ornamental Dingbats
        r"\U0001F680-\U0001F6FF"  # Transport and Map Symbols
        r"\U0001F700-\U0001F77F"  # Alchemical Symbols
        r"\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        r"\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        r"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        r"\U0001FA00-\U0001FA6F"  # Chess Symbols
        r"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        r"\u200D"  # Zero-Width Joiner (ZWJ) - for complex emoji sequences
        r"\uFE00-\uFE0F"  # Variation Selectors (VS15, VS16) - for emoji variations
        r"\u20E3"  # Combining Enclosing Keycap - for keycap emojis like 2️⃣
        r"]+$", re.UNICODE
    )

    @classmethod
    def add_option(cls, field_name, mutation_name=None):
        """Create a new class with the specified field name and mutation name"""
        # Create a unique class name that includes the mutation name if provided
        class_name = f"Custom{field_name.title().replace('_', '')}Validator"
        if mutation_name:
            class_name = f"{class_name}_{mutation_name}"
        return type(class_name, (cls,), {'field_name': field_name, 'mutation_name': mutation_name})

    field_name = "value"
    mutation_name = None

    def raise_error(self, message):
        """Helper function to raise GraphQLError with custom extensions"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if self.mutation_name:
            path.append(self.mutation_name)
        path.append(self.field_name)
        raise GraphQLError(message, extensions=extensions, path=path)

    def parse_value(self, value):
        """Handles values when passed as variables"""
        if not isinstance(value, str):
            self.raise_error(f"{self.field_name} must be a string.")
        
        if not (self.MIN_LENGTH <= len(value) <= self.MAX_LENGTH):
            self.raise_error(f"String length must be between {self.MIN_LENGTH} and {self.MAX_LENGTH} characters.")
        
        if not self.__class__.ALLOWED_PATTERN.match(value):
            self.raise_error(f"{self.field_name} must contain only letters, numbers, spaces, special characters, and emojis.")
        
        return value

    @classmethod
    def parse_literal(cls, node, _variables=None):
        """Handles inline literals in GraphQL queries"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if hasattr(cls, 'mutation_name') and cls.mutation_name:
            path.append(cls.mutation_name)
        path.append(cls.field_name)

        if not isinstance(node, ast.StringValueNode):
            raise GraphQLError("Value must be a string.", extensions=extensions, path=path)

        value = node.value
        if not (10 <= len(value) <= 200):
            raise GraphQLError(
                f"String length must be between 10 and 200 characters.",
                extensions=extensions,
                path=path
            )

        # Check for HTML tags (keeping the same validation as your NonSpecialCharacterString10_200)
        if re.search(r"<[^>]+>", value):
            raise GraphQLError(
                "HTML tags are not allowed.",
                extensions=extensions,
                path=path
            )

        # Use the same pattern as ALLOWED_PATTERN for consistency
        if not cls.ALLOWED_PATTERN.match(value):
            raise GraphQLError(
                "Value must contain only letters, numbers, spaces, special characters, and emojis.",
                extensions=extensions,
                path=path
            )

        return value    

class NonSpecialCharacterString2_100(graphene.Scalar):
    """Custom String Scalar that enforces length constraints and allows letters, numbers, spaces, emojis, and common punctuation"""

    MIN_LENGTH = 2
    MAX_LENGTH = 100
    # Allows letters, numbers, spaces, emojis, and common punctuation
    ALLOWED_PATTERN = re.compile(
        r"^[a-zA-Z0-9\s!\"#$%&'()*+,\-./:;<=>?@\[\\\]^_`{|}~"
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
        r"]+$",
        re.UNICODE
    )

    @classmethod
    def add_option(cls, field_name, mutation_name=None):
        """Create a new class with the specified field name and mutation name"""
        # Create a unique class name that includes the mutation name if provided
        class_name = f"Custom{field_name.title().replace('_', '')}Validator"
        if mutation_name:
            class_name = f"{class_name}_{mutation_name}"
            
        return type(class_name, (cls,), {'field_name': field_name, 'mutation_name': mutation_name})
    
    field_name = "value" 
    
    def raise_error(self, message):
        """Helper function to raise GraphQLError with custom extensions"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if self.mutation_name:
            path.append(self.mutation_name)
        path.append(self.field_name)
        raise GraphQLError(message, extensions=extensions, path=path)

    def parse_value(self, value):
        """Handles values when passed as variables"""
        # Allow None for optional fields
        if value is None:
            return None
            
        if not isinstance(value, str):
            self.raise_error(f"{self.field_name} must be a string.")
        if not (self.MIN_LENGTH <= len(value) <= self.MAX_LENGTH):
            self.raise_error(f"String length must be between {self.MIN_LENGTH} and {self.MAX_LENGTH} characters.")
        if not self.ALLOWED_PATTERN.match(value):
            self.raise_error(f"{self.field_name} must contain only letters. No special characters allowed.")
        return value

    @classmethod
    def parse_literal(cls, node, _variables=None):
        """Handles inline literals in GraphQL queries"""
        # Allow None for optional fields
        if node is None or (hasattr(node, 'value') and node.value is None):
            return None
            
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if hasattr(cls, 'mutation_name') and cls.mutation_name:
            path.append(cls.mutation_name)
        path.append(cls.field_name)
            
        if not isinstance(node, ast.StringValueNode):
            raise GraphQLError("Value must be a string.", extensions=extensions, path=path)

        value = node.value
        if not (cls.MIN_LENGTH <= len(value) <= cls.MAX_LENGTH):
            raise GraphQLError(
                f"String length must be between {cls.MIN_LENGTH} and {cls.MAX_LENGTH} characters.",
                extensions=extensions,
                path=path
            )
        if not cls.ALLOWED_PATTERN.match(value):
            raise GraphQLError(
                f"{cls.field_name} must contain only letters, numbers, spaces, emojis, and common punctuation.",
                extensions=extensions,
                path=path
            )
        return value

class NonSemiSpecialCharacterString2_100(graphene.Scalar):
    """Custom String Scalar that enforces length constraints and allows letters, numbers, spaces, and special characters"""

    MIN_LENGTH = 2
    MAX_LENGTH = 100
    ALLOWED_PATTERN = re.compile(r"^[a-zA-Z0-9 !@#$%^&*()_+\-=\[\]{}|;':\",./<>?`~]+$")  # Allows letters, numbers, spaces, and special characters

    @classmethod
    def add_option(cls, field_name, mutation_name=None):
        """Create a new class with the specified field name and mutation name"""
        # Create a unique class name that includes the mutation name if provided
        class_name = f"Custom{field_name.title().replace('_', '')}Validator"
        if mutation_name:
            class_name = f"{class_name}_{mutation_name}"
            
        return type(class_name, (cls,), {'field_name': field_name, 'mutation_name': mutation_name})
    
    field_name = "value" 
    
    def raise_error(self, message):
        """Helper function to raise GraphQLError with custom extensions"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if self.mutation_name:
            path.append(self.mutation_name)
        path.append(self.field_name)
        raise GraphQLError(message, extensions=extensions, path=path)

    def parse_value(self, value):
        """Handles values when passed as variables"""
        if not isinstance(value, str):
            self.raise_error(f"{self.field_name} must be a string.")
        if not (self.MIN_LENGTH <= len(value) <= self.MAX_LENGTH):
            self.raise_error(f"String length must be between {self.MIN_LENGTH} and {self.MAX_LENGTH} characters.")
        if not self.ALLOWED_PATTERN.match(value):
            self.raise_error(f"{self.field_name} must contain only letters, numbers, spaces, and special characters.")
        return value

    @classmethod
    def parse_literal(cls, node, _variables=None):
        """Handles inline literals in GraphQL queries"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if hasattr(cls, 'mutation_name') and cls.mutation_name:
            path.append(cls.mutation_name)
        path.append(cls.field_name)
            
        if not isinstance(node, ast.StringValueNode):
            raise GraphQLError("Value must be a string.", extensions=extensions, path=path)

        value = node.value
        if not (2 <= len(value) <= 100):
            raise GraphQLError(
                f"String length must be between 2 and 100 characters.",
                extensions=extensions,
                path=path
            )
        if not re.match(r"^[a-zA-ZÀ-ÖØ-öø-ÿ0-9 !@#$%^&*()_+\-=\[\]{}|;':\",./<>?`~]+$", value):
            raise GraphQLError(
                "Value must contain only letters, numbers, spaces, and special characters.",
                extensions=extensions,
                path=path
            )
        return value

class NonSpecialCharacterString2_200(graphene.Scalar):
    """Custom String Scalar that enforces length constraints and disallows special characters"""

    MIN_LENGTH = 2
    MAX_LENGTH = 200
    ALLOWED_PATTERN = re.compile(r"^[a-zA-Z ]+$")  # Allows only letters, numbers, and spaces
    
    @classmethod
    def add_option(cls, field_name, mutation_name=None):
        """Create a new class with the specified field name and mutation name"""
        # Create a unique class name that includes the mutation name if provided
        class_name = f"Custom{field_name.title().replace('_', '')}Validator"
        if mutation_name:
            class_name = f"{class_name}_{mutation_name}"
            
        return type(class_name, (cls,), {'field_name': field_name, 'mutation_name': mutation_name})
    
    field_name = "value" 
    
    def raise_error(self, message):
        """Helper function to raise GraphQLError with custom extensions"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if self.mutation_name:
            path.append(self.mutation_name)
        path.append(self.field_name)
        raise GraphQLError(message, extensions=extensions, path=path)

    def parse_value(self, value):
        """Handles values when passed as variables"""
        if not isinstance(value, str):
            self.raise_error("Value must be a string.")
        if not (self.MIN_LENGTH <= len(value) <= self.MAX_LENGTH):
            self.raise_error(f"String length must be between {self.MIN_LENGTH} and {self.MAX_LENGTH} characters.")
        if not self.ALLOWED_PATTERN.match(value):
            self.raise_error("Value must contain only letters. No special characters allowed.")
        return value

    @classmethod
    def parse_literal(cls, node, _variables=None):
        """Handles inline literals in GraphQL queries"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if hasattr(cls, 'mutation_name') and cls.mutation_name:
            path.append(cls.mutation_name)
        path.append(cls.field_name)
            
        if not isinstance(node, ast.StringValueNode):
            raise GraphQLError("Value must be a string.", extensions=extensions, path=path)

        value = node.value
        if not (2 <= len(value) <= 200):
            raise GraphQLError(
                f"String length must be between 2 and 200 characters.",
                extensions=extensions,
                path=path
            )
        if re.search(r"<[^>]+>", value):  
            raise GraphQLError(
                "HTML tags are not allowed.",
                extensions=extensions,
                path=path
            )
        return value

class SpecialCharacterString2_200(graphene.Scalar):
    """Custom String Scalar that enforces length constraints and allows letters, numbers, spaces, special characters, and emojis"""
    MIN_LENGTH = 2
    MAX_LENGTH = 200
    ALLOWED_PATTERN = re.compile(
        r"^[a-zA-Z0-9 !@#$%^&*()_+\-=\[\]{}|;':\",./<>?`~"
        r"\u00C0-\u017F"  # Latin Extended (accented characters)
        r"\u0100-\u024F"  # Latin Extended Additional
        r"\u1E00-\u1EFF"  # Latin Extended Additional
        r"\u2000-\u206F"  # General Punctuation
        r"\u2070-\u209F"  # Superscripts and Subscripts
        r"\u20A0-\u20CF"  # Currency Symbols
        r"\u2100-\u214F"  # Letterlike Symbols
        r"\u2190-\u21FF"  # Arrows
        r"\u2200-\u22FF"  # Mathematical Operators
        r"\u2300-\u23FF"  # Miscellaneous Technical
        r"\u2400-\u243F"  # Control Pictures
        r"\u2440-\u245F"  # Optical Character Recognition
        r"\u2460-\u24FF"  # Enclosed Alphanumerics
        r"\u2500-\u257F"  # Box Drawing
        r"\u2580-\u259F"  # Block Elements
        r"\u25A0-\u25FF"  # Geometric Shapes
        r"\u2600-\u26FF"  # Miscellaneous Symbols
        r"\u2700-\u27BF"  # Dingbats
        r"\uFE00-\uFE0F"
        r"\U0001F000-\U0001F02F"  # Mahjong Tiles
        r"\U0001F030-\U0001F09F"  # Domino Tiles
        r"\U0001F0A0-\U0001F0FF"  # Playing Cards
        r"\U0001F100-\U0001F1FF"  # Enclosed Alphanumeric Supplement
        r"\U0001F200-\U0001F2FF"  # Enclosed Ideographic Supplement
        r"\U0001F300-\U0001F5FF"  # Miscellaneous Symbols and Pictographs
        r"\U0001F600-\U0001F64F"  # Emoticons
        r"\U0001F650-\U0001F67F"  # Ornamental Dingbats
        r"\U0001F680-\U0001F6FF"  # Transport and Map Symbols
        r"\U0001F700-\U0001F77F"  # Alchemical Symbols
        r"\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        r"\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        r"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        r"\U0001FA00-\U0001FA6F"  # Chess Symbols
        r"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        r"\u200D"  # Zero-Width Joiner (ZWJ) - for complex emoji sequences
        r"\uFE00-\uFE0F"  # Variation Selectors (VS15, VS16) - for emoji variations
        r"\u20E3"  # Combining Enclosing Keycap - for keycap emojis like 2️⃣
        r"]+$", re.UNICODE
    )

    @classmethod
    def add_option(cls, field_name, mutation_name=None):
        """Create a new class with the specified field name and mutation name"""
        # Create a unique class name that includes the mutation name if provided
        class_name = f"Custom{field_name.title().replace('_', '')}Validator"
        if mutation_name:
            class_name = f"{class_name}_{mutation_name}"
        return type(class_name, (cls,), {'field_name': field_name, 'mutation_name': mutation_name})

    field_name = "value"

    def raise_error(self, message):
        """Helper function to raise GraphQLError with custom extensions"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if self.mutation_name:
            path.append(self.mutation_name)
        path.append(self.field_name)
        raise GraphQLError(message, extensions=extensions, path=path)

    def parse_value(self, value):
        """Handles values when passed as variables"""
        if not isinstance(value, str):
            self.raise_error("Value must be a string.")
        
        if not (self.MIN_LENGTH <= len(value) <= self.MAX_LENGTH):
            self.raise_error(f"String length must be between {self.MIN_LENGTH} and {self.MAX_LENGTH} characters.")
        
        if not self.__class__.ALLOWED_PATTERN.match(value):
            self.raise_error("Value must contain only letters, numbers, spaces, special characters, and emojis.")
        
        return value

    @classmethod
    def parse_literal(cls, node, _variables=None):
        """Handles inline literals in GraphQL queries"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if hasattr(cls, 'mutation_name') and cls.mutation_name:
            path.append(cls.mutation_name)
        path.append(cls.field_name)

        if not isinstance(node, ast.StringValueNode):
            raise GraphQLError("Value must be a string.", extensions=extensions, path=path)

        value = node.value
        if not (2 <= len(value) <= 200):
            raise GraphQLError(
                f"String length must be between 2 and 200 characters.",
                extensions=extensions,
                path=path
            )

        # Check for HTML tags (keeping your original validation)
        if re.search(r"<[^>]+>", value):
            raise GraphQLError(
                "HTML tags are not allowed.",
                extensions=extensions,
                path=path
            )

        # Use the same pattern as ALLOWED_PATTERN for consistency
        if not cls.ALLOWED_PATTERN.match(value):
            raise GraphQLError(
                "Value must contain only letters, numbers, spaces, special characters, and emojis.",
                extensions=extensions,
                path=path
            )

        return value 

class SpecialCharacterString2_100(graphene.Scalar):
    """Custom String Scalar that enforces length constraints and allows letters, numbers, spaces, special characters, and emojis"""
    MIN_LENGTH = 2
    MAX_LENGTH = 100
    ALLOWED_PATTERN = re.compile(
        r"^["
        r"a-zA-Z0-9 !@#$%^&*()_+\-=\[\]{}|;':\",./<>?`~"
        r"\u00C0-\u017F"  # Latin Extended (accented characters)
        r"\u0100-\u024F"  # Latin Extended Additional
        r"\u1E00-\u1EFF"  # Latin Extended Additional
        r"\u2000-\u206F"  # General Punctuation
        r"\u2070-\u209F"  # Superscripts and Subscripts
        r"\u20A0-\u20CF"  # Currency Symbols
        r"\u2100-\u214F"  # Letterlike Symbols
        r"\u2190-\u21FF"  # Arrows
        r"\u2200-\u22FF"  # Mathematical Operators
        r"\u2300-\u23FF"  # Miscellaneous Technical
        r"\u2400-\u243F"  # Control Pictures
        r"\u2440-\u245F"  # Optical Character Recognition
        r"\u2460-\u24FF"  # Enclosed Alphanumerics
        r"\u2500-\u257F"  # Box Drawing
        r"\u2580-\u259F"  # Block Elements
        r"\u25A0-\u25FF"  # Geometric Shapes
        r"\u2600-\u26FF"  # Miscellaneous Symbols
        r"\u2700-\u27BF"  # Dingbats
        r"\uFE00-\uFE0F"
        r"\U0001F000-\U0001F02F"  # Mahjong Tiles
        r"\U0001F030-\U0001F09F"  # Domino Tiles
        r"\U0001F0A0-\U0001F0FF"  # Playing Cards
        r"\U0001F100-\U0001F1FF"  # Enclosed Alphanumeric Supplement
        r"\U0001F200-\U0001F2FF"  # Enclosed Ideographic Supplement
        r"\U0001F300-\U0001F5FF"  # Miscellaneous Symbols and Pictographs
        r"\U0001F600-\U0001F64F"  # Emoticons
        r"\U0001F650-\U0001F67F"  # Ornamental Dingbats
        r"\U0001F680-\U0001F6FF"  # Transport and Map Symbols
        r"\U0001F700-\U0001F77F"  # Alchemical Symbols
        r"\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        r"\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        r"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        r"\U0001FA00-\U0001FA6F"  # Chess Symbols
        r"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        r"\u200D"  # Zero-Width Joiner (ZWJ) - for complex emoji sequences
        r"\uFE00-\uFE0F"  # Variation Selectors (VS15, VS16) - for emoji variations
        r"\u20E3"  # Combining Enclosing Keycap - for keycap emojis like 2️⃣
        r"]+$", re.UNICODE
    )

    @classmethod
    def add_option(cls, field_name, mutation_name=None):
        """Create a new class with the specified field name and mutation name"""
        # Create a unique class name that includes the mutation name if provided
        class_name = f"Custom{field_name.title().replace('_', '')}Validator"
        if mutation_name:
            class_name = f"{class_name}_{mutation_name}"
        
        # Create a new class that inherits from the original
        new_class = type(class_name, (cls,), {
            'field_name': field_name, 
            'mutation_name': mutation_name
        })
        
        # Override parse_value to be a class method that calls the instance method
        def class_parse_value(value):
            instance = new_class()
            return instance.parse_value(value)
        
        new_class.parse_value = class_parse_value
        return new_class

    field_name = "value"

    def raise_error(self, message):
        """Helper function to raise GraphQLError with custom extensions"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if self.mutation_name:
            path.append(self.mutation_name)
        path.append(self.field_name)
        raise GraphQLError(message, extensions=extensions, path=path)

    def parse_value(self, value):
        """Handles values when passed as variables"""
        # Allow None for optional fields
        if value is None:
            return None
            
        if not isinstance(value, str):
            self.raise_error(f"{self.field_name} must be a string.")
        
        if not (self.MIN_LENGTH <= len(value) <= self.MAX_LENGTH):
            self.raise_error(f"String length must be between {self.MIN_LENGTH} and {self.MAX_LENGTH} characters.")
        
        if not self.__class__.ALLOWED_PATTERN.match(value):
            self.raise_error(f"{self.field_name} must contain only letters, numbers, spaces, special characters, and emojis.")
        
        return value

    @classmethod
    def parse_literal(cls, node, _variables=None):
        """Handles inline literals in GraphQL queries"""
        # Allow None for optional fields
        if node is None or (hasattr(node, 'value') and node.value is None):
            return None
            
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if hasattr(cls, 'mutation_name') and cls.mutation_name:
            path.append(cls.mutation_name)
        path.append(cls.field_name)

        if not isinstance(node, ast.StringValueNode):
            raise GraphQLError("Value must be a string.", extensions=extensions, path=path)

        value = node.value
        if not (2 <= len(value) <= 100):
            raise GraphQLError(
                f"String length must be between 2 and 100 characters.",
                extensions=extensions,
                path=path
            )

        if not cls.ALLOWED_PATTERN.match(value):
            raise GraphQLError(
                "Value must contain only letters, numbers, spaces, special characters, and emojis.",
                extensions=extensions,
                path=path
            )

        return value

    
class SpecialCharacterString2_200(graphene.Scalar):
    """Custom String Scalar that enforces length constraints and allows letters, numbers, spaces, special characters, and emojis"""
    MIN_LENGTH = 2
    MAX_LENGTH = 200
    # CORRECTED pattern using \U00000000 format for emoji ranges
    ALLOWED_PATTERN = re.compile(
        r"^[a-zA-Z0-9 !@#$%^&*()_+\-=\[\]{}|;':\",./<>?`~"
        r"\u00C0-\u017F"  # Latin Extended (accented characters)
        r"\u0100-\u024F"  # Latin Extended Additional
        r"\u1E00-\u1EFF"  # Latin Extended Additional
        r"\u2000-\u206F"  # General Punctuation
        r"\u2070-\u209F"  # Superscripts and Subscripts
        r"\u20A0-\u20CF"  # Currency Symbols
        r"\u2100-\u214F"  # Letterlike Symbols
        r"\u2190-\u21FF"  # Arrows
        r"\u2200-\u22FF"  # Mathematical Operators
        r"\u2300-\u23FF"  # Miscellaneous Technical
        r"\u2400-\u243F"  # Control Pictures0
        r"\u2440-\u245F"  # Optical Character Recognition
        r"\u2460-\u24FF"  # Enclosed Alphanumerics
        r"\u2500-\u257F"  # Box Drawing
        r"\u2580-\u259F"  # Block Elements
        r"\u25A0-\u25FF"  # Geometric Shapes
        r"\u2600-\u26FF"  # Miscellaneous Symbols
        r"\u2700-\u27BF"  # Dingbats
        r"\U0001F000-\U0001F02F"  # Mahjong Tiles
        r"\U0001F030-\U0001F09F"  # Domino Tiles
        r"\U0001F0A0-\U0001F0FF"  # Playing Cards
        r"\U0001F100-\U0001F1FF"  # Enclosed Alphanumeric Supplement
        r"\U0001F200-\U0001F2FF"  # Enclosed Ideographic Supplement
        r"\U0001F300-\U0001F5FF"  # Miscellaneous Symbols and Pictographs
        r"\U0001F600-\U0001F64F"  # Emoticons
        r"\U0001F650-\U0001F67F"  # Ornamental Dingbats
        r"\U0001F680-\U0001F6FF"  # Transport and Map Symbols
        r"\U0001F700-\U0001F77F"  # Alchemical Symbols
        r"\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        r"\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        r"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        r"\U0001FA00-\U0001FA6F"  # Chess Symbols
        r"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        r"\u200D"  # Zero-Width Joiner (ZWJ) - for complex emoji sequences
        r"\uFE00-\uFE0F"  # Variation Selectors (VS15, VS16) - for emoji variations
        r"\u20E3"  # Combining Enclosing Keycap - for keycap emojis like 2️⃣
        r"]+$", re.UNICODE
    )

    @classmethod
    def add_option(cls, field_name, mutation_name=None):
        """Create a new class with the specified field name and mutation name"""
        # Create a unique class name that includes the mutation name if provided
        class_name = f"Custom{field_name.title().replace('_', '')}Validator"
        if mutation_name:
            class_name = f"{class_name}_{mutation_name}"
        return type(class_name, (cls,), {'field_name': field_name, 'mutation_name': mutation_name})

    field_name = "value"

    def raise_error(self, message):
        """Helper function to raise GraphQLError with custom extensions"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if self.mutation_name:
            path.append(self.mutation_name)
        path.append(self.field_name)
        raise GraphQLError(message, extensions=extensions, path=path)

    def parse_value(self, value):
        """Handles values when passed as variables"""
        if not isinstance(value, str):
            self.raise_error("Value must be a string.")
        
        if not (self.MIN_LENGTH <= len(value) <= self.MAX_LENGTH):
            self.raise_error(f"String length must be between {self.MIN_LENGTH} and {self.MAX_LENGTH} characters.")
        
        if not self.__class__.ALLOWED_PATTERN.match(value):
            self.raise_error("Value must contain only letters, numbers, spaces, special characters, and emojis.")
        
        return value

    @classmethod
    def parse_literal(cls, node, _variables=None):
        """Handles inline literals in GraphQL queries"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if hasattr(cls, 'mutation_name') and cls.mutation_name:
            path.append(cls.mutation_name)
        path.append(cls.field_name)

        if not isinstance(node, ast.StringValueNode):
            raise GraphQLError("Value must be a string.", extensions=extensions, path=path)

        value = node.value
        if not (2 <= len(value) <= 200):
            raise GraphQLError(
                f"String length must be between 2 and 200 characters.",
                extensions=extensions,
                path=path
            )

        # Check for HTML tags (keeping your original validation)
        if re.search(r"<[^>]+>", value):
            raise GraphQLError(
                "HTML tags are not allowed.",
                extensions=extensions,
                path=path
            )

        # Use the same pattern as ALLOWED_PATTERN for consistency
        if not cls.ALLOWED_PATTERN.match(value):
            raise GraphQLError(
                "Value must contain only letters, numbers, spaces, special characters, and emojis.",
                extensions=extensions,
                path=path
            )

        return value    
    
class SpecialCharacterString5_200(graphene.Scalar):
    """Custom String Scalar that enforces length constraints and allows letters, numbers, spaces, special characters, and emojis"""
    MIN_LENGTH = 5
    MAX_LENGTH = 200
    ALLOWED_PATTERN = re.compile(
        r"^[a-zA-Z0-9 !@#$%^&*()_+\-=\[\]{}|;':\",./<>?`~"
        r"\u00C0-\u017F"  # Latin Extended (accented characters)
        r"\u0100-\u024F"  # Latin Extended Additional
        r"\u1E00-\u1EFF"  # Latin Extended Additional
        r"\u2000-\u206F"  # General Punctuation
        r"\u2070-\u209F"  # Superscripts and Subscripts
        r"\u20A0-\u20CF"  # Currency Symbols
        r"\u2100-\u214F"  # Letterlike Symbols
        r"\u2190-\u21FF"  # Arrows
        r"\u2200-\u22FF"  # Mathematical Operators
        r"\u2300-\u23FF"  # Miscellaneous Technical
        r"\u2400-\u243F"  # Control Pictures
        r"\u2440-\u245F"  # Optical Character Recognition
        r"\u2460-\u24FF"  # Enclosed Alphanumerics
        r"\u2500-\u257F"  # Box Drawing
        r"\u2580-\u259F"  # Block Elements
        r"\u25A0-\u25FF"  # Geometric Shapes
        r"\u2600-\u26FF"  # Miscellaneous Symbols
        r"\u2700-\u27BF"  # Dingbats
        r"\U0001F000-\U0001F02F"  # Mahjong Tiles
        r"\U0001F030-\U0001F09F"  # Domino Tiles
        r"\U0001F0A0-\U0001F0FF"  # Playing Cards
        r"\U0001F100-\U0001F1FF"  # Enclosed Alphanumeric Supplement
        r"\U0001F200-\U0001F2FF"  # Enclosed Ideographic Supplement
        r"\U0001F300-\U0001F5FF"  # Miscellaneous Symbols and Pictographs
        r"\U0001F600-\U0001F64F"  # Emoticons
        r"\U0001F650-\U0001F67F"  # Ornamental Dingbats
        r"\U0001F680-\U0001F6FF"  # Transport and Map Symbols
        r"\U0001F700-\U0001F77F"  # Alchemical Symbols
        r"\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        r"\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        r"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        r"\U0001FA00-\U0001FA6F"  # Chess Symbols
        r"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        r"\u200D"  # Zero-Width Joiner (ZWJ) - for complex emoji sequences
        r"\uFE00-\uFE0F"  # Variation Selectors (VS15, VS16) - for emoji variations
        r"\u20E3"  # Combining Enclosing Keycap - for keycap emojis like 2️⃣
        r"]+$", re.UNICODE
    )

    @classmethod
    def add_option(cls, field_name, mutation_name=None):
        """Create a new class with the specified field name and mutation name"""
        # Create a unique class name that includes the mutation name if provided
        class_name = f"Custom{field_name.title().replace('_', '')}Validator"
        if mutation_name:
            class_name = f"{class_name}_{mutation_name}"
        return type(class_name, (cls,), {'field_name': field_name, 'mutation_name': mutation_name})

    field_name = "value"
    mutation_name = None

    def raise_error(self, message):
        """Helper function to raise GraphQLError with custom extensions"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if self.mutation_name:
            path.append(self.mutation_name)
        path.append(self.field_name)
        raise GraphQLError(message, extensions=extensions, path=path)

    def parse_value(self, value):
        """Handles values when passed as variables"""
        # Allow None for optional fields
        if value is None:
            return None
            
        if not isinstance(value, str):
            self.raise_error("Value must be a string.")

        if not (self.MIN_LENGTH <= len(value) <= self.MAX_LENGTH):
            self.raise_error(f"String length must be between {self.MIN_LENGTH} and {self.MAX_LENGTH} characters.")

        if not self.__class__.ALLOWED_PATTERN.match(value):
            self.raise_error("Value must contain only letters, numbers, spaces, special characters, and emojis.")

        return value

    @classmethod
    def parse_literal(cls, node, _variables=None):
        """Handles inline literals in GraphQL queries"""
        # Allow None for optional fields
        if node is None or (hasattr(node, 'value') and node.value is None):
            return None
            
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if hasattr(cls, 'mutation_name') and cls.mutation_name:
            path.append(cls.mutation_name)
        path.append(cls.field_name)

        if not isinstance(node, ast.StringValueNode):
            raise GraphQLError("Value must be a string.", extensions=extensions, path=path)

        value = node.value
        if not (5 <= len(value) <= 200):
            raise GraphQLError(
                f"String length must be between 5 and 200 characters.",
                extensions=extensions,
                path=path
            )

        # Check for HTML tags
        if re.search(r"<[^>]+>", value):
            raise GraphQLError(
                "HTML tags are not allowed.",
                extensions=extensions,
                path=path
            )

        # Use the same pattern as ALLOWED_PATTERN for consistency
        if not cls.ALLOWED_PATTERN.match(value):
            raise GraphQLError(
                "Value must contain only letters, numbers, spaces, special characters, and emojis.",
                extensions=extensions,
                path=path
            )

        return value
    
class SpecialCharacterString2_500(graphene.Scalar):
    """Custom String Scalar that enforces length constraints and allows letters, numbers, spaces, special characters, and emojis"""
    MIN_LENGTH = 2
    MAX_LENGTH = 200
    ALLOWED_PATTERN = re.compile(
        r"^[a-zA-Z0-9 !@#$%^&*()_+\-=\[\]{}|;':\",./<>?`~"
        r"\u00C0-\u017F"  # Latin Extended (accented characters)
        r"\u0100-\u024F"  # Latin Extended Additional
        r"\u1E00-\u1EFF"  # Latin Extended Additional
        r"\u2000-\u206F"  # General Punctuation
        r"\u2070-\u209F"  # Superscripts and Subscripts
        r"\u20A0-\u20CF"  # Currency Symbols
        r"\u2100-\u214F"  # Letterlike Symbols
        r"\u2190-\u21FF"  # Arrows
        r"\u2200-\u22FF"  # Mathematical Operators
        r"\u2300-\u23FF"  # Miscellaneous Technical
        r"\u2400-\u243F"  # Control Pictures
        r"\u2440-\u245F"  # Optical Character Recognition
        r"\u2460-\u24FF"  # Enclosed Alphanumerics
        r"\u2500-\u257F"  # Box Drawing
        r"\u2580-\u259F"  # Block Elements
        r"\u25A0-\u25FF"  # Geometric Shapes
        r"\u2600-\u26FF"  # Miscellaneous Symbols
        r"\u2700-\u27BF"  # Dingbats
        r"\U0001F000-\U0001F02F"  # Mahjong Tiles
        r"\U0001F030-\U0001F09F"  # Domino Tiles
        r"\U0001F0A0-\U0001F0FF"  # Playing Cards
        r"\U0001F100-\U0001F1FF"  # Enclosed Alphanumeric Supplement
        r"\U0001F200-\U0001F2FF"  # Enclosed Ideographic Supplement
        r"\U0001F300-\U0001F5FF"  # Miscellaneous Symbols and Pictographs
        r"\U0001F600-\U0001F64F"  # Emoticons
        r"\U0001F650-\U0001F67F"  # Ornamental Dingbats
        r"\U0001F680-\U0001F6FF"  # Transport and Map Symbols
        r"\U0001F700-\U0001F77F"  # Alchemical Symbols
        r"\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        r"\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        r"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        r"\U0001FA00-\U0001FA6F"  # Chess Symbols
        r"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        r"\u200D"  # Zero-Width Joiner (ZWJ) - for complex emoji sequences
        r"\uFE00-\uFE0F"  # Variation Selectors (VS15, VS16) - for emoji variations
        r"\u20E3"  # Combining Enclosing Keycap - for keycap emojis like 2️⃣
        r"]+$", re.UNICODE
    )

    @classmethod
    def add_option(cls, field_name, mutation_name=None):
        """Create a new class with the specified field name and mutation name"""
        # Create a unique class name that includes the mutation name if provided
        class_name = f"Custom{field_name.title().replace('_', '')}Validator"
        if mutation_name:
            class_name = f"{class_name}_{mutation_name}"
        return type(class_name, (cls,), {'field_name': field_name, 'mutation_name': mutation_name})

    field_name = "value"
    mutation_name = None

    def raise_error(self, message):
        """Helper function to raise GraphQLError with custom extensions"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if self.mutation_name:
            path.append(self.mutation_name)
        path.append(self.field_name)
        raise GraphQLError(message, extensions=extensions, path=path)

    def parse_value(self, value):
        """Handles values when passed as variables"""
        if not isinstance(value, str):
            self.raise_error(f"{self.field_name} must be a string.")
        
        if not (self.MIN_LENGTH <= len(value) <= self.MAX_LENGTH):
            self.raise_error(f"String length must be between {self.MIN_LENGTH} and {self.MAX_LENGTH} characters.")
        
        if not self.__class__.ALLOWED_PATTERN.match(value):
            self.raise_error(f"{self.field_name} must contain only letters, numbers, spaces, special characters, and emojis.")
        
        return value

    @classmethod
    def parse_literal(cls, node, _variables=None):
        """Handles inline literals in GraphQL queries"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if hasattr(cls, 'mutation_name') and cls.mutation_name:
            path.append(cls.mutation_name)
        path.append(cls.field_name)

        if not isinstance(node, ast.StringValueNode):
            raise GraphQLError("Value must be a string.", extensions=extensions, path=path)

        value = node.value
        if not (2 <= len(value) <= 500):
            raise GraphQLError(
                f"String length must be between 2 and 500 characters.",
                extensions=extensions,
                path=path
            )

        # Use the same pattern as ALLOWED_PATTERN for consistency
        if not cls.ALLOWED_PATTERN.match(value):
            raise GraphQLError(
                "Value must contain only letters, numbers, spaces, special characters, and emojis.",
                extensions=extensions,
                path=path
            )

        return value    
class UsernameString6_15(graphene.Scalar):
    """Custom String Scalar that enforces length constraints for usernames"""
    MIN_LENGTH = 6
    MAX_LENGTH = 15
    ALLOWED_PATTERN = re.compile(r"^[a-zA-Z0-9_]+$")  # Allows letters, numbers, and underscores

    @classmethod
    def add_option(cls, field_name, mutation_name=None):
        """Create a new class with the specified field name and mutation name"""
        class_name = f"Custom{field_name.title().replace('_', '')}Validator"
        if mutation_name:
            class_name = f"{class_name}_{mutation_name}"
        return type(class_name, (cls,), {'field_name': field_name, 'mutation_name': mutation_name})

    field_name = "username"
    mutation_name = None

    def raise_error(self, message):
        """Helper function to raise GraphQLError with custom extensions"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if self.mutation_name:
            path.append(self.mutation_name)
        path.append(self.field_name)
        raise GraphQLError(message, extensions=extensions, path=path)

    def parse_value(self, value):
        """Handles values when passed as variables"""
        if not isinstance(value, str):
            self.raise_error(f"{self.field_name} must be a string.")
        if not (self.MIN_LENGTH <= len(value) <= self.MAX_LENGTH):
            self.raise_error(f"Username length must be between {self.MIN_LENGTH} and {self.MAX_LENGTH} characters.")
        if not self.ALLOWED_PATTERN.match(value):
            self.raise_error(f"{self.field_name} must contain only letters, numbers, and underscores.")
        return value

    @classmethod
    def parse_literal(cls, node, _variables=None):
        """Handles inline literals in GraphQL queries"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if hasattr(cls, 'mutation_name') and cls.mutation_name:
            path.append(cls.mutation_name)
        path.append(cls.field_name)

        if not isinstance(node, ast.StringValueNode):
            raise GraphQLError(f"{cls.field_name} must be a string.", extensions=extensions, path=path)

        value = node.value
        if not (cls.MIN_LENGTH <= len(value) <= cls.MAX_LENGTH):
            raise GraphQLError(
                f"Username length must be between {cls.MIN_LENGTH} and {cls.MAX_LENGTH} characters.",
                extensions=extensions,
                path=path,
            )
        if not re.match(r"^[a-zA-Z0-9_]+$", value):
            raise GraphQLError(
                f"{cls.field_name} must contain only letters, numbers, and underscores.",
                extensions=extensions,
                path=path,
            )
        return value


class UsernameString3_30(graphene.Scalar):
    """Custom String Scalar for community/subcommunity usernames (3-30 characters)"""
    MIN_LENGTH = 3
    MAX_LENGTH = 30
    ALLOWED_PATTERN = re.compile(r"^[a-zA-Z0-9_]+$")  # Allows letters, numbers, and underscores

    @classmethod
    def add_option(cls, field_name, mutation_name=None):
        """Create a new class with the specified field name and mutation name"""
        class_name = f"Custom{field_name.title().replace('_', '')}Validator"
        if mutation_name:
            class_name = f"{class_name}_{mutation_name}"
        return type(class_name, (cls,), {'field_name': field_name, 'mutation_name': mutation_name})

    field_name = "username"
    mutation_name = None

    def raise_error(self, message):
        """Helper function to raise GraphQLError with custom extensions"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if self.mutation_name:
            path.append(self.mutation_name)
        path.append(self.field_name)
        raise GraphQLError(message, extensions=extensions, path=path)

    def parse_value(self, value):
        """Handles values when passed as variables"""
        if not isinstance(value, str):
            self.raise_error(f"{self.field_name} must be a string.")
        if not (self.MIN_LENGTH <= len(value) <= self.MAX_LENGTH):
            self.raise_error(f"Username length must be between {self.MIN_LENGTH} and {self.MAX_LENGTH} characters.")
        if not self.ALLOWED_PATTERN.match(value):
            self.raise_error(f"{self.field_name} must contain only letters, numbers, and underscores.")
        return value

    @classmethod
    def parse_literal(cls, node, _variables=None):
        """Handles inline literals in GraphQL queries"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if hasattr(cls, 'mutation_name') and cls.mutation_name:
            path.append(cls.mutation_name)
        path.append(cls.field_name)

        if not isinstance(node, ast.StringValueNode):
            raise GraphQLError(f"{cls.field_name} must be a string.", extensions=extensions, path=path)

        value = node.value
        if not (cls.MIN_LENGTH <= len(value) <= cls.MAX_LENGTH):
            raise GraphQLError(
                f"Username length must be between {cls.MIN_LENGTH} and {cls.MAX_LENGTH} characters.",
                extensions=extensions,
                path=path,
            )
        if not re.match(r"^[a-zA-Z0-9_]+$", value):
            raise GraphQLError(
                f"{cls.field_name} must contain only letters, numbers, and underscores.",
                extensions=extensions,
                path=path,
            )
        return value


class PhoneNumberScalar(graphene.Scalar):
    """Custom Scalar for validating Indian phone numbers"""

    PHONE_PATTERN = re.compile(r"^\+91[6-9]\d{9}$")  
    # +91 followed by 10 digits, first digit between 6-9

    @classmethod
    def add_option(cls, field_name, mutation_name=None):
        """Create a new class with the specified field name and mutation name"""
        class_name = f"Custom{field_name.title().replace('_', '')}Validator"
        if mutation_name:
            class_name = f"{class_name}_{mutation_name}"
            
        return type(class_name, (cls,), {'field_name': field_name, 'mutation_name': mutation_name})
    
    field_name = "value" 
    mutation_name = None
    
    def raise_error(self, message):
        """Helper function to raise GraphQLError with custom extensions"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if self.mutation_name:
            path.append(self.mutation_name)
        path.append(self.field_name)
        raise GraphQLError(message, extensions=extensions, path=path)

    def parse_value(self, value):
        """Handles values when passed as variables"""
        if not isinstance(value, str):
            self.raise_error(f"{self.field_name} must be a string.")
        if not self.PHONE_PATTERN.match(value):
            self.raise_error("Invalid Indian phone number. Must be in format +91XXXXXXXXXX and start with 6-9.")
        return value

    @classmethod
    def parse_literal(cls, node, _variables=None):
        """Handles inline literals in GraphQL queries"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if hasattr(cls, 'mutation_name') and cls.mutation_name:
            path.append(cls.mutation_name)
        path.append(cls.field_name)
            
        if not isinstance(node, ast.StringValueNode):
            raise GraphQLError("Phone number must be a string.", extensions=extensions, path=path)

        value = node.value
        if not re.match(r"^\+91[6-9]\d{9}$", value):
            raise GraphQLError(
                "Invalid Indian phone number. Must be in format +91XXXXXXXXXX and start with 6-9.",
                extensions=extensions,
                path=path
            )
        return value
class DateTimeScalar(graphene.Scalar):
    """Custom Scalar for validating DateTime in ISO 8601 format (YYYY-MM-DDThh:mm:ss) or date-only format (YYYY-MM-DD)"""

    # Pattern for ISO 8601 format: YYYY-MM-DDThh:mm:ss
    ISO_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")
    # Pattern for date-only format: YYYY-MM-DD
    DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    @classmethod
    def add_option(cls, field_name, mutation_name=None):
        """Create a new class with the specified field name and mutation name"""
        # Create a unique class name that includes the mutation name if provided
        class_name = f"Custom{field_name.title().replace('_', '')}Validator"
        if mutation_name:
            class_name = f"{class_name}_{mutation_name}"
            
        return type(class_name, (cls,), {'field_name': field_name, 'mutation_name': mutation_name})
    
    field_name = "value" 
    mutation_name = None
    
    def raise_error(self, message):
        """Helper function to raise GraphQLError with custom extensions"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if self.mutation_name:
            path.append(self.mutation_name)
        path.append(self.field_name)
        raise GraphQLError(message, extensions=extensions, path=path)

    def parse_value(self, value):
        """Handles values when passed as variables"""
        from datetime import datetime

        # Allow None for optional fields
        if value is None:
            return None

        if not isinstance(value, str):
            self.raise_error(f"{self.field_name} must be a string.")

        # Check if it matches date-only format (YYYY-MM-DD)
        if self.DATE_PATTERN.match(value):
            try:
                # Convert date-only string to datetime object with time 00:00:00
                return datetime.strptime(value, "%Y-%m-%d")
            except ValueError as e:
                self.raise_error(f"Invalid date: {str(e)}")
        
        # Check if it matches the ISO 8601 format
        elif self.ISO_PATTERN.match(value):
            try:
                # Convert string to datetime object
                return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
            except ValueError as e:
                self.raise_error(f"Invalid datetime: {str(e)}")
        
        else:
            self.raise_error(f"Invalid datetime format. Must be YYYY-MM-DD or ISO 8601 format (YYYY-MM-DDThh:mm:ss).")

    @classmethod
    def parse_literal(cls, node, _variables=None):
        """Handles inline literals in GraphQL queries"""
        from datetime import datetime

        # Allow None for optional fields
        if node is None or (hasattr(node, 'value') and node.value is None):
            return None

        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if hasattr(cls, 'mutation_name') and cls.mutation_name:
            path.append(cls.mutation_name)
        path.append(cls.field_name)

        if not isinstance(node, ast.StringValueNode):
            raise GraphQLError("DateTime must be a string.", extensions=extensions, path=path)

        value = node.value
        
        # Check if it matches date-only format (YYYY-MM-DD)
        if cls.DATE_PATTERN.match(value):
            try:
                # Convert date-only string to datetime object with time 00:00:00
                return datetime.strptime(value, "%Y-%m-%d")
            except ValueError as e:
                raise GraphQLError(
                    f"Invalid date: {str(e)}",
                    extensions=extensions,
                    path=path
                )
        
        # Check if it matches the ISO 8601 format
        elif cls.ISO_PATTERN.match(value):
            try:
                # Convert string to datetime object
                return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
            except ValueError as e:
                raise GraphQLError(
                    f"Invalid datetime: {str(e)}",
                    extensions=extensions,
                    path=path
                )
        
        else:
            raise GraphQLError(
                f"Invalid datetime format. Must be YYYY-MM-DD or ISO 8601 format (YYYY-MM-DDThh:mm:ss).",
                extensions=extensions,
                path=path
            )

class Int(graphene.Scalar):
    """Custom Int Scalar that validates int values"""
    @classmethod
    def add_option(cls, field_name, mutation_name=None):
        """Create a new class with the specified field name and mutation name"""
        # Create a unique class name that includes the mutation name if provided
        class_name = f"Custom{field_name.title().replace('_', '')}Validator"
        if mutation_name:
            class_name = f"{class_name}_{mutation_name}"
            
        return type(class_name, (cls,), {'field_name': field_name, 'mutation_name': mutation_name})
    
    field_name = "value"
    mutation_name = None

    def raise_error(self, message):
        """Helper function to raise GraphQLError with custom extensions"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if self.mutation_name:
            path.append(self.mutation_name)
        path.append(self.field_name)
        raise GraphQLError(message, extensions=extensions, path=path)

    def parse_value(self, value):
        """Handles values when passed as variables"""
        if not isinstance(value, int):
            self.raise_error(f"{self.field_name} must be an int.")
        return value

    @classmethod
    def parse_literal(cls, node, _variables=None):
        """Handles inline literals in GraphQL queries"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if hasattr(cls, 'mutation_name') and cls.mutation_name:
            path.append(cls.mutation_name)
        path.append(cls.field_name)
        
        if not isinstance(node, (ast.IntValueNode, ast.FloatValueNode)):
            raise GraphQLError(f"{cls.field_name} must be an int.", extensions=extensions, path=path)

        try:
            return int(node.value)
        except ValueError:
            raise GraphQLError(f"Invalid int format for {cls.field_name}.", extensions=extensions, path=path)

class ListString(graphene.Scalar):
    """Custom List Scalar that validates list of string values"""
    @classmethod
    def add_option(cls, field_name, mutation_name=None):
        """Create a new class with the specified field name and mutation name"""
        # Create a unique class name that includes the mutation name if provided
        class_name = f"Custom{field_name.title().replace('_', '')}Validator"
        if mutation_name:
            class_name = f"{class_name}_{mutation_name}"
            
        return type(class_name, (cls,), {'field_name': field_name, 'mutation_name': mutation_name})
    
    field_name = "value"
    mutation_name = None

    def raise_error(self, message):
        """Helper function to raise GraphQLError with custom extensions"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if self.mutation_name:
            path.append(self.mutation_name)
        path.append(self.field_name)
        raise GraphQLError(message, extensions=extensions, path=path)

    def parse_value(self, value):
        """Handles values when passed as variables"""
        if not isinstance(value, list):
            self.raise_error(f"{self.field_name} must be a list.")
        
        # Validate each item in the list is a string
        for item in value:
            if not isinstance(item, str):
                self.raise_error(f"All items in {self.field_name} must be strings.")
        return value

    @classmethod
    def parse_literal(cls, node, _variables=None):
        """Handles inline literals in GraphQL queries"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if hasattr(cls, 'mutation_name') and cls.mutation_name:
            path.append(cls.mutation_name)
        path.append(cls.field_name)
        
        if not isinstance(node, ast.ListValueNode):
            raise GraphQLError(f"{cls.field_name} must be a list.", extensions=extensions, path=path)

        # Validate each item in the list is a string
        values = []
        for item in node.values:
            if not isinstance(item, ast.StringValueNode):
                raise GraphQLError(
                    f"All items in {cls.field_name} must be strings.",
                    extensions=extensions,
                    path=path
                )
            values.append(item.value)
        return values
    
    
class SpecialCharacterString2_50(graphene.Scalar):
    """Custom String Scalar that enforces length constraints and allows letters, numbers, spaces, special characters, and emojis"""
    MIN_LENGTH = 2
    MAX_LENGTH = 50
    ALLOWED_PATTERN = re.compile(
        r"^[a-zA-Z0-9 !@#$%^&*()_+\-=\[\]{}|;':\",./<>?`~"
        r"\u00C0-\u017F"  # Latin Extended (accented characters)
        r"\u0100-\u024F"  # Latin Extended Additional
        r"\u1E00-\u1EFF"  # Latin Extended Additional
        r"\u2000-\u206F"  # General Punctuation
        r"\u2070-\u209F"  # Superscripts and Subscripts
        r"\u20A0-\u20CF"  # Currency Symbols
        r"\u2100-\u214F"  # Letterlike Symbols
        r"\u2190-\u21FF"  # Arrows
        r"\u2200-\u22FF"  # Mathematical Operators
        r"\u2300-\u23FF"  # Miscellaneous Technical
        r"\u2400-\u243F"  # Control Pictures
        r"\u2440-\u245F"  # Optical Character Recognition
        r"\u2460-\u24FF"  # Enclosed Alphanumerics
        r"\u2500-\u257F"  # Box Drawing
        r"\u2580-\u259F"  # Block Elements
        r"\u25A0-\u25FF"  # Geometric Shapes
        r"\u2600-\u26FF"  # Miscellaneous Symbols
        r"\u2700-\u27BF"  # Dingbats
        r"\U0001F000-\U0001F02F"  # Mahjong Tiles
        r"\U0001F030-\U0001F09F"  # Domino Tiles
        r"\U0001F0A0-\U0001F0FF"  # Playing Cards
        r"\U0001F100-\U0001F1FF"  # Enclosed Alphanumeric Supplement
        r"\U0001F200-\U0001F2FF"  # Enclosed Ideographic Supplement
        r"\U0001F300-\U0001F5FF"  # Miscellaneous Symbols and Pictographs
        r"\U0001F600-\U0001F64F"  # Emoticons
        r"\U0001F650-\U0001F67F"  # Ornamental Dingbats
        r"\U0001F680-\U0001F6FF"  # Transport and Map Symbols
        r"\U0001F700-\U0001F77F"  # Alchemical Symbols
        r"\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        r"\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        r"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        r"\U0001FA00-\U0001FA6F"  # Chess Symbols
        r"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        r"\u200D"  # Zero-Width Joiner (ZWJ) - for complex emoji sequences
        r"\uFE00-\uFE0F"  # Variation Selectors (VS15, VS16) - for emoji variations
        r"\u20E3"  # Combining Enclosing Keycap - for keycap emojis like 2️⃣
        r"]+$", re.UNICODE
    )

    @classmethod
    def add_option(cls, field_name, mutation_name=None):
        """Create a new class with the specified field name and mutation name"""
        # Create a unique class name that includes the mutation name if provided
        class_name = f"Custom{field_name.title().replace('_', '')}Validator"
        if mutation_name:
            class_name = f"{class_name}_{mutation_name}"
        return type(class_name, (cls,), {'field_name': field_name, 'mutation_name': mutation_name})

    field_name = "value"
    mutation_name = None

    def raise_error(self, message):
        """Helper function to raise GraphQLError with custom extensions"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if self.mutation_name:
            path.append(self.mutation_name)
        path.append(self.field_name)
        raise GraphQLError(message, extensions=extensions, path=path)

    def parse_value(self, value):
        """Handles values when passed as variables"""
        # Allow None for optional fields
        if value is None:
            return None
            
        if not isinstance(value, str):
            self.raise_error("Value must be a string.")

        if not (self.MIN_LENGTH <= len(value) <= self.MAX_LENGTH):
            self.raise_error(f"String length must be between {self.MIN_LENGTH} and {self.MAX_LENGTH} characters.")

        if not self.__class__.ALLOWED_PATTERN.match(value):
            self.raise_error("Value must contain only letters, numbers, spaces, special characters, and emojis.")

        return value

    @classmethod
    def parse_literal(cls, node, _variables=None):
        """Handles inline literals in GraphQL queries"""
        # Allow None for optional fields
        if node is None or (hasattr(node, 'value') and node.value is None):
            return None
            
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if hasattr(cls, 'mutation_name') and cls.mutation_name:
            path.append(cls.mutation_name)
        path.append(cls.field_name)

        if not isinstance(node, ast.StringValueNode):
            raise GraphQLError("Value must be a string.", extensions=extensions, path=path)

        value = node.value
        if not (2 <= len(value) <= 50):
            raise GraphQLError(
                f"String length must be between 2 and 50 characters.",
                extensions=extensions,
                path=path
            )

        # Check for HTML tags
        if re.search(r"<[^>]+>", value):
            raise GraphQLError(
                "HTML tags are not allowed.",
                extensions=extensions,
                path=path
            )

        # Use the same pattern as ALLOWED_PATTERN for consistency
        if not cls.ALLOWED_PATTERN.match(value):
            raise GraphQLError(
                "Value must contain only letters, numbers, spaces, special characters, and emojis.",
                extensions=extensions,
                path=path
            )

        return value


class NonSpecialCharacterString4_100(graphene.Scalar):
    """Custom String Scalar that enforces length constraints and disallows special characters"""

    MIN_LENGTH = 4
    MAX_LENGTH = 100
    # Only letters, numbers, spaces, and basic punctuation (no special symbols)
    ALLOWED_PATTERN = re.compile(
        r"^[a-zA-Z0-9\s\-.,!?()]+$",
        re.UNICODE
    )

    @classmethod
    def add_option(cls, field_name, mutation_name=None):
        """Create a new class with the specified field name and mutation name"""
        # Create a unique class name that includes the mutation name if provided
        class_name = f"Custom{field_name.title().replace('_', '')}Validator"
        if mutation_name:
            class_name = f"{class_name}_{mutation_name}"

        return type(class_name, (cls,), {'field_name': field_name, 'mutation_name': mutation_name})

    field_name = "value"
    mutation_name = None

    def raise_error(self, message):
        """Helper function to raise GraphQLError with custom extensions"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if self.mutation_name:
            path.append(self.mutation_name)
        path.append(self.field_name)
        raise GraphQLError(message, extensions=extensions, path=path)

    def parse_value(self, value):
        """Handles values when passed as variables"""
        if not isinstance(value, str):
            self.raise_error(f"{self.field_name} must be a string.")

        if not (self.MIN_LENGTH <= len(value) <= self.MAX_LENGTH):
            self.raise_error(f"String length must be between {self.MIN_LENGTH} and {self.MAX_LENGTH} characters.")

        if not self.__class__.ALLOWED_PATTERN.match(value):
            self.raise_error(f"{self.field_name} must contain only letters, numbers, spaces, and basic punctuation.")

        return value

    @classmethod
    def parse_literal(cls, node, _variables=None):
        """Handles inline literals in GraphQL queries"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if hasattr(cls, 'mutation_name') and cls.mutation_name:
            path.append(cls.mutation_name)
        path.append(cls.field_name)

        if not isinstance(node, ast.StringValueNode):
            raise GraphQLError("Value must be a string.", extensions=extensions, path=path)

        value = node.value
        if not (4 <= len(value) <= 100):
            raise GraphQLError(
                "String length must be between 4 and 100 characters.",
                extensions=extensions,
                path=path
            )

        if not cls.ALLOWED_PATTERN.match(value):
            raise GraphQLError(
                "Value must contain only letters, numbers, spaces, and basic punctuation.",
                extensions=extensions,
                path=path
            )

        return value


class CreateAchievementWhatValidator(SpecialCharacterString2_100):
    """Custom validator for the 'what' field in CreateAchievement with specific error messages"""
    
    field_name = "what"
    mutation_name = "CreateAchievement"
    
    def raise_error(self, message):
        """Helper function to raise GraphQLError with custom extensions"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if self.mutation_name:
            path.append(self.mutation_name)
        path.append(self.field_name)
        raise GraphQLError(message, extensions=extensions, path=path)

    def parse_value(self, value):
        """Handles values when passed as variables"""
        if not isinstance(value, str):
            self.raise_error("what must be a string.")
        
        if not (self.MIN_LENGTH <= len(value) <= self.MAX_LENGTH):
            self.raise_error("what must be between 2 and 100 characters.")
        
        if not self.__class__.ALLOWED_PATTERN.match(value):
            self.raise_error("what must contain only letters, numbers, spaces, special characters, and emojis.")
        
        return value

    @classmethod
    def parse_literal(cls, node, _variables=None):
        """Handles inline literals in GraphQL queries"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if hasattr(cls, 'mutation_name') and cls.mutation_name:
            path.append(cls.mutation_name)
        path.append("what")

        if not isinstance(node, ast.StringValueNode):
            raise GraphQLError("what must be a string.", extensions=extensions, path=path)

        value = node.value
        if not (2 <= len(value) <= 100):
            raise GraphQLError(
                "what must be between 2 and 100 characters.",
                extensions=extensions,
                path=path
            )

        if not cls.ALLOWED_PATTERN.match(value):
            raise GraphQLError(
                "what must contain only letters, numbers, spaces, special characters, and emojis.",
                extensions=extensions,
                path=path
            )

        return value


class CreateAchievementFromSourceValidator(SpecialCharacterString2_100):
    """Custom validator for the 'from_source' field in CreateAchievement with specific error messages"""
    
    field_name = "from"
    mutation_name = "CreateAchievement"
    
    def raise_error(self, message):
        """Helper function to raise GraphQLError with custom extensions"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if self.mutation_name:
            path.append(self.mutation_name)
        path.append(self.field_name)
        raise GraphQLError(message, extensions=extensions, path=path)
    
    def parse_value(self, value):
        """Handles values when passed as variables"""
        if not isinstance(value, str):
            self.raise_error("from must be a string.")
        
        if not (self.MIN_LENGTH <= len(value) <= self.MAX_LENGTH):
            self.raise_error("from must be between 2 and 100 characters.")
        
        if not self.__class__.ALLOWED_PATTERN.match(value):
            self.raise_error("from must contain only letters, numbers, spaces, special characters, and emojis.")
        
        return value

    @classmethod
    def parse_literal(cls, node, _variables=None):
        """Handles inline literals in GraphQL queries"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if hasattr(cls, 'mutation_name') and cls.mutation_name:
            path.append(cls.mutation_name)
        path.append("from")

        if not isinstance(node, ast.StringValueNode):
            raise GraphQLError("from must be a string.", extensions=extensions, path=path)

        value = node.value
        if not (2 <= len(value) <= 100):
            raise GraphQLError(
                "from must be between 2 and 100 characters.",
                extensions=extensions,
                path=path
            )

        if not cls.ALLOWED_PATTERN.match(value):
            raise GraphQLError(
                "from must contain only letters, numbers, spaces, special characters, and emojis.",
                extensions=extensions,
                path=path
            )

        return value


class CreateCommunityNameValidator(NonSpecialCharacterString4_100):
    """Custom validator for the 'name' field in CreateCommunity with specific error messages"""

    field_name = "name"
    mutation_name = "CreateCommunity"

    def raise_error(self, message):
        """Helper function to raise GraphQLError with custom extensions"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if self.mutation_name:
            path.append(self.mutation_name)
        path.append(self.field_name)
        raise GraphQLError(message, extensions=extensions, path=path)

    def parse_value(self, value):
        """Handles values when passed as variables"""
        if not isinstance(value, str):
            self.raise_error("name must be a string.")

        if not (self.MIN_LENGTH <= len(value) <= self.MAX_LENGTH):
            self.raise_error("name must be between 4 and 100 characters.")

        if not self.__class__.ALLOWED_PATTERN.match(value):
            self.raise_error("name must contain only letters, numbers, spaces, and basic punctuation.")

        return value

    @classmethod
    def parse_literal(cls, node, _variables=None):
        """Handles inline literals in GraphQL queries"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if hasattr(cls, 'mutation_name') and cls.mutation_name:
            path.append(cls.mutation_name)
        path.append("name")

        if not isinstance(node, ast.StringValueNode):
            raise GraphQLError("name must be a string.", extensions=extensions, path=path)

        value = node.value
        if not (4 <= len(value) <= 100):
            raise GraphQLError(
                "name must be between 4 and 100 characters.",
                extensions=extensions,
                path=path
            )

        if not cls.ALLOWED_PATTERN.match(value):
            raise GraphQLError(
                "name must contain only letters, numbers, spaces, and basic punctuation.",
                extensions=extensions,
                path=path
            )

        return value


class SpecialCharacterString1_50(graphene.Scalar):
    """Custom String Scalar for Story title and content - Min 1, Max 50 characters, allows all characters except HTML tags"""
    MIN_LENGTH = 1
    MAX_LENGTH = 50
    
    @classmethod
    def add_option(cls, field_name, mutation_name=None):
        """Create a new class with the specified field name and mutation name"""
        class_name = f"Custom{field_name.title().replace('_', '')}Validator"
        if mutation_name:
            class_name = f"{class_name}_{mutation_name}"
        return type(class_name, (cls,), {'field_name': field_name, 'mutation_name': mutation_name})
    
    field_name = "value"
    mutation_name = None
    
    def raise_error(self, message):
        """Helper function to raise GraphQLError with custom extensions"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if self.mutation_name:
            path.append(self.mutation_name)
        path.append(self.field_name)
        raise GraphQLError(message, extensions=extensions, path=path)
    
    def parse_value(self, value):
        """Handles values when passed as variables"""
        # Allow None for optional fields
        if value is None:
            return None
        
        if not isinstance(value, str):
            self.raise_error(f"{self.field_name} must be a string.")
        
        # Trim whitespace
        value_trimmed = value.strip()
        
        if not (self.MIN_LENGTH <= len(value_trimmed) <= self.MAX_LENGTH):
            self.raise_error(f"String length must be between {self.MIN_LENGTH} and {self.MAX_LENGTH} characters.")
        
        # Check for HTML tags
        if re.search(r"<[^>]+>", value_trimmed):
            self.raise_error("HTML tags are not allowed.")
        
        return value_trimmed
    
    @classmethod
    def parse_literal(cls, node, _variables=None):
        """Handles inline literals in GraphQL queries"""
        # Allow None for optional fields
        if node is None or (hasattr(node, 'value') and node.value is None):
            return None
        
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if hasattr(cls, 'mutation_name') and cls.mutation_name:
            path.append(cls.mutation_name)
        path.append(cls.field_name)
        
        if not isinstance(node, ast.StringValueNode):
            raise GraphQLError("Value must be a string.", extensions=extensions, path=path)
        
        value = node.value.strip()
        if not (1 <= len(value) <= 50):
            raise GraphQLError(
                "String length must be between 1 and 50 characters.",
                extensions=extensions,
                path=path
            )
        
        if re.search(r"<[^>]+>", value):
            raise GraphQLError(
                "HTML tags are not allowed.",
                extensions=extensions,
                path=path
            )
        
        return value


class SpecialCharacterString1_100(graphene.Scalar):
    """Custom String Scalar for Story captions - Min 1, Max 100 characters, allows all characters except HTML tags"""
    MIN_LENGTH = 1
    MAX_LENGTH = 100
    
    @classmethod
    def add_option(cls, field_name, mutation_name=None):
        """Create a new class with the specified field name and mutation name"""
        class_name = f"Custom{field_name.title().replace('_', '')}Validator"
        if mutation_name:
            class_name = f"{class_name}_{mutation_name}"
        return type(class_name, (cls,), {'field_name': field_name, 'mutation_name': mutation_name})
    
    field_name = "value"
    mutation_name = None
    
    def raise_error(self, message):
        """Helper function to raise GraphQLError with custom extensions"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if self.mutation_name:
            path.append(self.mutation_name)
        path.append(self.field_name)
        raise GraphQLError(message, extensions=extensions, path=path)
    
    def parse_value(self, value):
        """Handles values when passed as variables"""
        # Allow None for optional fields
        if value is None:
            return None
        
        if not isinstance(value, str):
            self.raise_error(f"{self.field_name} must be a string.")
        
        # Trim whitespace
        value_trimmed = value.strip()
        
        if not (self.MIN_LENGTH <= len(value_trimmed) <= self.MAX_LENGTH):
            self.raise_error(f"String length must be between {self.MIN_LENGTH} and {self.MAX_LENGTH} characters.")
        
        # Check for HTML tags
        if re.search(r"<[^>]+>", value_trimmed):
            self.raise_error("HTML tags are not allowed.")
        
        return value_trimmed
    
    @classmethod
    def parse_literal(cls, node, _variables=None):
        """Handles inline literals in GraphQL queries"""
        # Allow None for optional fields
        if node is None or (hasattr(node, 'value') and node.value is None):
            return None
        
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if hasattr(cls, 'mutation_name') and cls.mutation_name:
            path.append(cls.mutation_name)
        path.append(cls.field_name)
        
        if not isinstance(node, ast.StringValueNode):
            raise GraphQLError("Value must be a string.", extensions=extensions, path=path)
        
        value = node.value.strip()
        if not (1 <= len(value) <= 100):
            raise GraphQLError(
                "String length must be between 1 and 100 characters.",
                extensions=extensions,
                path=path
            )
        
        if re.search(r"<[^>]+>", value):
            raise GraphQLError(
                "HTML tags are not allowed.",
                extensions=extensions,
                path=path
            )
        
        return value


class SpecialCharacterString1_200(graphene.Scalar):
    """Custom String Scalar for Comments - Min 1, Max 200 characters, allows all characters except HTML tags"""
    MIN_LENGTH = 1
    MAX_LENGTH = 200
    
    @classmethod
    def add_option(cls, field_name, mutation_name=None):
        """Create a new class with the specified field name and mutation name"""
        class_name = f"Custom{field_name.title().replace('_', '')}Validator"
        if mutation_name:
            class_name = f"{class_name}_{mutation_name}"
        return type(class_name, (cls,), {'field_name': field_name, 'mutation_name': mutation_name})
    
    field_name = "value"
    mutation_name = None
    
    def raise_error(self, message):
        """Helper function to raise GraphQLError with custom extensions"""
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if self.mutation_name:
            path.append(self.mutation_name)
        path.append(self.field_name)
        raise GraphQLError(message, extensions=extensions, path=path)
    
    def parse_value(self, value):
        """Handles values when passed as variables"""
        # Allow None for optional fields
        if value is None:
            return None
        
        if not isinstance(value, str):
            self.raise_error(f"{self.field_name} must be a string.")
        
        # Trim whitespace
        value_trimmed = value.strip()
        
        # Reject whitespace-only comments
        if len(value_trimmed) == 0:
            self.raise_error(f"{self.field_name} cannot be empty or contain only whitespace.")
        
        if not (self.MIN_LENGTH <= len(value_trimmed) <= self.MAX_LENGTH):
            self.raise_error(f"{self.field_name} must be between {self.MIN_LENGTH} and {self.MAX_LENGTH} characters.")
        
        # Check for HTML tags
        if re.search(r"<[^>]+>", value_trimmed):
            self.raise_error("HTML tags are not allowed.")
        
        return value_trimmed
    
    @classmethod
    def parse_literal(cls, node, _variables=None):
        """Handles inline literals in GraphQL queries"""
        # Allow None for optional fields
        if node is None or (hasattr(node, 'value') and node.value is None):
            return None
        
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if hasattr(cls, 'mutation_name') and cls.mutation_name:
            path.append(cls.mutation_name)
        path.append(cls.field_name)
        
        if not isinstance(node, ast.StringValueNode):
            raise GraphQLError("Value must be a string.", extensions=extensions, path=path)
        
        value = node.value.strip()
        
        # Reject whitespace-only comments
        if len(value) == 0:
            raise GraphQLError(
                f"Value cannot be empty or contain only whitespace.",
                extensions=extensions,
                path=path
            )
        
        if not (1 <= len(value) <= 200):
            raise GraphQLError(
                "Value must be between 1 and 200 characters.",
                extensions=extensions,
                path=path
            )
        
        if re.search(r"<[^>]+>", value):
            raise GraphQLError(
                "HTML tags are not allowed.",
                extensions=extensions,
                path=path
            )
        
        return value


