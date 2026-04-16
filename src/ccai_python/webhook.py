"""
webhook.py - Webhook service for the CCAI API
Handles webhook configuration and management for CloudContactAI events.

:license: MIT
:copyright: 2025 CloudContactAI LLC
"""

import hmac
import hashlib
import base64
from typing import Any, Callable, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum


class WebhookEventType(str, Enum):
    """Event types supported by CloudContactAI webhooks"""
    MESSAGE_SENT = "message.sent"
    MESSAGE_INCOMING = "message.incoming"
    MESSAGE_RECEIVED = "message.received"
    MESSAGE_EXCLUDED = "message.excluded"
    MESSAGE_ERROR_CARRIER = "message.error.carrier"
    MESSAGE_ERROR_CLOUDCONTACT = "message.error.cloudcontact"


class WebhookEvent(BaseModel):
    """Webhook event sent by CloudContactAI server"""
    model_config = {"extra": "allow"}

    event_type: str = Field(..., alias="eventType", description="Type of the event")
    data: Dict[str, Any] = Field(..., description="Event-specific data")
    event_hash: str = Field(..., alias="eventHash", description="Hash computed by the backend for signature verification")


class WebhookConfig(BaseModel):
    """Configuration for webhook integration"""
    url: str = Field(..., description="Webhook URL")
    events: List[WebhookEventType] = Field(..., description="List of events to subscribe to")
    secret: Optional[str] = Field(default=None, description="Optional secret for signature verification")
    secret_key: Optional[str] = Field(default=None, description="Alternative secret key name")
    method: Optional[str] = Field(default="POST", description="HTTP method")
    integration_type: Optional[str] = Field(default="ALL", description="Integration type")


class WebhookResponse(BaseModel):
    """Response from webhook API operations"""
    model_config = {"extra": "allow"}

    id: Optional[Union[str, int]] = Field(default=None, description="Webhook ID")
    url: Optional[str] = Field(default=None, description="Webhook URL")
    events: Optional[List[WebhookEventType]] = Field(default=None, description="Subscribed events")


class Webhook:
    """Webhook service for handling CloudContactAI webhook events"""

    def __init__(self, ccai):
        self.ccai = ccai

    def register(self, config: WebhookConfig) -> WebhookResponse:
        """Register a new webhook endpoint.
        If secret is not provided, the server will auto-generate one.
        The API expects an array of webhook objects and returns an array.
        """
        payload = [{
            "url": config.url,
            "method": config.method or "POST",
            "integrationType": config.integration_type or "ALL",
        }]

        # Only include secretKey if explicitly provided
        secret = config.secret_key or config.secret
        if secret:
            payload[0]["secretKey"] = secret

        endpoint = f"/v1/client/{self.ccai.client_id}/integration"
        response = self.ccai.request('POST', endpoint, payload)

        # API returns an array — return the first element
        if isinstance(response, list) and len(response) > 0:
            data: Dict[str, Any] = dict(response[0])
        else:
            data = dict(response)
        return WebhookResponse(**data)

    def update(self, webhook_id: str, config: Dict[str, Any]) -> WebhookResponse:
        """Update an existing webhook configuration.
        If secret is not provided, the server will keep the existing secret.
        Uses POST to the same endpoint as register, with id in the payload.
        """
        # Try to convert to int, fall back to string ID
        try:
            webhook_int_id = int(webhook_id)
        except ValueError:
            webhook_int_id = webhook_id

        payload = [{
            "id": webhook_int_id,
            "url": config.get("url", ""),
            "method": config.get("method", "POST"),
            "integrationType": config.get("integration_type", "ALL"),
        }]

        # Only include secretKey if explicitly provided
        secret = config.get("secret_key") or config.get("secret")
        if secret:
            payload[0]["secretKey"] = secret

        endpoint = f"/v1/client/{self.ccai.client_id}/integration"
        response = self.ccai.request('POST', endpoint, payload)

        # API returns an array — return the first element
        if isinstance(response, list) and len(response) > 0:
            data: Dict[str, Any] = dict(response[0])
        else:
            data = dict(response)
        return WebhookResponse(**data)

    def list(self) -> List[WebhookResponse]:
        """List all registered webhooks"""
        endpoint = f"/v1/client/{self.ccai.client_id}/integration"
        response = self.ccai.request('GET', endpoint)
        if isinstance(response, list):
            return [WebhookResponse(**dict(webhook)) for webhook in response]
        return [WebhookResponse(**dict(response))]

    def delete(self, webhook_id: str) -> Dict[str, Any]:
        """Delete a webhook"""
        endpoint = f"/v1/client/{self.ccai.client_id}/integration/{webhook_id}"
        return self.ccai.request('DELETE', endpoint)

    def verify_signature(self, signature: str, client_id: str, event_hash: str, secret: str) -> bool:
        """Verify a webhook signature using HMAC-SHA256.

        Signature is computed as: HMAC-SHA256(secretKey, clientId:eventHash) encoded in Base64

        :param signature: Signature from the X-CCAI-Signature header (Base64 encoded)
        :param client_id: Client ID
        :param event_hash: Event hash from the webhook payload
        :param secret: Webhook secret key
        :return: True if the signature is valid
        """
        if not signature or not client_id or not event_hash or not secret:
            return False

        # Compute: HMAC-SHA256(secretKey, "$clientId:$eventHash")
        data = f"{client_id}:{event_hash}"
        computed = hmac.new(
            secret.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha256
        ).digest()  # raw bytes

        computed_base64 = base64.b64encode(computed).decode('utf-8')

        # Constant-time comparison to prevent timing attacks
        return hmac.compare_digest(computed_base64, signature)

    @staticmethod
    def create_handler(handlers: Dict[str, Any]) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
        """Create a webhook handler function for web frameworks"""
        def handler(request_body: Dict[str, Any]) -> Dict[str, Any]:
            event = WebhookEvent(**request_body)

            if 'on_event' in handlers:
                handlers['on_event'](event)

            return {'received': True}

        return handler
