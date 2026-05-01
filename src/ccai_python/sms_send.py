import os
from dotenv import load_dotenv
from ccai_python import CCAI
from ccai_python.sms.sms import Account

# Load environment variables
load_dotenv()

ccai = CCAI(
    client_id=os.environ['CCAI_CLIENT_ID'],
    api_key=os.environ['CCAI_API_KEY'],
    use_test=True
)

account = Account(
    first_name=os.environ['TEST_FIRST_NAME'],
    last_name=os.environ['TEST_LAST_NAME'],
    phone=os.environ['TEST_PHONE_NUMBER']
)

response = ccai.sms.send(
    accounts=[account],
    message="Live test message from script",
    title="CLI Confirm"
)

print("✅ SMS Sent!")
print("📨 Response:", response)
