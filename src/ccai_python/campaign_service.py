"""Campaign service for managing campaign registrations via CloudContactAI API"""

from typing import Any, Dict, List


CAMPAIGN_USE_CASES = {
    "TWO_FACTOR_AUTHENTICATION", "ACCOUNT_NOTIFICATION", "CUSTOMER_CARE", "DELIVERY_NOTIFICATION",
    "FRAUD_ALERT", "HIGHER_EDUCATION", "LOW_VOLUME_MIXED", "MARKETING", "MIXED",
    "POLLING_VOTING", "PUBLIC_SERVICE_ANNOUNCEMENT", "SECURITY_ALERT",
}
CAMPAIGN_SUB_USE_CASES = {
    "TWO_FACTOR_AUTHENTICATION", "ACCOUNT_NOTIFICATION", "CUSTOMER_CARE", "DELIVERY_NOTIFICATION",
    "FRAUD_ALERT", "MARKETING", "POLLING_VOTING",
}

MIXED_USE_CASES = {"MIXED", "LOW_VOLUME_MIXED"}

REQUIRED_FIELDS = [
    "brandId", "useCase", "description", "messageFlow", "hasEmbeddedLinks",
    "hasEmbeddedPhone", "isAgeGated", "isDirectLending", "optInKeywords",
    "optInMessage", "optInProofUrl", "helpKeywords", "helpMessage",
    "optOutKeywords", "optOutMessage", "sampleMessages",
]


def _validate_campaign(data: Dict[str, Any], is_create: bool = True) -> None:
    errors: List[Dict[str, str]] = []

    if is_create:
        for field in REQUIRED_FIELDS:
            if not data.get(field) and data.get(field) is not False:
                errors.append({"field": field, "message": f"{field} is required"})

    if "useCase" in data and data["useCase"] not in CAMPAIGN_USE_CASES:
        errors.append({"field": "useCase", "message": "Invalid use case"})

    use_case = data.get("useCase")
    sub_use_cases = data.get("subUseCases")

    if use_case in MIXED_USE_CASES:
        if not sub_use_cases or not isinstance(sub_use_cases, list) or not (2 <= len(sub_use_cases) <= 3):
            errors.append({"field": "subUseCases", "message": "MIXED/LOW_VOLUME_MIXED requires 2-3 sub use cases"})
        elif sub_use_cases:
            for suc in sub_use_cases:
                if suc not in CAMPAIGN_SUB_USE_CASES:
                    errors.append({"field": "subUseCases", "message": f"Invalid sub use case: {suc}"})
    elif use_case and sub_use_cases:
        errors.append({"field": "subUseCases", "message": "subUseCases should be empty for non-MIXED use cases"})

    sample_messages = data.get("sampleMessages")
    if sample_messages is not None:
        if not isinstance(sample_messages, list) or not (2 <= len(sample_messages) <= 5):
            errors.append({"field": "sampleMessages", "message": "sampleMessages must contain 2-5 items"})
        elif sample_messages:
            opt_out_keywords = data.get("optOutKeywords") or []
            help_keywords = data.get("helpKeywords") or []

            has_opt_out = any(
                "Reply STOP" in msg or any(f"Reply {kw}" in msg for kw in opt_out_keywords)
                for msg in sample_messages
            )
            if not has_opt_out:
                errors.append({"field": "sampleMessages", "message": "At least one sample must contain 'Reply STOP' or 'Reply {optOutKeyword}'"})

            has_help = any(
                "Reply HELP" in msg or any(f"Reply {kw}" in msg for kw in help_keywords)
                for msg in sample_messages
            )
            if not has_help:
                errors.append({"field": "sampleMessages", "message": "At least one sample must contain 'Reply HELP' or 'Reply {helpKeyword}'"})

    opt_out_message = data.get("optOutMessage")
    if opt_out_message is not None:
        opt_out_keywords = data.get("optOutKeywords") or []
        if "STOP" not in opt_out_message and not any(kw in opt_out_message for kw in opt_out_keywords):
            errors.append({"field": "optOutMessage", "message": "optOutMessage must contain 'STOP' or at least one optOutKeyword"})

    help_message = data.get("helpMessage")
    if help_message is not None:
        help_keywords = data.get("helpKeywords") or []
        if "HELP" not in help_message and not any(kw in help_message for kw in help_keywords):
            errors.append({"field": "helpMessage", "message": "helpMessage must contain 'HELP' or at least one helpKeyword"})

    opt_in_proof_url = data.get("optInProofUrl")
    if opt_in_proof_url is not None:
        if not opt_in_proof_url.startswith("http://") and not opt_in_proof_url.startswith("https://"):
            errors.append({"field": "optInProofUrl", "message": "optInProofUrl must start with http:// or https://"})

    for link_field in ("termsLink", "privacyLink"):
        val = data.get(link_field)
        if val:
            if not val.startswith("http://") and not val.startswith("https://"):
                errors.append({"field": link_field, "message": f"{link_field} must start with http:// or https://"})

    if errors:
        raise ValueError({"message": "Validation failed", "errors": errors})


class Campaign:
    """Campaign service for managing campaign registrations"""

    def __init__(self, ccai):
        self._ccai = ccai

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new campaign"""
        _validate_campaign(data, is_create=True)
        return self._ccai.custom_request("post", "/v1/campaigns", data, base_url=self._ccai.compliance_base_url)

    def get(self, campaign_id: int) -> Dict[str, Any]:
        """Get a campaign by ID"""
        return self._ccai.custom_request("get", f"/v1/campaigns/{campaign_id}", base_url=self._ccai.compliance_base_url)

    def list(self) -> List[Dict[str, Any]]:
        """List all campaigns for the authenticated account"""
        return self._ccai.custom_request("get", "/v1/campaigns", base_url=self._ccai.compliance_base_url)

    def update(self, campaign_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Partially update a campaign"""
        _validate_campaign(data, is_create=False)
        return self._ccai.custom_request("patch", f"/v1/campaigns/{campaign_id}", data, base_url=self._ccai.compliance_base_url)

    def delete(self, campaign_id: int) -> None:
        """Delete a campaign"""
        self._ccai.custom_request("delete", f"/v1/campaigns/{campaign_id}", base_url=self._ccai.compliance_base_url)
