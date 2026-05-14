"""
contact_validator_service.py - Email and phone contact validation via CloudContactAI

:license: MIT
:copyright: 2025 CloudContactAI LLC
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class EmailValidationResult(BaseModel):
    contact: str
    type: str
    status: str
    metadata: Dict[str, Any] = {}


class PhoneValidationResult(BaseModel):
    contact: str
    type: str
    status: str
    metadata: Dict[str, Any] = {}


class ValidationSummary(BaseModel):
    total: int
    valid: int
    invalid: int
    risky: int
    landline: int = 0


class BulkEmailValidationResult(BaseModel):
    results: List[EmailValidationResult]
    summary: ValidationSummary


class BulkPhoneValidationResult(BaseModel):
    results: List[PhoneValidationResult]
    summary: ValidationSummary


class PhoneInput(BaseModel):
    phone: str
    countryCode: Optional[str] = None


class ContactValidator:
    """Service for validating email addresses and phone numbers"""

    def __init__(self, ccai) -> None:
        self.ccai = ccai

    def validate_email(self, email: str) -> EmailValidationResult:
        """Validate a single email address"""
        response = self.ccai.request('POST', '/v1/contact-validator/email', {'email': email})
        return EmailValidationResult(**response)

    def validate_emails(self, emails: List[str]) -> BulkEmailValidationResult:
        """Validate multiple email addresses (up to 50)"""
        response = self.ccai.request('POST', '/v1/contact-validator/emails', {'emails': emails})
        return BulkEmailValidationResult(**response)

    def validate_phone(self, phone: str, country_code: Optional[str] = None) -> PhoneValidationResult:
        """Validate a single phone number in E.164 format"""
        response = self.ccai.request(
            'POST', '/v1/contact-validator/phone',
            {'phone': phone, 'countryCode': country_code}
        )
        return PhoneValidationResult(**response)

    def validate_phones(self, phones: List[Dict[str, Any]]) -> BulkPhoneValidationResult:
        """Validate multiple phone numbers (up to 50)"""
        response = self.ccai.request('POST', '/v1/contact-validator/phones', {'phones': phones})
        return BulkPhoneValidationResult(**response)
