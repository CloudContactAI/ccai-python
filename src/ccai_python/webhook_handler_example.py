import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ccai_python import Webhook, WebhookEventType, WebhookEvent

# Example webhook event handler
def handle_webhook_event(event: WebhookEvent):
    """Handle CloudContactAI webhook events"""
    print(f"📨 Webhook Event Received: {event.event_type}")
    print(f"   Event Hash: {event.event_hash}")

    # Handle different event types
    if event.event_type == WebhookEventType.MESSAGE_SENT:
        print(f"✅ Message sent successfully")
        if 'To' in event.data:
            print(f"   Recipient: {event.data['To']}")
        if 'TotalPrice' in event.data:
            print(f"   Cost: ${event.data['TotalPrice']}")
        if 'Segments' in event.data:
            print(f"   Segments: {event.data['Segments']}")

    elif event.event_type == WebhookEventType.MESSAGE_INCOMING:
        print(f"📥 Message received (reply)")
        if 'From' in event.data:
            print(f"   From: {event.data['From']}")
        if 'Message' in event.data:
            print(f"   Message: {event.data['Message']}")

    elif event.event_type == WebhookEventType.MESSAGE_EXCLUDED:
        print(f"⚠️ Message excluded")
        if 'ExcludedReason' in event.data:
            print(f"   Reason: {event.data['ExcludedReason']}")

    elif event.event_type == WebhookEventType.MESSAGE_ERROR_CARRIER:
        print(f"❌ Carrier error")
        if 'ErrorCode' in event.data:
            print(f"   Code: {event.data['ErrorCode']}")
        if 'ErrorMessage' in event.data:
            print(f"   Message: {event.data['ErrorMessage']}")

    elif event.event_type == WebhookEventType.MESSAGE_ERROR_CLOUDCONTACT:
        print(f"🚨 System error")
        if 'ErrorCode' in event.data:
            print(f"   Code: {event.data['ErrorCode']}")
        if 'ErrorMessage' in event.data:
            print(f"   Message: {event.data['ErrorMessage']}")

    # Handle custom data if present
    if 'CustomData' in event.data and event.data['CustomData']:
        print(f"   📌 Custom Data: {event.data['CustomData']}")


# Create webhook handler
webhook_handler = Webhook.create_handler({
    'on_event': handle_webhook_event
})

# Example webhook payloads (these would come from CloudContactAI)
test_payloads = [
    {
        'eventType': 'message.sent',
        'eventHash': 'hash-abc123',
        'data': {
            'To': '+15551234567',
            'TotalPrice': 0.07,
            'Segments': 1,
            'CustomData': 'order-12345'
        }
    },
    {
        'eventType': 'message.incoming',
        'eventHash': 'hash-def456',
        'data': {
            'From': '+15551234567',
            'Message': 'Thanks for the message!'
        }
    },
    {
        'eventType': 'message.excluded',
        'eventHash': 'hash-ghi789',
        'data': {
            'ExcludedReason': 'Invalid phone number'
        }
    }
]

print("🔧 Testing webhook handler with sample payloads:\n")
for payload in test_payloads:
    result = webhook_handler(payload)
    print(f"✓ Result: {result}\n")