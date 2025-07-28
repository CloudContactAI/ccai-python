import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ccai_python import CCAI, Account

ccai = CCAI(client_id="2682", api_key="eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJpbmZvQGFsbGNvZGUuY29tIiwiaXNzIjoiY2xvdWRjb250YWN0IiwibmJmIjoxNzE5NDQwMjM2LCJpYXQiOjE3MTk0NDAyMzYsInJvbGUiOiJVU0VSIiwiY2xpZW50SWQiOjI2ODIsImlkIjoyNzY0LCJ0eXBlIjoiQVBJX0tFWSIsImtleV9yYW5kb21faWQiOiI1MGRiOTUzZC1hMjUxLTRmZjMtODI5Yi01NjIyOGRhOGE1YTAifQ.PKVjXYHdjBMum9cTgLzFeY2KIb9b2tjawJ0WXalsb8Bckw1RuxeiYKS1bw5Cc36_Rfmivze0T7r-Zy0PVj2omDLq65io0zkBzIEJRNGDn3gx_AqmBrJ3yGnz9s0WTMr2-F1TFPUByzbj1eSOASIKeI7DGufTA5LDrRclVkz32Oo")

# Test webhook by sending SMS (which will trigger webhook events)
print("🚀 Sending test SMS to trigger webhook...")

account = Account(
    first_name="Test",
    last_name="User", 
    phone="+14156961732"
)

try:
    response = ccai.sms.send(
        accounts=[account],
        message="Hello ${first_name}! This is a webhook test message.",
        title="Webhook Test Campaign"
    )
    
    print("✅ SMS sent successfully:", response)
    print("📡 Check your webhook server console for the webhook event!")
except Exception as e:
    print("❌ Error sending SMS:", e)