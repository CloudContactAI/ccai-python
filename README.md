# CCAI Python Client

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

## Features

- Send SMS messages to single or multiple recipients
- Send MMS messages with images
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
