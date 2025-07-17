from ccai_python import CCAI, Account

ccai = CCAI(client_id="YOUR-CLIENT-ID", api_key="YOUR-API-KEY")

account = Account(
    first_name="John",
    last_name="Doe",
    phone="+15551234567"
)

response = ccai.mms.send_with_image(
    image_path="imagePY.jpg",
    content_type="image/jpeg",
    accounts=[account],
    message="Live test MMS from script with image!",
    title="CLI MMS Test"
)

print("✅ MMS Sent!")
print("📨 Response:", response)