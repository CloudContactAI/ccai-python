from ccai_python import CCAI, Account

ccai = CCAI(client_id="YOUR-CLIENT-ID", api_key="YOUR-API-KEY")

account = Account(
    first_name="John",
    last_name="Doe",
    phone="+15551234567"
)

response = ccai.sms.send(
    accounts=[account],
    message="Live test message from script",
    title="CLI Confirm"
)

print("✅ SMS Sent!")
print("📨 Response:", response)
