from django.test import TestCase, override_settings
from django.urls import reverse
from unittest.mock import MagicMock, patch

import requests


class GoogleLocationSearchViewTests(TestCase):
    def _get_url(self):
        return reverse("service:location_search")

    @override_settings(GOOGLE_MAPS_API_KEY="test-key")
    def test_missing_query_returns_bad_request(self):
        response = self.client.get(self._get_url())
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["error"],
            "Missing required query parameter `query`.",
        )

    @override_settings(GOOGLE_MAPS_API_KEY=None)
    def test_missing_api_key_returns_server_error(self):
        response = self.client.get(self._get_url(), {"query": "Delhi"})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json()["error"],
            "Google Maps API key not configured.",
        )

    @override_settings(GOOGLE_MAPS_API_KEY="fake-key")
    @patch("service.views.requests.get")
    def test_successful_search_returns_google_payload(self, mock_get):
        fake_payload = {"results": [{"name": "New Delhi"}]}
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = fake_payload
        mock_get.return_value = mock_response

        response = self.client.get(
            self._get_url(),
            {"query": "New Delhi", "language": "en"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), fake_payload)

        mock_get.assert_called_once()
        _, kwargs = mock_get.call_args
        self.assertEqual(kwargs["params"]["key"], "fake-key")
        self.assertEqual(kwargs["params"]["query"], "New Delhi")
        self.assertEqual(kwargs["params"]["language"], "en")
        self.assertEqual(kwargs["timeout"], 5)

    @override_settings(GOOGLE_MAPS_API_KEY="fake-key")
    @patch("service.views.requests.get", side_effect=requests.RequestException("boom"))
    def test_google_maps_failure_returns_bad_gateway(self, mock_get):
        response = self.client.get(self._get_url(), {"query": "Delhi"})
        self.assertEqual(response.status_code, 502)
        body = response.json()
        self.assertEqual(body["error"], "Failed to reach Google Maps API.")
        self.assertIn("details", body)
        mock_get.assert_called_once()
