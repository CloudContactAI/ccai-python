"""
Tests for the webhook service

:license: MIT
:copyright: 2025 CloudContactAI LLC
"""

import hmac
import hashlib
import base64
import unittest
from unittest.mock import patch, MagicMock

from ccai_python import CCAI
from ccai_python.webhook import Webhook, WebhookConfig, WebhookEventType


class TestWebhook(unittest.TestCase):
    """Test cases for the Webhook service"""

    def setUp(self):
        """Set up test fixtures"""
        self.client_id = "test-client-id"
        self.api_key = "test-api-key"
        self.ccai = CCAI(client_id=self.client_id, api_key=self.api_key)

    @patch.object(CCAI, 'request')
    def test_register_webhook_auto_generated_secret(self, mock_request):
        """Test webhook registration with auto-generated secret"""
        mock_request.return_value = [{
            "id": "webhook_123",
            "url": "https://example.com/webhook",
            "events": ["message.sent"],
            "secretKey": "sk_live_auto_generated"
        }]

        config = WebhookConfig(
            url="https://example.com/webhook",
            events=[WebhookEventType.MESSAGE_SENT]
            # secret not provided - server should auto-generate
        )
        result = self.ccai.webhook.register(config)

        self.assertEqual(result.id, "webhook_123")
        self.assertEqual(result.url, "https://example.com/webhook")
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        self.assertEqual(call_args[0][0], 'POST')
        self.assertIn('/v1/client/', call_args[0][1])
        # Payload should be an array WITHOUT secretKey
        self.assertIsInstance(call_args[0][2], list)
        self.assertNotIn("secretKey", call_args[0][2][0])

    @patch.object(CCAI, 'request')
    def test_register_webhook_custom_secret(self, mock_request):
        """Test webhook registration with custom secret"""
        mock_request.return_value = [{
            "id": "webhook_124",
            "url": "https://example.com/webhook-custom",
            "events": ["message.sent"],
            "secretKey": "my-custom-secret"
        }]

        config = WebhookConfig(
            url="https://example.com/webhook-custom",
            events=[WebhookEventType.MESSAGE_SENT],
            secret="my-custom-secret"
        )
        result = self.ccai.webhook.register(config)

        self.assertEqual(result.id, "webhook_124")
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        # Payload should be an array WITH secretKey
        self.assertIsInstance(call_args[0][2], list)
        self.assertIn("secretKey", call_args[0][2][0])
        self.assertEqual(call_args[0][2][0]["secretKey"], "my-custom-secret")

    @patch.object(CCAI, 'request')
    def test_update_webhook(self, mock_request):
        """Test webhook update without secret"""
        mock_request.return_value = [{
            "id": "webhook_123",
            "url": "https://example.com/updated",
            "events": ["message.received"]
        }]

        result = self.ccai.webhook.update("webhook_123", {"url": "https://example.com/updated"})

        self.assertEqual(result.url, "https://example.com/updated")
        call_args = mock_request.call_args
        self.assertEqual(call_args[0][0], 'POST')
        # Payload should be an array with id (string IDs pass through as-is)
        self.assertIsInstance(call_args[0][2], list)
        self.assertEqual(call_args[0][2][0]["id"], "webhook_123")
        # Payload should NOT contain secretKey when not provided
        self.assertNotIn("secretKey", call_args[0][2][0])

    @patch.object(CCAI, 'request')
    def test_update_webhook_with_secret(self, mock_request):
        """Test webhook update with custom secret"""
        mock_request.return_value = [{
            "id": "webhook_123",
            "url": "https://example.com/updated",
            "events": ["message.received"],
            "secretKey": "new-secret"
        }]

        result = self.ccai.webhook.update("webhook_123", {
            "url": "https://example.com/updated",
            "secret": "new-secret"
        })

        self.assertEqual(result.url, "https://example.com/updated")
        call_args = mock_request.call_args
        # Payload should contain secretKey when provided
        self.assertIn("secretKey", call_args[0][2][0])
        self.assertEqual(call_args[0][2][0]["secretKey"], "new-secret")

    @patch.object(CCAI, 'request')
    def test_list_webhooks(self, mock_request):
        """Test listing webhooks"""
        mock_request.return_value = [{
            "id": "webhook_123",
            "url": "https://example.com/webhook",
            "events": ["message.sent"]
        }]

        result = self.ccai.webhook.list()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, "webhook_123")

    @patch.object(CCAI, 'request')
    def test_delete_webhook(self, mock_request):
        """Test deleting a webhook"""
        mock_request.return_value = {"success": True, "message": "Webhook deleted"}

        result = self.ccai.webhook.delete("webhook_123")

        self.assertTrue(result["success"])
        call_args = mock_request.call_args
        self.assertEqual(call_args[0][0], 'DELETE')
        self.assertIn('webhook_123', call_args[0][1])

    def test_verify_signature_valid(self):
        """Test valid signature verification"""
        client_id = "test-client-id"
        event_hash = "event-hash-abc123"
        secret = "test-secret"

        # Compute expected signature: HMAC-SHA256(secretKey, clientId:eventHash) in Base64
        data = f"{client_id}:{event_hash}"
        computed = hmac.new(
            secret.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha256
        ).digest()  # raw bytes
        expected = base64.b64encode(computed).decode('utf-8')

        result = self.ccai.webhook.verify_signature(expected, client_id, event_hash, secret)
        self.assertTrue(result)

    def test_verify_signature_invalid(self):
        """Test invalid signature rejection"""
        result = self.ccai.webhook.verify_signature("bad-signature", "client-id", "event-hash", "test-secret")
        self.assertFalse(result)

    def test_verify_signature_empty_params(self):
        """Test empty parameter rejection"""
        self.assertFalse(self.ccai.webhook.verify_signature("", "client-id", "event-hash", "test-secret"))
        self.assertFalse(self.ccai.webhook.verify_signature("sig", "", "event-hash", "test-secret"))
        self.assertFalse(self.ccai.webhook.verify_signature("sig", "client-id", "", "test-secret"))
        self.assertFalse(self.ccai.webhook.verify_signature("sig", "client-id", "event-hash", ""))


if __name__ == '__main__':
    unittest.main()
