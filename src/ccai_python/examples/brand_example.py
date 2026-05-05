"""
Brand registration example using the CCAI Python client

:license: MIT
:copyright: 2025 CloudContactAI LLC
"""

from ccai_python import CCAI

# Initialize the client
ccai = CCAI(
    client_id="YOUR-CLIENT-ID",
    api_key="API-KEY-TOKEN"
)


def brand_examples():
    """Example of managing brands"""
    try:
        # Create a brand
        print("Creating a brand...")
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

        # Get brand by ID
        print("\nFetching brand by ID...")
        fetched = ccai.brands.get(brand["id"])
        print(f"Brand: {fetched['legalCompanyName']}, Score: {fetched.get('websiteMatchScore')}")

        # List all brands
        print("\nListing all brands...")
        brands = ccai.brands.list()
        print(f"Found {len(brands)} brand(s)")

        # Update a brand
        print("\nUpdating brand...")
        updated = ccai.brands.update(brand["id"], {
            "street": "456 Oak Avenue",
            "city": "Los Angeles",
            "contactEmail": "admin@collect.org",
        })
        print(f"Brand updated: {updated['street']}, {updated['city']}")

        # Delete a brand
        print("\nDeleting brand...")
        ccai.brands.delete(brand["id"])
        print("Brand deleted successfully")

    except Exception as error:
        print(f"Error: {error}")
        raise


if __name__ == "__main__":
    brand_examples()
