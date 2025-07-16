import pytest
from graphql_jwt.testcases import JSONWebTokenTestCase
from auth_manager.models import Users

class CreateUserMutationTests(JSONWebTokenTestCase):

    def test_create_user_success(self):
        """Test the user creation mutation for a new user."""
        mutation = """
        mutation CreateUser($input: CreateUserInput!) {
            registerUser(input: $input) {
                token
                refreshToken
                success
                message
            }
        }
        """

        # Define the input data
        variables = {
            "input": {
                "email": "newuser613@example.com",
                "password": "Newpassword@231",
                "userType": "personal"
            }
        }

        # Send the request
        response = self.client.execute(mutation, variables=variables)

        # Check that the response is not None
        # self.assertIsNotNone(response.data)
        print(response)
        # Check for the expected fields in the response
        self.assertTrue(response.data.get('registerUser'))  # Ensure registerUser is present in response
        self.assertEqual(response.data['registerUser']['success'], True)
        self.assertEqual(response.data['registerUser']['message'], 'Your account has been successfully created.')

        # Check if the user exists in the database
        user = Users.nodes.get(email="newuser613@example.com")
        self.assertEqual(user.email, "newuser613@example.com")
