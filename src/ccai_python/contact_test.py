import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
from ccai_python import CCAI

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

ccai = CCAI(
    client_id=os.environ['CCAI_CLIENT_ID'] ,
    api_key=os.environ['CCAI_API_KEY'] 
)

# Test set_do_not_text with phone number
print("🚀 Testing contact set_do_not_text...")

try:
    response = ccai.contact.set_do_not_text(
        do_not_text=True,
        phone=os.getenv('TEST_PHONE_NUMBER')
    )

    print("✅ Contact marked as do not text!")
    print(f"   Contact ID: {response.contact_id}")
    print(f"   Phone: {response.phone}")
    print(f"   Do Not Text: {response.do_not_text}")
except Exception as e:
    print("❌ Error setting do-not-text:", e)
