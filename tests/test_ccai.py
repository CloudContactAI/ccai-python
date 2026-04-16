"""
Tests for the CCAI client

:license: MIT
:copyright: 2025 CloudContactAI LLC
"""

import os
import unittest
from unittest.mock import patch, MagicMock

from ccai_python import CCAI, Account


class TestCCAI(unittest.TestCase):
    """Test cases for the CCAI client"""

    def setUp(self):
        """Set up test fixtures"""
        self.client_id = "test-client-id"
        self.api_key = "test-api-key"
        self.ccai = CCAI(client_id=self.client_id, api_key=self.api_key)

    def test_initialization(self):
        """Test client initialization"""
        self.assertEqual(self.ccai.client_id, self.client_id)
        self.assertEqual(self.ccai.api_key, self.api_key)
        self.assertEqual(self.ccai.base_url, "https://core.cloudcontactai.com/api")

        # Test custom base URL
        custom_url = "https://custom.api.example.com"
        ccai = CCAI(client_id=self.client_id, api_key=self.api_key, base_url=custom_url)
        self.assertEqual(ccai.base_url, custom_url)

    def test_initialization_with_test_environment(self):
        """Test client initialization with test environment"""
        ccai = CCAI(client_id=self.client_id, api_key=self.api_key, use_test=True)
        self.assertEqual(ccai.base_url, "https://core-test-cloudcontactai.allcode.com/api")
        self.assertEqual(ccai.email_base_url, "https://email-campaigns-test-cloudcontactai.allcode.com/api/v1")
        self.assertEqual(ccai.file_base_url, "https://files-test-cloudcontactai.allcode.com")
        self.assertTrue(ccai.use_test)

    def test_initialization_production_default(self):
        """Test production URLs are default"""
        ccai = CCAI(client_id=self.client_id, api_key=self.api_key)
        self.assertEqual(ccai.base_url, "https://core.cloudcontactai.com/api")
        self.assertEqual(ccai.email_base_url, "https://email-campaigns.cloudcontactai.com/api/v1")
        self.assertEqual(ccai.file_base_url, "https://files.cloudcontactai.com")
        self.assertFalse(ccai.use_test)

    def test_initialization_validation(self):
        """Test validation during initialization"""
        with self.assertRaises(ValueError):
            CCAI(client_id="", api_key=self.api_key)

        with self.assertRaises(ValueError):
            CCAI(client_id=self.client_id, api_key="")

    @patch.dict(os.environ, {"CCAI_BASE_URL": "https://env-base.example.com"})
    def test_env_var_override(self):
        """Test environment variable URL override"""
        ccai = CCAI(client_id=self.client_id, api_key=self.api_key)
        self.assertEqual(ccai.base_url, "https://env-base.example.com")

    @patch('requests.request')
    def test_request(self, mock_request):
        """Test the request method"""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "success"}
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response

        # Test GET request
        result = self.ccai.request("get", "/test-endpoint")
        self.assertEqual(result, {"status": "success"})

        # Verify request was made correctly
        mock_request.assert_called_with(
            method="GET",
            url="https://core.cloudcontactai.com/api/test-endpoint",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "*/*"
            },
            json=None,
            timeout=30
        )

        # Test POST request with data
        data = {"key": "value"}
        result = self.ccai.request("post", "/test-endpoint", data=data)
        self.assertEqual(result, {"status": "success"})

        # Verify request was made correctly
        mock_request.assert_called_with(
            method="POST",
            url="https://core.cloudcontactai.com/api/test-endpoint",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "*/*"
            },
            json=data,
            timeout=30
        )


if __name__ == '__main__':
    unittest.main()
