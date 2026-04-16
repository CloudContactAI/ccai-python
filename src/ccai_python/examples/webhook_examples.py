"""
Examples of using CloudContactAI webhooks with Python web frameworks

This example shows how to create webhook handlers for different Python web frameworks
like Flask, FastAPI, and Django.
"""

from typing import Dict, Any
from ccai_python import CCAI
from ccai_python.webhook import (
    Webhook, WebhookConfig, WebhookEventType, 
    MessageSentEvent, MessageReceivedEvent
)

# Initialize the CCAI client
ccai = CCAI(
    client_id="<YOUR_CLIENT_ID>",
    api_key="<YOUR_API_KEY>"
)

def register_webhook_example():
    """Example: Register a new webhook with auto-generated secret"""
    try:
        # Example 1: Auto-generated secret (server will generate and return it)
        config = WebhookConfig(
            url="https://your-domain.com/api/ccai-webhook",
            events=[WebhookEventType.MESSAGE_SENT, WebhookEventType.MESSAGE_RECEIVED]
            # secret not provided - server will auto-generate
        )

        response = ccai.webhook.register(config)
        print("Webhook registered successfully with auto-generated secret:", response)
        print(f"Auto-generated Secret Key: {getattr(response, 'secretKey', 'N/A')}")

        # Example 2: Custom secret
        config_custom = WebhookConfig(
            url="https://your-domain.com/api/ccai-webhook-v2",
            events=[WebhookEventType.MESSAGE_SENT, WebhookEventType.MESSAGE_RECEIVED],
            secret="my-custom-secret-key"
        )

        response_custom = ccai.webhook.register(config_custom)
        print("Webhook registered with custom secret:", response_custom)

        return response.id
    except Exception as error:
        print("Error registering webhook:", error)
        return None

def list_webhooks_example():
    """Example: List all registered webhooks"""
    try:
        webhooks = ccai.webhook.list()
        print("Registered webhooks:", webhooks)
        return webhooks
    except Exception as error:
        print("Error listing webhooks:", error)
        return []

def update_webhook_example(webhook_id: str):
    """Example: Update an existing webhook"""
    try:
        update_data = {
            "url": "https://your-domain.com/api/updated-ccai-webhook",
            "events": [WebhookEventType.MESSAGE_RECEIVED]
        }
        
        response = ccai.webhook.update(webhook_id, update_data)
        print("Webhook updated successfully:", response)
    except Exception as error:
        print("Error updating webhook:", error)

def delete_webhook_example(webhook_id: str):
    """Example: Delete a webhook"""
    try:
        response = ccai.webhook.delete(webhook_id)
        print("Webhook deleted successfully:", response)
    except Exception as error:
        print("Error deleting webhook:", error)

# Flask example
def create_flask_webhook_handler():
    """Example Flask webhook handler"""
    from flask import Flask, request, jsonify
    
    app = Flask(__name__)
    
    @app.route('/api/ccai-webhook', methods=['POST'])
    def handle_webhook():
        try:
            payload = request.get_json()
            
            # Optional: Verify webhook signature
            signature = request.headers.get('X-CCAI-Signature')
            if signature:
                is_valid = ccai.webhook.verify_signature(
                    signature, 
                    request.get_data(as_text=True), 
                    "your-webhook-secret"
                )
                if not is_valid:
                    return jsonify({"error": "Invalid signature"}), 401
            
            # Process the webhook based on its type
            if payload.get('type') == WebhookEventType.MESSAGE_SENT:
                event = MessageSentEvent(**payload)
                handle_message_sent(event)
            elif payload.get('type') == WebhookEventType.MESSAGE_RECEIVED:
                event = MessageReceivedEvent(**payload)
                handle_message_received(event)
            
            return jsonify({"received": True})
        except Exception as e:
            print(f"Error processing webhook: {e}")
            return jsonify({"error": "Internal server error"}), 500
    
    return app

# FastAPI example
def create_fastapi_webhook_handler():
    """Example FastAPI webhook handler"""
    from fastapi import FastAPI, Request, HTTPException
    from fastapi.responses import JSONResponse
    
    app = FastAPI()
    
    @app.post("/api/ccai-webhook")
    async def handle_webhook(request: Request):
        try:
            payload = await request.json()
            
            # Optional: Verify webhook signature
            signature = request.headers.get('x-ccai-signature')
            if signature:
                body = await request.body()
                is_valid = ccai.webhook.verify_signature(
                    signature, 
                    body.decode('utf-8'), 
                    "your-webhook-secret"
                )
                if not is_valid:
                    raise HTTPException(status_code=401, detail="Invalid signature")
            
            # Process the webhook based on its type
            if payload.get('type') == WebhookEventType.MESSAGE_SENT:
                event = MessageSentEvent(**payload)
                await handle_message_sent_async(event)
            elif payload.get('type') == WebhookEventType.MESSAGE_RECEIVED:
                event = MessageReceivedEvent(**payload)
                await handle_message_received_async(event)
            
            return JSONResponse({"received": True})
        except Exception as e:
            print(f"Error processing webhook: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    return app

# Django example
def create_django_webhook_view():
    """Example Django webhook view"""
    from django.http import JsonResponse
    from django.views.decorators.csrf import csrf_exempt
    from django.views.decorators.http import require_http_methods
    import json
    
    @csrf_exempt
    @require_http_methods(["POST"])
    def handle_webhook(request):
        try:
            payload = json.loads(request.body)
            
            # Optional: Verify webhook signature
            signature = request.META.get('HTTP_X_CCAI_SIGNATURE')
            if signature:
                is_valid = ccai.webhook.verify_signature(
                    signature, 
                    request.body.decode('utf-8'), 
                    "your-webhook-secret"
                )
                if not is_valid:
                    return JsonResponse({"error": "Invalid signature"}, status=401)
            
            # Process the webhook based on its type
            if payload.get('type') == WebhookEventType.MESSAGE_SENT:
                event = MessageSentEvent(**payload)
                handle_message_sent(event)
            elif payload.get('type') == WebhookEventType.MESSAGE_RECEIVED:
                event = MessageReceivedEvent(**payload)
                handle_message_received(event)
            
            return JsonResponse({"received": True})
        except Exception as e:
            print(f"Error processing webhook: {e}")
            return JsonResponse({"error": "Internal server error"}, status=500)
    
    return handle_webhook

def handle_message_sent(event: MessageSentEvent):
    """Handle outbound message events"""
    print("Message sent event received:")
    print(f"Campaign: {event.campaign.title} (ID: {event.campaign.id})")
    print(f"From: {event.from_}")
    print(f"To: {event.to}")
    print(f"Message: {event.message}")
    
    # Add your custom logic here
    # For example, updating your database, triggering other processes, etc.

def handle_message_received(event: MessageReceivedEvent):
    """Handle inbound message events"""
    print("Message received event received:")
    print(f"Campaign: {event.campaign.title} (ID: {event.campaign.id})")
    print(f"From: {event.from_}")
    print(f"To: {event.to}")
    print(f"Message: {event.message}")
    
    # Add your custom logic here
    # For example, updating your database, triggering automated responses, etc.

async def handle_message_sent_async(event: MessageSentEvent):
    """Async handler for outbound message events"""
    print("Message sent event received (async):")
    print(f"Campaign: {event.campaign.title} (ID: {event.campaign.id})")
    print(f"From: {event.from_}")
    print(f"To: {event.to}")
    print(f"Message: {event.message}")
    
    # Add your async custom logic here

async def handle_message_received_async(event: MessageReceivedEvent):
    """Async handler for inbound message events"""
    print("Message received event received (async):")
    print(f"Campaign: {event.campaign.title} (ID: {event.campaign.id})")
    print(f"From: {event.from_}")
    print(f"To: {event.to}")
    print(f"Message: {event.message}")
    
    # Add your async custom logic here

# Generic webhook handler using the built-in create_handler method
def create_generic_webhook_handler():
    """Create a generic webhook handler"""
    handlers = {
        'on_message_sent': handle_message_sent,
        'on_message_received': handle_message_received
    }
    
    return Webhook.create_handler(handlers)

if __name__ == "__main__":
    # Example usage
    webhook_id = register_webhook_example()
    if webhook_id:
        list_webhooks_example()
        update_webhook_example(webhook_id)
        # delete_webhook_example(webhook_id)  # Uncomment to delete