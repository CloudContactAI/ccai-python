import sys
import os
from dotenv import load_dotenv
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

from ccai_python import CCAI, EmailAccount

ccai = CCAI(
    client_id=os.getenv('CCAI_CLIENT_ID'),
    api_key=os.getenv('CCAI_API_KEY'),
    use_test=True
)

response = ccai.email.send_single(
    first_name=os.getenv('TEST_FIRST_NAME'),
    last_name=os.getenv('TEST_LAST_NAME'),
    email=os.getenv('TEST_EMAIL'),
    subject="Test Email from Python",
    message="<h1>Hello Andreas!</h1><p>This is a test email from the Python CCAI client.</p>",
    sender_email="noreply@cloudcontactai.com",
    reply_email="support@cloudcontactai.com",
    sender_name="CloudContactAI",
    title="Python Email Test"
)

print("✅ Email Sent!")
print("📨 Response:", response)