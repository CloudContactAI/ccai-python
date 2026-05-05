"""
Campaign registration example using the CCAI Python client

:license: MIT
:copyright: 2025 CloudContactAI LLC
"""

from ccai_python import CCAI

# Initialize the client
ccai = CCAI(
    client_id="YOUR-CLIENT-ID",
    api_key="API-KEY-TOKEN"
)


def campaign_examples():
    """Example of managing campaigns"""
    try:
        # Create a campaign (assumes brand ID 1 exists)
        print("Creating a campaign...")
        campaign = ccai.campaigns.create({
            "brandId": 1,
            "useCase": "MIXED",
            "subUseCases": ["CUSTOMER_CARE", "TWO_FACTOR_AUTHENTICATION", "ACCOUNT_NOTIFICATION"],
            "description": "This campaign handles security codes and support for Collect.org.",
            "messageFlow": "Users opt-in via our signup form checkbox at https://collect.org/signup",
            "termsLink": "https://collect.org/terms",
            "privacyLink": "https://collect.org/privacy",
            "hasEmbeddedLinks": True,
            "hasEmbeddedPhone": False,
            "isAgeGated": False,
            "isDirectLending": False,
            "optInKeywords": ["START", "JOIN"],
            "optInMessage": "Welcome to Collect.org! Msg&Data rates may apply. Reply STOP to cancel.",
            "optInProofUrl": "https://collect.org/images/opt-in-proof.png",
            "helpKeywords": ["HELP", "INFO"],
            "helpMessage": "Collect.org: For help email support@collect.org. Reply STOP to cancel.",
            "optOutKeywords": ["STOP", "UNSUBSCRIBE"],
            "optOutMessage": "Collect.org: You have been unsubscribed. STOP received.",
            "sampleMessages": [
                "Your Collect.org security code is 554321. Reply STOP to cancel.",
                "Hi [Name], your ticket #[ID] has been updated. Reply HELP for more info."
            ]
        })
        print(f"Campaign created with ID: {campaign['id']}, fee: ${campaign['monthlyFee']}/mo")

        # Get campaign by ID
        print("\nFetching campaign by ID...")
        fetched = ccai.campaigns.get(campaign["id"])
        print(f"Campaign: {fetched['useCase']}, Brand: {fetched['brandId']}")

        # List all campaigns
        print("\nListing all campaigns...")
        campaigns = ccai.campaigns.list()
        print(f"Found {len(campaigns)} campaign(s)")

        # Update a campaign
        print("\nUpdating campaign...")
        updated = ccai.campaigns.update(campaign["id"], {
            "description": "Updated campaign description for Collect.org messaging.",
            "sampleMessages": [
                "Your Collect.org code is 123456. Reply STOP to opt-out.",
                "Your support ticket has been resolved. Reply HELP for more info.",
                "Your payment of $50.00 was received. Reply STOP to cancel."
            ]
        })
        print(f"Campaign updated: {updated['description']}")

        # Delete a campaign
        print("\nDeleting campaign...")
        ccai.campaigns.delete(campaign["id"])
        print("Campaign deleted successfully")

    except Exception as error:
        print(f"Error: {error}")
        raise


if __name__ == "__main__":
    campaign_examples()
