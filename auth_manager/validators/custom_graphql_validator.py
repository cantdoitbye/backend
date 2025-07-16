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
        if not isinstance(value, str):
            self.raise_error(f"{self.field_name} must be a string.")
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
       
        return value

class NonSpecialCharacterString2_30(graphene.Scalar):
    """Custom String Scalar that enforces length constraints and disallows special characters"""

    MIN_LENGTH = 2
    MAX_LENGTH = 30
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
            raise GraphQLError(f"{cls.field_name} must be a string.", extensions=extensions, path=path)

        value = node.value
        if not (cls.MIN_LENGTH <= len(value) <= cls.MAX_LENGTH):
            raise GraphQLError(
                f"String length must be between {cls.MIN_LENGTH} and {cls.MAX_LENGTH} characters.",
                extensions=extensions,
                path=path,

            )
        if not re.match(r"^[a-zA-ZÀ-ÖØ-öø-ÿ]+$", value):
            raise GraphQLError(
                f"{cls.field_name} must contain only letters. No special characters allowed.",
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
    

class NonSpecialCharacterString20_500(graphene.Scalar):
    """Custom String Scalar that enforces length constraints and disallows special characters"""

    MIN_LENGTH = 20
    MAX_LENGTH = 500
    ALLOWED_PATTERN = re.compile(r"<[^>]+>")  # Allows only letters, numbers, and spaces
     
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
        if not (20 <= len(value) <= 500):
            raise GraphQLError(
                f"String length must be between 20 and 500 characters.",
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
    


class NonSpecialCharacterString5_100(graphene.Scalar):
    """Custom String Scalar that enforces length constraints and disallows special characters"""

    MIN_LENGTH = 5
    MAX_LENGTH = 100
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
    """Custom String Scalar that enforces length constraints and disallows special characters"""

    MIN_LENGTH = 10
    MAX_LENGTH = 200
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
        return value

class NonSpecialCharacterString2_100(graphene.Scalar):
    """Custom String Scalar that enforces length constraints and disallows special characters"""

    MIN_LENGTH = 2
    MAX_LENGTH = 100
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
        if not (2 <= len(value) <= 100):
            raise GraphQLError(
                f"String length must be between 2 and 100 characters.",
                extensions=extensions,
                path=path
            )
        if not re.match(r"^[a-zA-ZÀ-ÖØ-öø-ÿ0-9+ ]+$", value):
            raise GraphQLError(
                "Value must contain only letters. No special characters allowed.",
                extensions=extensions,
                path=path
            )
        return value

class NonSemiSpecialCharacterString2_100(graphene.Scalar):
    """Custom String Scalar that enforces length constraints and disallows special characters"""

    MIN_LENGTH = 2
    MAX_LENGTH = 100
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
        if not (2 <= len(value) <= 100):
            raise GraphQLError(
                f"String length must be between 2 and 100 characters.",
                extensions=extensions,
                path=path
            )
        if not re.match(r"^[a-zA-ZÀ-ÖØ-öø-ÿ0-9+ ]+$", value):
            raise GraphQLError(
                "Value must contain only letters. No special characters allowed. Except +",
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


class NonSpecialCharacterString2_500(graphene.Scalar):
    """Custom String Scalar that enforces length constraints and disallows special characters"""

    MIN_LENGTH = 2
    MAX_LENGTH = 500
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
        if not (2 <= len(value) <= 500):
            raise GraphQLError(
                f"String length must be between {cls.MIN_LENGTH} and {cls.MAX_LENGTH} characters.",
                extensions=extensions,
                path=path
            )
        if not re.match(r"^[a-zA-ZÀ-ÖØ-öø-ÿ ]+$", value):
            raise GraphQLError(
                "Value must contain only letters. No special characters allowed.",
                extensions=extensions,
                path=path
            )
        return value


class PhoneNumberScalar(graphene.Scalar):
    """Custom Scalar for validating phone numbers"""

    MIN_LENGTH = 11
    MAX_LENGTH = 17
    PHONE_PATTERN = re.compile(r"^\+\d{12,17}$")  # Starts with +, followed by 10-16 digits

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
        if not self.PHONE_PATTERN.match(value):
            self.raise_error("Invalid phone number format. Must start with '+' and contain 12-17 digits.")
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
        if not re.match(r"^\+\d{12,17}$", value):
            raise GraphQLError(
                "Invalid phone number format. Must start with '+' and contain 12-17 digits.",
                extensions=extensions,
                path=path
            )
        return value

class DateTimeScalar(graphene.Scalar):
    """Custom Scalar for validating DateTime in ISO 8601 format (YYYY-MM-DDThh:mm:ss)"""

    # Pattern for ISO 8601 format: YYYY-MM-DDThh:mm:ss
    ISO_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")

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

        if not isinstance(value, str):
            self.raise_error(f"{self.field_name} must be a string.")
        
        # Check if it matches the ISO 8601 format
        if not self.ISO_PATTERN.match(value):
            self.raise_error(f"Invalid datetime format. Must be in ISO 8601 format (YYYY-MM-DDThh:mm:ss).")
        
        try:
            # Convert string to datetime object
            return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
        except ValueError as e:
            self.raise_error(f"Invalid datetime: {str(e)}")

    @classmethod
    def parse_literal(cls, node, _variables=None):
        """Handles inline literals in GraphQL queries"""
        from datetime import datetime
        
        extensions = {"code": "BAD_REQUEST", "status_code": 400}
        path = []
        if hasattr(cls, 'mutation_name') and cls.mutation_name:
            path.append(cls.mutation_name)
        path.append(cls.field_name)
            
        if not isinstance(node, ast.StringValueNode):
            raise GraphQLError("DateTime must be a string.", extensions=extensions, path=path)

        value = node.value
        
        # Check if it matches the ISO 8601 format
        if not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", value):
            raise GraphQLError(
                "Invalid datetime format. Must be in ISO 8601 format (YYYY-MM-DDThh:mm:ss).",
                extensions=extensions,
                path=path
            )
        
        try:
            # Convert string to datetime object
            return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
        except ValueError as e:
            raise GraphQLError(
                f"Invalid datetime: {str(e)}",
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
    
    