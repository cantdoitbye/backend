from django.test import TestCase
from django.utils.decorators import async_to_sync
from unittest.mock import patch, AsyncMock
from nio import LoginResponse, RegisterResponse
from chat.utils import register_user_on_matrix
from django.conf import settings


class MatrixIntegrationTests(TestCase):
    @async_to_sync
    @patch("chat.utils.AsyncClient")
    async def test_successful_user_registration(self, mock_client):
        # Mock Matrix client and responses
        mock_admin_client = AsyncMock()
        mock_client.return_value = mock_admin_client

        # Mock admin login response
        mock_admin_client.login.return_value = LoginResponse(
            user_id="@admin:example.com",
            device_id="DEVICEID",
            access_token="ADMIN_TOKEN",
        )

        # Test user data
        username = "testuser"
        password = "testpass"
        expected_user_id = f"@{username}:example.com"

        # Execute registration
        result = await register_user_on_matrix(username, password)

        # Assertions
        self.assertEqual(result, expected_user_id)
        mock_admin_client.login.assert_awaited_once_with(
            settings.MATRIX_ADMIN_USER, settings.MATRIX_ADMIN_PASSWORD
        )
        mock_admin_client.register_with_password.assert_awaited_once_with(
            user_id=expected_user_id, password=password
        )
        mock_admin_client.logout.assert_awaited_once()

    @async_to_sync
    @patch("chat.utils.AsyncClient")
    async def test_failed_admin_login(self, mock_client):
        mock_admin_client = AsyncMock()
        mock_client.return_value = mock_admin_client

        # Simulate failed admin login
        mock_admin_client.login.return_value = None

        result = await register_user_on_matrix("testuser", "testpass")

        self.assertIsNone(result)
        mock_admin_client.register_with_password.assert_not_awaited()

    @async_to_sync
    @patch("chat.utils.AsyncClient")
    async def test_user_registration_failure(self, mock_client):
        mock_admin_client = AsyncMock()
        mock_client.return_value = mock_admin_client

        mock_admin_client.login.return_value = LoginResponse(
            user_id="@admin:example.com",
            device_id="DEVICEID",
            access_token="ADMIN_TOKEN",
        )

        # Simulate registration failure
        mock_admin_client.register_with_password.side_effect = Exception(
            "Registration failed"
        )

        result = await register_user_on_matrix("testuser", "testpass")

        self.assertIsNone(result)
        mock_admin_client.logout.assert_awaited_once()

    @async_to_sync
    @patch("chat.utils.AsyncClient")
    async def test_matrix_server_unreachable(self, mock_client):
        mock_admin_client = AsyncMock()
        mock_client.return_value = mock_admin_client

        # Simulate connection error
        mock_admin_client.login.side_effect = ConnectionError("Server unreachable")

        result = await register_user_on_matrix("testuser", "testpass")

        self.assertIsNone(result)
        mock_admin_client.register_with_password.assert_not_awaited()
