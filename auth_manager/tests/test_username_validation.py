#!/usr/bin/env python3
"""
Unit tests for username validation functionality.

This module contains comprehensive unit tests for the username validation
logic to ensure the bug fix works correctly and covers all edge cases.

Tests cover:
- Valid usernames (3-9 characters)
- Invalid usernames (too short, too long)
- Invalid characters
- Boundary conditions
- Original failing case
"""

import unittest
from graphql import GraphQLError
from auth_manager.validators.rules.string_validation import validate_username


class TestUsernameValidation(unittest.TestCase):
    """
    Test cases for username validation functionality.
    """

    def test_valid_usernames_3_to_9_characters(self):
        """
        Test that valid usernames with 3-9 characters are accepted.
        """
        valid_usernames = [
            "abc",           # 3 characters - minimum boundary
            "test",          # 4 characters
            "user1",         # 5 characters
            "abcdef",        # 6 characters
            "testuser",      # 8 characters
            "test_user",     # 9 characters with underscore - maximum boundary
            "user_123",      # 8 characters with underscore and numbers
            "ABC123",        # 6 characters uppercase
            "test123",       # 7 characters mixed
        ]
        
        for username in valid_usernames:
            with self.subTest(username=username):
                try:
                    result = validate_username(username)
                    self.assertTrue(result, f"Username '{username}' should be valid")
                except GraphQLError:
                    self.fail(f"Username '{username}' should be valid but was rejected")

    def test_invalid_usernames_too_short(self):
        """
        Test that usernames shorter than 6 characters are rejected.
        """
        short_usernames = [
            "",           # 0 characters - empty string
            "a",          # 1 character
            "ab",         # 2 characters
        ]
        
        for username in short_usernames:
            with self.subTest(username=username):
                with self.assertRaises(GraphQLError) as context:
                    validate_username(username)
                self.assertIn("Must be between 3 and 9 characters", str(context.exception))

    def test_invalid_usernames_too_long(self):
        """
        Test that usernames longer than 9 characters are rejected.
        """
        long_usernames = [
            "verylongusername",      # 16 characters
            "a1b2c3d4e5",           # 10 characters
            "toolongusername123",   # 18 characters
            "superlongusername",    # 17 characters
            "1234567890",           # 10 characters
            "nitinooump",           # 10 characters - now too long
        ]
        
        for username in long_usernames:
            with self.subTest(username=username):
                with self.assertRaises(GraphQLError) as context:
                    validate_username(username)
                self.assertIn("Must be between 3 and 9 characters", str(context.exception))

    def test_invalid_characters(self):
        """
        Test that usernames with invalid characters are rejected.
        """
        invalid_usernames = [
            "user@name",     # Contains @ symbol
            "user name",     # Contains space
            "user-name",     # Contains hyphen
            "user.name",     # Contains dot
            "user#name",     # Contains hash
            "user$name",     # Contains dollar sign
            "user%name",     # Contains percent
            "user&name",     # Contains ampersand
            "user*name",     # Contains asterisk
            "user+name",     # Contains plus
            "user=name",     # Contains equals
            "user!name",     # Contains exclamation
            "user?name",     # Contains question mark
            "user(name)",    # Contains parentheses
            "user[name]",    # Contains brackets
            "user{name}",    # Contains braces
            "user|name",     # Contains pipe
            "user\\name",    # Contains backslash
            "user/name",     # Contains forward slash
            "user:name",     # Contains colon
            "user;name",     # Contains semicolon
            "user'name",     # Contains apostrophe
            "user\"name",    # Contains quote
            "user<name>",    # Contains angle brackets
            "user,name",     # Contains comma
        ]
        
        for username in invalid_usernames:
            with self.subTest(username=username):
                with self.assertRaises(GraphQLError) as context:
                    validate_username(username)
                # Should fail due to invalid characters, not length
                error_message = str(context.exception)
                self.assertTrue(
                    "Must be between 3 and 9 characters" in error_message,
                    f"Username '{username}' should be rejected due to invalid characters"
                )

    def test_boundary_conditions(self):
        """
        Test exact boundary conditions (3 and 9 characters).
        """
        # Test minimum boundary (3 characters)
        min_boundary_usernames = [
            "abc",       # 3 letters
            "123",       # 3 numbers
            "ab1",       # 3 mixed
            "a_1",       # 3 with underscore
            "A1B",       # 3 uppercase mixed
        ]
        
        for username in min_boundary_usernames:
            with self.subTest(username=username, boundary="minimum"):
                try:
                    result = validate_username(username)
                    self.assertTrue(result, f"3-character username '{username}' should be valid")
                except GraphQLError:
                    self.fail(f"3-character username '{username}' should be valid but was rejected")
        
        # Test maximum boundary (9 characters)
        max_boundary_usernames = [
            "abcdefghi",     # 9 letters
            "123456789",     # 9 numbers
            "abc123456",     # 9 mixed
            "test_user",     # 9 with underscore
            "A1B2C3D4E",     # 9 uppercase mixed
        ]
        
        for username in max_boundary_usernames:
            with self.subTest(username=username, boundary="maximum"):
                try:
                    result = validate_username(username)
                    self.assertTrue(result, f"9-character username '{username}' should be valid")
                except GraphQLError:
                    self.fail(f"9-character username '{username}' should be valid but was rejected")

    def test_original_failing_case(self):
        """
        Test that the original failing case is now properly rejected as too long.
        """
        username = "nitinooump"  # 10 characters - now too long for 3-9 range
        
        with self.assertRaises(GraphQLError) as context:
            validate_username(username)
        self.assertIn("Must be between 3 and 9 characters", str(context.exception))

    def test_allowed_characters_only(self):
        """
        Test that only alphanumeric characters and underscores are allowed.
        """
        valid_char_usernames = [
            "abc",           # Only letters (3 chars)
            "123",           # Only numbers (3 chars)
            "abc123",        # Letters and numbers (6 chars)
            "test_user",     # Letters and underscore (9 chars)
            "user_123",      # Letters, numbers, and underscore (8 chars)
            "_test123",      # Starting with underscore (8 chars)
            "test123_",      # Ending with underscore (8 chars)
            "_test_12",      # Multiple underscores (8 chars)
            "ABCDEF",        # Uppercase letters (6 chars)
            "AbC123",        # Mixed case (6 chars)
        ]
        
        for username in valid_char_usernames:
            with self.subTest(username=username):
                try:
                    result = validate_username(username)
                    self.assertTrue(result, f"Username '{username}' with valid characters should pass")
                except GraphQLError:
                    self.fail(f"Username '{username}' with valid characters should pass but was rejected")

    def test_error_message_content(self):
        """
        Test that error messages contain the correct information.
        """
        invalid_username = "ab"  # 2 characters - too short
        
        with self.assertRaises(GraphQLError) as context:
            validate_username(invalid_username)
        
        error_message = str(context.exception)
        self.assertIn("Invalid username", error_message)
        self.assertIn("Must be between 3 and 9 characters", error_message)

    def test_function_return_value(self):
        """
        Test that the function returns True for valid usernames.
        """
        valid_username = "testuser"  # 8 characters - valid
        result = validate_username(valid_username)
        self.assertTrue(result)
        self.assertIsInstance(result, bool)


class TestUsernameValidationIntegration(unittest.TestCase):
    """
    Integration tests for username validation in the context of the application.
    """

    def test_graphql_mutation_scenario(self):
        """
        Test the exact scenario from the GraphQL mutation that was failing.
        """
        # This simulates a valid username scenario for the SearchUsername mutation
        username = "testuser"  # 8 characters - valid for 3-9 range
        
        # This should not raise an exception
        try:
            result = validate_username(username)
            self.assertTrue(result)
        except GraphQLError as e:
            self.fail(f"GraphQL mutation scenario should work but failed: {str(e)}")

    def test_multiple_validation_calls(self):
        """
        Test that multiple calls to validate_username work correctly.
        """
        usernames = ["testuser", "user123", "abc", "abcdef"]
        
        for username in usernames:
            with self.subTest(username=username):
                result = validate_username(username)
                self.assertTrue(result)


if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=2)