"""
Basic example using the CCAI Python client

:license: MIT
:copyright: 2025 CloudContactAI LLC
"""

from ccai_python import CCAI, Account, SMSResponse

# Create a new CCAI client
ccai = CCAI(
    client_id="YOUR-CLIENT-ID",
    api_key="API-KEY-TOKEN"
)

# Example recipients
accounts = [
    Account(
        first_name="John",
        last_name="Doe",
        phone="+15551234567"  # Use E.164 format
    )
]

# Alternative dictionary format
dict_accounts = [
    {
        "first_name": "John",
        "last_name": "Doe",
        "phone": "+15551234567"  # Use E.164 format
    }
]

# Message with variable placeholders
message = "Hello ${first_name} ${last_name}, this is a test message!"
title = "Test Campaign"


def send_messages() -> dict:
    """Example of sending SMS messages"""
    try:
        # Method 1: Send SMS to multiple recipients
        print('Sending campaign to multiple recipients...')
        campaign_response: SMSResponse = ccai.sms.send(
            accounts=accounts,
            message=message,
            title=title
        )
        print('SMS campaign sent successfully!')
        print(campaign_response.model_dump())

        # Method 2: Send SMS to a single recipient
        print('\nSending message to a single recipient...')
        single_response: SMSResponse = ccai.sms.send_single(
            first_name="Jane",
            last_name="Smith",
            phone="+15559876543",
            message="Hi ${first_name}, thanks for your interest!",
            title="Single Message Test"
        )
        print('Single SMS sent successfully!')
        print(single_response.model_dump())

        return {
            "campaign_response": campaign_response.model_dump(),
            "single_response": single_response.model_dump()
        }
    except Exception as error:
        print(f'Error sending SMS: {str(error)}')
        raise


if __name__ == "__main__":
    try:
        results = send_messages()
        print('\nAll messages sent successfully!')
        print(f'\nResults: {results}')
    except Exception:
        print('\nFailed to send one or more messages.')
