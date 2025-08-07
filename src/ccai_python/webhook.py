"""
webhook.py - Webhook service for the CCAI API
Handles webhook configuration and management for CloudContactAI events.

:license: MIT
:copyright: 2025 CloudContactAI LLC
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class WebhookEventType(str, Enum):
    """Event types supported by CloudContactAI webhooks"""
    MESSAGE_SENT = "message.sent"
    MESSAGE_RECEIVED = "message.received"


class WebhookCampaign(BaseModel):
    """Campaign information included in webhook events"""
    id: int = Field(..., description="Campaign ID")
    title: str = Field(..., description="Campaign title")
    message: str = Field(..., description="Campaign message")
    sender_phone: str = Field(..., description="Sender phone number")
    created_at: str = Field(..., description="Creation timestamp")
    run_at: str = Field(..., description="Run timestamp")


class WebhookEventBase(BaseModel):
    """Base interface for all webhook events"""
    campaign: WebhookCampaign = Field(..., description="Campaign information")
    from_: str = Field(..., alias="from", description="Sender")
    to: str = Field(..., description="Recipient")
    message: str = Field(..., description="Message content")


class MessageSentEvent(WebhookEventBase):
    """Message Sent (Outbound) webhook event"""
    type: WebhookEventType = Field(default=WebhookEventType.MESSAGE_SENT, description="Event type")


class MessageReceivedEvent(WebhookEventBase):
    """Message Received (Inbound) webhook event"""
    type: WebhookEventType = Field(default=WebhookEventType.MESSAGE_RECEIVED, description="Event type")


class WebhookConfig(BaseModel):
    """Configuration for webhook integration"""
    url: str = Field(..., description="Webhook URL")
    events: List[WebhookEventType] = Field(..., description="List of events to subscribe to")
    secret: Optional[str] = Field(default=None, description="Optional secret for signature verification")


class WebhookResponse(BaseModel):
    """Response from webhook API operations"""
    id: str = Field(..., description="Webhook ID")
    url: str = Field(..., description="Webhook URL")
    events: List[WebhookEventType] = Field(..., description="Subscribed events")


class Webhook:
    """Webhook service for handling CloudContactAI webhook events"""
    
    def __init__(self, ccai):
        self.ccai = ccai
    
    def register(self, config: WebhookConfig) -> WebhookResponse:
        """Register a new webhook endpoint"""
        response = self.ccai.request('POST', '/webhooks', config.dict())
        return WebhookResponse(**response)
    
    def update(self, webhook_id: str, config: Dict[str, Any]) -> WebhookResponse:
        """Update an existing webhook configuration"""
        response = self.ccai.request('PUT', f'/webhooks/{webhook_id}', config)
        return WebhookResponse(**response)
    
    def list(self) -> List[WebhookResponse]:
        """List all registered webhooks"""
        response = self.ccai.request('GET', '/webhooks')
        return [WebhookResponse(**webhook) for webhook in response]
    
    def delete(self, webhook_id: str) -> Dict[str, Any]:
        """Delete a webhook"""
        return self.ccai.request('DELETE', f'/webhooks/{webhook_id}')
    
    def verify_signature(self, signature: str, body: str, secret: str) -> bool:
        """Verify a webhook signature"""
        # Placeholder for signature verification logic
        # In production, this should implement proper HMAC verification
        return True
    
    @staticmethod
    def create_handler(handlers: Dict[str, Any]) -> callable:
        """Create a webhook handler function for web frameworks"""
        def handler(request_body: Dict[str, Any]) -> Dict[str, Any]:
            event_type = request_body.get('type')
            
            if event_type == WebhookEventType.MESSAGE_SENT:
                event = MessageSentEvent(**request_body)
                if 'on_message_sent' in handlers:
                    handlers['on_message_sent'](event)
            elif event_type == WebhookEventType.MESSAGE_RECEIVED:
                event = MessageReceivedEvent(**request_body)
                if 'on_message_received' in handlers:
                    handlers['on_message_received'](event)
            
            return {'received': True}
        
        return handler