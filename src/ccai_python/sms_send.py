import os
from dotenv import load_dotenv
from ccai_python import CCAI, Account

# Load environment variables
load_dotenv()

ccai = CCAI(
    client_id=os.getenv('CCAI_CLIENT_ID'),
    api_key=os.getenv('CCAI_API_KEY')
)

account = Account(
    first_name=os.getenv('TEST_FIRST_NAME'),
    last_name=os.getenv('TEST_LAST_NAME'),
    phone=os.getenv('TEST_PHONE_NUMBER')
)

response = ccai.sms.send(
    accounts=[account],
    message="Live test message from script",
    title="CLI Confirm"
)

print("✅ SMS Sent!")
print("📨 Response:", response)
