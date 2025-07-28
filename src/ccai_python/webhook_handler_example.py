import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ccai_python import Webhook, WebhookEventType, MessageSentEvent, MessageReceivedEvent

# Example webhook handler
def handle_message_sent(event: MessageSentEvent):
    print(f"✅ Message sent event received:")
    print(f"   Campaign: {event.campaign.title} (ID: {event.campaign.id})")
    print(f"   From: {event.from_}")
    print(f"   To: {event.to}")
    print(f"   Message: {event.message}")

def handle_message_received(event: MessageReceivedEvent):
    print(f"📨 Message received event received:")
    print(f"   Campaign: {event.campaign.title} (ID: {event.campaign.id})")
    print(f"   From: {event.from_}")
    print(f"   To: {event.to}")
    print(f"   Message: {event.message}")

# Create webhook handler
webhook_handler = Webhook.create_handler({
    'on_message_sent': handle_message_sent,
    'on_message_received': handle_message_received
})

# Example webhook payload (this would come from CloudContactAI)
test_payload = {
    'type': 'message.sent',
    'campaign': {
        'id': 123,
        'title': 'Test Campaign',
        'message': '',
        'sender_phone': '+11234567894',
        'created_at': '2025-01-14 22:18:28.273',
        'run_at': ''
    },
    'from': '+11234567894',
    'to': '+15551234567',
    'message': 'Hello Test User, this is a test message!'
}

print("🔧 Testing webhook handler with sample payload:")
result = webhook_handler(test_payload)
print(f"📤 Handler result: {result}")