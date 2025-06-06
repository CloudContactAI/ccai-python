"""
Tests for the CCAI client

:license: MIT
:copyright: 2025 CloudContactAI LLC
"""

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
    
    def test_initialization_validation(self):
        """Test validation during initialization"""
        with self.assertRaises(ValueError):
            CCAI(client_id="", api_key=self.api_key)
        
        with self.assertRaises(ValueError):
            CCAI(client_id=self.client_id, api_key="")
    
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
