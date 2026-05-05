"""Brand service for managing brand registrations via CloudContactAI API"""

from typing import Any, Dict, List, Optional
import re


ENTITY_TYPES = {"PRIVATE_PROFIT", "PUBLIC_PROFIT", "NON_PROFIT", "GOVERNMENT", "SOLE_PROPRIETOR"}
VERTICAL_TYPES = {
    "AUTOMOTIVE", "AGRICULTURE", "BANKING", "COMMUNICATION", "CONSTRUCTION", "EDUCATION",
    "ENERGY", "ENTERTAINMENT", "GOVERNMENT", "HEALTHCARE", "HOSPITALITY", "INSURANCE",
    "LEGAL", "MANUFACTURING", "NON_PROFIT", "PROFESSIONAL", "REAL_ESTATE", "RETAIL",
    "TECHNOLOGY", "TRANSPORTATION",
}
TAX_ID_COUNTRIES = {"US", "CA", "GB", "AU"}
STOCK_EXCHANGES = {"NASDAQ", "NYSE", "AMEX", "TSX", "LON", "JPX", "HKEX", "OTHER"}


def _validate_brand(data: Dict[str, Any], is_create: bool = True) -> None:
    errors: List[Dict[str, str]] = []

    if is_create:
        for field in [
            "legalCompanyName", "entityType", "taxId", "taxIdCountry", "country",
            "verticalType", "websiteUrl", "street", "city", "state", "postalCode",
            "contactFirstName", "contactLastName", "contactEmail", "contactPhone",
        ]:
            if not data.get(field):
                errors.append({"field": field, "message": f"{field} is required"})

    if "entityType" in data and data["entityType"] not in ENTITY_TYPES:
        errors.append({"field": "entityType", "message": "Invalid entity type"})

    if "verticalType" in data and data["verticalType"] not in VERTICAL_TYPES:
        errors.append({"field": "verticalType", "message": "Invalid vertical type"})

    if "taxIdCountry" in data and data["taxIdCountry"] not in TAX_ID_COUNTRIES:
        errors.append({"field": "taxIdCountry", "message": "Invalid tax ID country"})

    if "stockExchange" in data and data["stockExchange"] and data["stockExchange"] not in STOCK_EXCHANGES:
        errors.append({"field": "stockExchange", "message": "Invalid stock exchange"})

    if "websiteUrl" in data and data.get("websiteUrl"):
        url = data["websiteUrl"]
        if not url.startswith("http://") and not url.startswith("https://"):
            errors.append({"field": "websiteUrl", "message": "Website URL must start with http:// or https://"})

    if "contactEmail" in data and data.get("contactEmail"):
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", data["contactEmail"]):
            errors.append({"field": "contactEmail", "message": "Invalid email format"})

    if "taxId" in data and data.get("taxId") and "taxIdCountry" in data:
        if data["taxIdCountry"] in ("US", "CA") and not re.match(r"^\d{9}$", data["taxId"]):
            errors.append({"field": "taxId", "message": f"Tax ID must be exactly 9 digits for {data['taxIdCountry']}"})

    if data.get("entityType") == "PUBLIC_PROFIT":
        if not data.get("stockSymbol"):
            errors.append({"field": "stockSymbol", "message": "Stock symbol is required for PUBLIC_PROFIT entities"})
        if not data.get("stockExchange"):
            errors.append({"field": "stockExchange", "message": "Stock exchange is required for PUBLIC_PROFIT entities"})

    if errors:
        raise ValueError({"message": "Validation failed", "errors": errors})


class Brand:
    """Brand service for managing brand registrations"""

    def __init__(self, ccai):
        self._ccai = ccai

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new brand"""
        _validate_brand(data, is_create=True)
        return self._ccai.custom_request("post", "/v1/brands", data, base_url=self._ccai.compliance_base_url)

    def get(self, brand_id: int) -> Dict[str, Any]:
        """Get a brand by ID"""
        return self._ccai.custom_request("get", f"/v1/brands/{brand_id}", base_url=self._ccai.compliance_base_url)

    def list(self) -> List[Dict[str, Any]]:
        """List all brands for the authenticated account"""
        return self._ccai.custom_request("get", "/v1/brands", base_url=self._ccai.compliance_base_url)

    def update(self, brand_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Partially update a brand"""
        _validate_brand(data, is_create=False)
        return self._ccai.custom_request("patch", f"/v1/brands/{brand_id}", data, base_url=self._ccai.compliance_base_url)

    def delete(self, brand_id: int) -> None:
        """Delete a brand"""
        self._ccai.custom_request("delete", f"/v1/brands/{brand_id}", base_url=self._ccai.compliance_base_url)
