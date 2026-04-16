"""
Tests for the email service

:license: MIT
:copyright: 2025 CloudContactAI LLC
"""

import unittest
from unittest.mock import patch, MagicMock

from ccai_python import CCAI
from ccai_python.email_service import Email, EmailCampaign, EmailAccount


class TestEmail(unittest.TestCase):
    """Test cases for the Email service"""

    def setUp(self):
        """Set up test fixtures"""
        self.client_id = "test-client-id"
        self.api_key = "test-api-key"
        self.ccai = CCAI(client_id=self.client_id, api_key=self.api_key)

    @patch('requests.request')
    def test_send_single_uses_client_email_url(self, mock_request):
        """Test that email uses the client's email_base_url, not hardcoded"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": 123, "status": "PENDING"}
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response

        self.ccai.email.send_single(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            subject="Test Subject",
            message="<p>Test</p>",
            sender_email="sender@example.com",
            reply_email="reply@example.com",
            sender_name="Test Sender",
            title="Test Campaign"
        )

        # Verify the URL uses client's email_base_url, not hardcoded test URL
        call_url = mock_request.call_args.kwargs.get('url') or mock_request.call_args[1].get('url')
        self.assertIn("email-campaigns.cloudcontactai.com/api/v1", call_url)
        # Verify headers use client_id, not hardcoded 1223
        call_headers = mock_request.call_args.kwargs.get('headers') or mock_request.call_args[1].get('headers')
        self.assertEqual(call_headers.get('AccountId'), 'test-client-id')
        self.assertEqual(call_headers.get('ClientId'), 'test-client-id')
        self.assertNotEqual(call_headers.get('AccountId'), '1223')

    @patch('requests.request')
    def test_send_single_test_environment(self, mock_request):
        """Test email URL in test environment"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": 456, "status": "PENDING"}
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response

        ccai = CCAI(client_id=self.client_id, api_key=self.api_key, use_test=True)
        ccai.email.send_single(
            first_name="John", last_name="Doe", email="john@example.com",
            subject="Test", message="<p>Test</p>",
            sender_email="s@e.com", reply_email="r@e.com",
            sender_name="Sender", title="Title"
        )

        call_url = mock_request.call_args.kwargs.get('url') or mock_request.call_args[1].get('url')
        self.assertIn("email-campaigns-test-cloudcontactai.allcode.com/api/v1", call_url)

    def test_send_validation_empty_accounts(self):
        """Test validation for empty accounts"""
        campaign = EmailCampaign(
            subject="Test", title="Test", message="<p>Test</p>",
            sender_email="s@e.com", reply_email="r@e.com", sender_name="Sender",
            accounts=[]
        )
        with self.assertRaises(ValueError) as ctx:
            self.ccai.email.send_campaign(campaign)
        self.assertIn("At least one account is required", str(ctx.exception))

    def test_send_validation_missing_fields(self):
        """Test validation for missing required fields"""
        with self.assertRaises(ValueError):
            self.ccai.email.send_single(
                first_name="John", last_name="Doe", email="john@example.com",
                subject="", message="<p>Test</p>",
                sender_email="s@e.com", reply_email="r@e.com",
                sender_name="Sender", title="Title"
            )


    @patch('requests.request')
    def test_email_account_custom_fields_and_id(self, mock_request):
        """Test that customAccountId and data are sent in the request"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": 123,
            "status": "PENDING",
            "message": "Email campaign sent successfully",
            "responseId": "resp-email-xyz",
        }
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response

        campaign = EmailCampaign(
            subject="Test", title="Test", message="<p>Test</p>",
            sender_email="s@e.com", reply_email="r@e.com", sender_name="Sender",
            accounts=[EmailAccount(
                first_name="John", last_name="Doe", email="john@example.com",
                custom_account_id="ext-id-123",
                data={"tier": "gold", "locale": "en-US"},
            )]
        )
        result = self.ccai.email.send_campaign(campaign)

        # Verify request body contains the custom fields
        call_json = mock_request.call_args.kwargs.get("json") or mock_request.call_args[1].get("json")
        account_in_payload = call_json["accounts"][0]
        self.assertEqual(account_in_payload.get("customAccountId"), "ext-id-123")
        self.assertEqual(account_in_payload.get("data"), {"tier": "gold", "locale": "en-US"})
        # Verify wire format uses camelCase for campaign fields
        self.assertIn("senderEmail", call_json)
        self.assertIn("replyEmail", call_json)
        self.assertNotIn("sender_email", call_json)
        self.assertNotIn("reply_email", call_json)

        # Verify response fields
        self.assertEqual(result.message, "Email campaign sent successfully")
        self.assertEqual(result.response_id, "resp-email-xyz")


if __name__ == '__main__':
    unittest.main()
