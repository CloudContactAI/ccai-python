# CCAI Python Client

Version: 1.0.1

A Python client for interacting with the CloudContactAI API.

## Installation

```bash
pip install ccai-python
```

## Usage

### SMS

```python
from ccai_python import CCAI

# Initialize the client
ccai = CCAI(
    client_id="YOUR-CLIENT-ID",
    api_key="YOUR-API-KEY"
)

# Send a single SMS
response = ccai.sms.send_single(
    first_name="John",
    last_name="Doe",
    phone="+15551234567",
    message="Hello ${first_name}, this is a test message!",
    title="Test Campaign"
)

print(f"Message sent with ID: {response.id}")

# Send to multiple recipients
accounts = [
    {"first_name": "John", "last_name": "Doe", "phone": "+15551234567"},
    {"first_name": "Jane", "last_name": "Smith", "phone": "+15559876543"}
]

campaign_response = ccai.sms.send(
    accounts=accounts,
    message="Hello ${first_name} ${last_name}, this is a test message!",
    title="Bulk Test Campaign"
)

print(f"Campaign sent with ID: {campaign_response.campaign_id}")
```

### MMS

```python
from ccai_python import CCAI, Account, SMSOptions

# Initialize the client
ccai = CCAI(
    client_id="YOUR-CLIENT-ID",
    api_key="YOUR-API-KEY"
)

# Define a progress callback
def track_progress(status):
    print(f"Progress: {status}")

# Create options with progress tracking
options = SMSOptions(
    timeout=60,
    retries=3,
    on_progress=track_progress
)

# Complete MMS workflow (get URL, upload image, send MMS)
image_path = "path/to/your/image.jpg"
content_type = "image/jpeg"

# Define recipient
account = Account(
    first_name="John",
    last_name="Doe",
    phone="+15551234567"  # Use E.164 format
)

# Send MMS with image in one step
response = ccai.mms.send_with_image(
    image_path=image_path,
    content_type=content_type,
    accounts=[account],
    message="Hello ${first_name}, check out this image!",
    title="MMS Campaign Example",
    options=options
)

print(f"MMS sent! Campaign ID: {response.campaign_id}")
```

### Email

```python
from ccai_python import CCAI, EmailAccount, EmailCampaign
from datetime import datetime, timedelta

# Initialize the client
ccai = CCAI(
    client_id="YOUR-CLIENT-ID",
    api_key="YOUR-API-KEY"
)

# Send a single email
response = ccai.email.send_single(
    first_name="John",
    last_name="Doe",
    email="john@example.com",
    subject="Welcome to Our Service",
    message="<p>Hello John,</p><p>Thank you for signing up!</p>",
    sender_email="noreply@yourcompany.com",
    reply_email="support@yourcompany.com",
    sender_name="Your Company",
    title="Welcome Email"
)

print(f"Email sent with ID: {response.id}")

# Send email campaign to multiple recipients
accounts = [
    EmailAccount(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        phone=""
    ),
    EmailAccount(
        first_name="Jane",
        last_name="Smith",
        email="jane@example.com",
        phone=""
    )
]

campaign = EmailCampaign(
    subject="Monthly Newsletter",
    title="July 2025 Newsletter",
    message="<h1>Hello ${firstName}!</h1><p>Here's our monthly update...</p>",
    sender_email="newsletter@yourcompany.com",
    reply_email="support@yourcompany.com",
    sender_name="Your Company Newsletter",
    accounts=accounts
)

response = ccai.email.send_campaign(campaign)
print(f"Email campaign sent: {response}")

# Schedule an email for future delivery
tomorrow = datetime.now() + timedelta(days=1)
tomorrow = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)

scheduled_campaign = EmailCampaign(
    subject="Scheduled Email",
    title="Future Email",
    message="<p>This email was scheduled in advance!</p>",
    sender_email="scheduled@yourcompany.com",
    reply_email="support@yourcompany.com",
    sender_name="Your Company",
    accounts=[accounts[0]],
    scheduled_timestamp=tomorrow.isoformat(),
    scheduled_timezone="America/New_York"
)

response = ccai.email.send_campaign(scheduled_campaign)
print(f"Email scheduled: {response}")
```

### Contacts

```python
from ccai_python import CCAI

# Initialize the client
ccai = CCAI(
    client_id="YOUR-CLIENT-ID",
    api_key="YOUR-API-KEY"
)

# Set do not text status using contact ID
response = ccai.contact.set_do_not_text(
    do_not_text=True,
    contact_id="your-contact-id"
)
print(f"Contact {response.contact_id} do not text set to {response.do_not_text}")

# Set do not text status using phone number
response = ccai.contact.set_do_not_text(
    do_not_text=True,
    phone="+15551234567"
)
print(f"Contact {response.contact_id} ({response.phone}) do not text set to {response.do_not_text}")

# Remove do not text status from a contact
response = ccai.contact.set_do_not_text(
    do_not_text=False,
    contact_id="your-contact-id"
)
print(f"Contact {response.contact_id} do not text removed: {response.do_not_text}")
```

### Contact Validator

Validate email addresses and phone numbers.

> Bulk endpoints accept up to 50 contacts per request and are processed server-side in chunks.

```python
from ccai_python import CCAI

ccai = CCAI(
    client_id="YOUR-CLIENT-ID",
    api_key="YOUR-API-KEY"
)

# Validate a single email
email_result = ccai.contact_validator.validate_email("user@example.com")
print(email_result.status)  # "valid" | "invalid" | "risky"
print(email_result.metadata.get("safe_to_send"))  # True | False

# Validate multiple emails (up to 50, processed server-side in chunks)
bulk_emails = ccai.contact_validator.validate_emails(["user@example.com", "bad@invalid.xyz"])
print(bulk_emails.summary.model_dump())  # {"total": 2, "valid": 1, "invalid": 1, "risky": 0, "landline": 0}

# Validate a single phone number
phone_result = ccai.contact_validator.validate_phone("+15551234567", country_code="US")
print(phone_result.status)  # "valid" | "invalid" | "landline"
print(phone_result.metadata.get("carrier_type"))  # "mobile" | "landline" | "voip"

# Validate multiple phone numbers (up to 50, processed server-side in chunks)
bulk_phones = ccai.contact_validator.validate_phones([
    {"phone": "+15551234567"},
    {"phone": "+15559876543", "countryCode": "US"}
])
print(bulk_phones.summary.model_dump())  # {"total": 2, "valid": 1, "invalid": 0, "risky": 0, "landline": 1}
```

### Webhooks

```python
from ccai_python import CCAI, WebhookConfig, WebhookEventType

# Initialize the client
ccai = CCAI(
    client_id="YOUR-CLIENT-ID",
    api_key="YOUR-API-KEY"
)

# Example 1: Register a webhook with auto-generated secret
# If secret is not provided, the server will auto-generate one
config = WebhookConfig(
    url="https://your-domain.com/api/ccai-webhook",
    events=[WebhookEventType.MESSAGE_SENT, WebhookEventType.MESSAGE_RECEIVED]
    # secret not provided - server will auto-generate and return it
)

webhook = ccai.webhook.register(config)
print(f"Webhook registered with ID: {webhook.id}")
print(f"Auto-generated Secret: {webhook.secretKey}")

# Example 2: Register a webhook with a custom secret
config_custom = WebhookConfig(
    url="https://your-domain.com/api/ccai-webhook-v2",
    events=[WebhookEventType.MESSAGE_SENT, WebhookEventType.MESSAGE_RECEIVED],
    secret="your-custom-secret-key"
)

webhook_custom = ccai.webhook.register(config_custom)
print(f"Webhook with custom secret registered: {webhook_custom.id}")

# List all webhooks
webhooks = ccai.webhook.list()
print(f"Found {len(webhooks)} webhooks")

# Update a webhook
updated_webhook = ccai.webhook.update(webhook.id, {
    "url": "https://your-domain.com/api/ccai-webhook-v3"
})
print(f"Webhook updated: {updated_webhook.url}")

# Delete a webhook
result = ccai.webhook.delete(webhook.id)
print(f"Webhook deleted: {result}")

# Verify webhook signature in your handler
def verify_and_handle_webhook(signature, client_id, event_hash, secret):
    if ccai.webhook.verify_signature(signature, client_id, event_hash, secret):
        print(f"Valid webhook signature verified")
    else:
        print("Invalid signature")

# Create a webhook handler for web frameworks
def handle_message_sent(event):
    print(f"Message sent: {event.message} to {event.to}")

def handle_message_received(event):
    print(f"Message received: {event.message} from {event.from_}")

handlers = {
    'on_message_sent': handle_message_sent,
    'on_message_received': handle_message_received
}

webhook_handler = ccai.webhook.create_handler(handlers)

# Use with Flask
from flask import Flask, request, jsonify
import json

app = Flask(__name__)

@app.route('/api/ccai-webhook', methods=['POST'])
def handle_webhook():
    signature = request.headers.get('X-CCAI-Signature', '')
    body = request.get_data(as_text=True)
    secret = 'your-webhook-secret-key'  # Use the secret from webhook registration
    
    # Parse payload to get client_id and event_hash
    payload = json.loads(body)
    client_id = os.getenv('CCAI_CLIENT_ID')
    event_hash = payload.get('eventHash', '')
    
    # Verify signature
    if not ccai.webhook.verify_signature(signature, client_id, event_hash, secret):
        return jsonify({"error": "Invalid signature"}), 401
    
    # Process webhook
    result = webhook_handler(payload)
    return jsonify(result)
```

### Brands

Register and manage brands for TCR (The Campaign Registry) business verification.

```python
from ccai_python import CCAI

ccai = CCAI(
    client_id="YOUR-CLIENT-ID",
    api_key="YOUR-API-KEY"
)

# Create a brand
brand = ccai.brands.create({
    "legalCompanyName": "Collect.org Inc.",
    "dba": "Collect",
    "entityType": "NON_PROFIT",
    "taxId": "123456789",
    "taxIdCountry": "US",
    "country": "US",
    "verticalType": "NON_PROFIT",
    "websiteUrl": "https://www.collect.org",
    "street": "123 Main Street",
    "city": "San Francisco",
    "state": "CA",
    "postalCode": "94105",
    "contactFirstName": "Jane",
    "contactLastName": "Doe",
    "contactEmail": "jane@collect.org",
    "contactPhone": "+14155551234",
})
print(f"Brand created with ID: {brand['id']}")

# Get a brand by ID
fetched = ccai.brands.get(brand["id"])
print(f"Website match score: {fetched.get('websiteMatchScore')}")

# List all brands for the account
brands = ccai.brands.list()
print(f"Found {len(brands)} brand(s)")

# Update a brand (partial update)
updated = ccai.brands.update(brand["id"], {
    "street": "456 Oak Avenue",
    "city": "Los Angeles",
})

# Delete a brand
ccai.brands.delete(brand["id"])
```

#### Entity Types

`PRIVATE_PROFIT`, `PUBLIC_PROFIT`, `NON_PROFIT`, `GOVERNMENT`, `SOLE_PROPRIETOR`

> Note: `PUBLIC_PROFIT` entities require `stockSymbol` and `stockExchange` fields.

#### Vertical Types

`AUTOMOTIVE`, `AGRICULTURE`, `BANKING`, `COMMUNICATION`, `CONSTRUCTION`, `EDUCATION`, `ENERGY`, `ENTERTAINMENT`, `GOVERNMENT`, `HEALTHCARE`, `HOSPITALITY`, `INSURANCE`, `LEGAL`, `MANUFACTURING`, `NON_PROFIT`, `PROFESSIONAL`, `REAL_ESTATE`, `RETAIL`, `TECHNOLOGY`, `TRANSPORTATION`

### Campaigns

Register and manage campaigns for TCR (The Campaign Registry) carrier vetting. Each campaign must be linked to a verified brand.

```python
from ccai_python import CCAI

ccai = CCAI(
    client_id="YOUR-CLIENT-ID",
    api_key="YOUR-API-KEY"
)

# Create a campaign
campaign = ccai.campaigns.create({
    "brandId": 1,
    "useCase": "MIXED",
    "subUseCases": ["CUSTOMER_CARE", "TWO_FACTOR_AUTHENTICATION", "ACCOUNT_NOTIFICATION"],
    "description": "Security codes and support messaging.",
    "messageFlow": "Users opt-in via signup form at https://example.com/signup",
    "hasEmbeddedLinks": True,
    "hasEmbeddedPhone": False,
    "isAgeGated": False,
    "isDirectLending": False,
    "optInKeywords": ["START"],
    "optInMessage": "Welcome! Reply STOP to cancel.",
    "optInProofUrl": "https://example.com/opt-in-proof.png",
    "helpKeywords": ["HELP"],
    "helpMessage": "For HELP email support@example.com.",
    "optOutKeywords": ["STOP"],
    "optOutMessage": "STOP received. You are unsubscribed.",
    "sampleMessages": [
        "Your code is 554321. Reply STOP to cancel.",
        "Your ticket has been updated. Reply HELP for info."
    ]
})
print(f"Campaign created with ID: {campaign['id']}")

# Get a campaign by ID
fetched = ccai.campaigns.get(campaign["id"])

# List all campaigns for the account
campaigns = ccai.campaigns.list()
print(f"Found {len(campaigns)} campaign(s)")

# Update a campaign (partial update)
updated = ccai.campaigns.update(campaign["id"], {
    "description": "Updated description."
})

# Delete a campaign
ccai.campaigns.delete(campaign["id"])
```

#### Use Cases

`TWO_FACTOR_AUTHENTICATION`, `ACCOUNT_NOTIFICATION`, `CUSTOMER_CARE`, `DELIVERY_NOTIFICATION`, `FRAUD_ALERT`, `HIGHER_EDUCATION`, `LOW_VOLUME_MIXED`, `MARKETING`, `MIXED`, `POLLING_VOTING`, `PUBLIC_SERVICE_ANNOUNCEMENT`, `SECURITY_ALERT`

> Note: `MIXED` and `LOW_VOLUME_MIXED` campaigns require 2–3 `subUseCases`.

#### Sub-Use Cases

`TWO_FACTOR_AUTHENTICATION`, `ACCOUNT_NOTIFICATION`, `CUSTOMER_CARE`, `DELIVERY_NOTIFICATION`, `FRAUD_ALERT`, `MARKETING`, `POLLING_VOTING`

## Features

- Send SMS messages to single or multiple recipients
- Send MMS messages with images
- Send Email campaigns with HTML content
- Schedule emails for future delivery
- Brand registration and management for TCR verification
- Campaign registration and management for TCR carrier vetting
- Webhook management (register, update, list, delete)
- Webhook event handling for web frameworks
- Validate email addresses (valid/invalid/risky) and phone numbers (valid/invalid/landline)
- Upload images to S3 with signed URLs
- Variable substitution in messages
- Progress tracking callbacks
- Type hints for better IDE integration
- Comprehensive error handling

## Requirements

- Python 3.10 or higher
- `requests` library
- `pydantic` library

## License

MIT
