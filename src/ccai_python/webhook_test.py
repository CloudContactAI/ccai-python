import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import os
from dotenv import load_dotenv
from ccai_python import CCAI, Account

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

ccai = CCAI(
    client_id=os.getenv('CCAI_CLIENT_ID'),
    api_key=os.getenv('CCAI_API_KEY'),
    use_test=True
)

# Test webhook by sending SMS (which will trigger webhook events)
print("🚀 Sending test SMS to trigger webhook...")

account = Account(
    first_name=os.getenv('TEST_FIRST_NAME'),
    last_name=os.getenv('TEST_LAST_NAME'),
    phone=os.getenv('TEST_PHONE_NUMBER')
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