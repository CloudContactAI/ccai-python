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

response = ccai.mms.send_with_image(
    image_path="imagePY.jpg",
    content_type="image/jpeg",
    accounts=[account],
    message="Live test MMS from script with image!",
    title="CLI Python MMS Test",
    force_new_campaign=False
)

print("✅ MMS Sent!")
print("📨 Response:", response)