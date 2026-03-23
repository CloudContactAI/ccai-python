"""
Tests for the Contact service

:license: MIT
:copyright: 2026 CloudContactAI LLC
"""

import unittest
from unittest.mock import patch

from ccai_python import CCAI
from ccai_python.contact_service import ContactDoNotTextResponse


class TestContact(unittest.TestCase):
    """Test cases for the Contact service"""

    def setUp(self):
        """Set up test fixtures"""
        self.client_id = "<client_id>"
        self.api_key = "<api_key>"
        self.ccai = CCAI(client_id=self.client_id, api_key=self.api_key)

    @patch.object(CCAI, 'request')
    def test_set_do_not_text_by_contact_id(self, mock_request):
        """Test setting do-not-text using contact ID"""
        mock_request.return_value = {
            "contactId": "contact-123",
            "phone": "+15551234567",
            "doNotText": True
        }

        response = self.ccai.contact.set_do_not_text(
            do_not_text=True,
            contact_id="contact-123"
        )

        self.assertIsInstance(response, ContactDoNotTextResponse)
        self.assertEqual(response.contact_id, "contact-123")
        self.assertEqual(response.phone, "+15551234567")
        self.assertTrue(response.do_not_text)

        mock_request.assert_called_once_with(
            'PUT',
            '/account/do-not-text',
            {
                "clientId": self.client_id,
                "contactId": "contact-123",
                "phone": None,
                "doNotText": True
            }
        )

    @patch.object(CCAI, 'request')
    def test_set_do_not_text_by_phone(self, mock_request):
        """Test setting do-not-text using phone number"""
        mock_request.return_value = {
            "contactId": "contact-456",
            "phone": "+15559876543",
            "doNotText": True
        }

        response = self.ccai.contact.set_do_not_text(
            do_not_text=True,
            phone="+15559876543"
        )

        self.assertIsInstance(response, ContactDoNotTextResponse)
        self.assertEqual(response.contact_id, "contact-456")
        self.assertEqual(response.phone, "+15559876543")
        self.assertTrue(response.do_not_text)

        mock_request.assert_called_once_with(
            'PUT',
            '/account/do-not-text',
            {
                "clientId": self.client_id,
                "contactId": None,
                "phone": "+15559876543",
                "doNotText": True
            }
        )

    @patch.object(CCAI, 'request')
    def test_remove_do_not_text(self, mock_request):
        """Test removing do-not-text status"""
        mock_request.return_value = {
            "contactId": "contact-123",
            "phone": "+15551234567",
            "doNotText": False
        }

        response = self.ccai.contact.set_do_not_text(
            do_not_text=False,
            contact_id="contact-123"
        )

        self.assertFalse(response.do_not_text)

    @patch.object(CCAI, 'request')
    def test_set_do_not_text_api_error(self, mock_request):
        """Test handling API errors"""
        mock_request.side_effect = Exception("API Error")

        with self.assertRaises(Exception) as context:
            self.ccai.contact.set_do_not_text(
                do_not_text=True,
                contact_id="contact-123"
            )

        self.assertIn("API Error", str(context.exception))


if __name__ == '__main__':
    unittest.main()
