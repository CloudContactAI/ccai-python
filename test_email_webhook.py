#!/usr/bin/env python3
"""
Test script for email and webhook functionality in CCAI Python library
"""

import os
from datetime import datetime, timedelta
from src.ccai_python import CCAI
from src.ccai_python.email_service import EmailCampaign, EmailAccount, EmailOptions
from src.ccai_python.webhook import WebhookConfig, WebhookEventType

def test_email_functionality():
    """Test email functionality"""
    print("Testing Email Functionality...")
    
    # Initialize CCAI client
    ccai = CCAI(
        client_id=os.getenv('CCAI_CLIENT_ID'),
        api_key=os.getenv('CCAI_API_KEY'),
        use_test=True
    )
    
    try:
        # Test single email
        print("\\n1. Testing single email...")
        response = ccai.email.send_single(
            first_name="Andreas",
            last_name="Garcia",
            email="andreas@allcode.com",
            subject="Test Email from Python",
            message="<p>Hello Andreas,</p><p>This is a test email from the Python CCAI library!</p>",
            sender_email="test@allcode.com",
            reply_email="support@allcode.com",
            sender_name="CCAI Python Test",
            title="Python Test Email"
        )
        print(f"Single email sent successfully: {response}")
        
        # Test email campaign
        print("\\n2. Testing email campaign...")
        accounts = [
            EmailAccount(
                first_name="Andreas",
                last_name="Garcia",
                email="andreas@allcode.com",
                phone=""
            ),
            EmailAccount(
                first_name="Test",
                last_name="User",
                email="joel@allcode.com",
                phone=""
            )
        ]
        
        campaign = EmailCampaign(
            subject="Python Campaign Test",
            title="Python Email Campaign",
            message="<p>Hello ${firstName} ${lastName},</p><p>This is a test campaign from Python!</p>",
            sender_email="campaign@allcode.com",
            reply_email="support@allcode.com",
            sender_name="CCAI Python Campaign",
            accounts=accounts
        )
        
        def progress_callback(status):
            print(f"  Progress: {status}")
        
        options = EmailOptions(on_progress=progress_callback)
        response = ccai.email.send_campaign(campaign, options)
        print(f"Email campaign sent successfully: {response}")
        
        # Test scheduled email
        print("\\n3. Testing scheduled email...")
        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        
        scheduled_campaign = EmailCampaign(
            subject="Scheduled Email Test",
            title="Scheduled Python Email",
            message="<p>Hello ${firstName},</p><p>This is a scheduled email from Python!</p>",
            sender_email="scheduled@allcode.com",
            reply_email="support@allcode.com",
            sender_name="CCAI Python Scheduler",
            accounts=[accounts[0]],
            scheduled_timestamp=tomorrow.isoformat(),
            scheduled_timezone="America/New_York"
        )
        
        response = ccai.email.send_campaign(scheduled_campaign)
        print(f"Scheduled email created successfully: {response}")
        
    except Exception as e:
        print(f"Error testing email functionality: {e}")

def test_webhook_functionality():
    """Test webhook functionality"""
    print("\\nTesting Webhook Functionality...")
    
    # Initialize CCAI client
    ccai = CCAI(
        client_id=os.getenv('CCAI_CLIENT_ID'),
        api_key=os.getenv('CCAI_API_KEY'),
        use_test=True
    )
    
    try:
        # Test webhook registration
        print("\\n1. Testing webhook registration...")
        config = WebhookConfig(
            url="https://example.com/webhook-test",
            events=[WebhookEventType.MESSAGE_SENT, WebhookEventType.MESSAGE_RECEIVED],
            secret="test-secret-123"
        )
        
        # Note: This might fail if the webhook endpoint doesn't exist
        # In a real scenario, you'd have a valid webhook URL
        try:
            response = ccai.webhook.register(config)
            print(f"Webhook registered successfully: {response}")
            webhook_id = response.id
            
            # Test listing webhooks
            print("\\n2. Testing webhook listing...")
            webhooks = ccai.webhook.list()
            print(f"Found {len(webhooks)} webhooks")
            
            # Test webhook update
            print("\\n3. Testing webhook update...")
            update_data = {
                "events": [WebhookEventType.MESSAGE_RECEIVED]
            }
            updated_webhook = ccai.webhook.update(webhook_id, update_data)
            print(f"Webhook updated successfully: {updated_webhook}")
            
            # Test webhook deletion
            print("\\n4. Testing webhook deletion...")
            delete_response = ccai.webhook.delete(webhook_id)
            print(f"Webhook deleted successfully: {delete_response}")
            
        except Exception as e:
            print(f"Webhook API operations failed (this is expected if webhook endpoints don't exist): {e}")
        
        # Test webhook handler creation
        print("\\n5. Testing webhook handler creation...")
        
        def on_message_sent(event):
            print(f"Message sent: {event.message} to {event.to}")
        
        def on_message_received(event):
            print(f"Message received: {event.message} from {event.from_}")
        
        handlers = {
            'on_message_sent': on_message_sent,
            'on_message_received': on_message_received
        }
        
        webhook_handler = ccai.webhook.create_handler(handlers)
        print("Webhook handler created successfully")
        
        # Test signature verification
        print("\\n6. Testing signature verification...")
        is_valid = ccai.webhook.verify_signature("test-signature", "test-body", "test-secret")
        print(f"Signature verification result: {is_valid}")
        
    except Exception as e:
        print(f"Error testing webhook functionality: {e}")

def main():
    """Main test function"""
    print("CCAI Python Library - Email and Webhook Functionality Test")
    print("=" * 60)
    
    test_email_functionality()
    test_webhook_functionality()
    
    print("\\n" + "=" * 60)
    print("Test completed!")

if __name__ == "__main__":
    main()