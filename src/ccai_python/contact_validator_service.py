"""
contact_validator_service.py - Email and phone contact validation via CloudContactAI

:license: MIT
:copyright: 2025 CloudContactAI LLC
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class EmailValidationChecks(BaseModel):
    """
    The six checks of an email validation, each with its own Amazon SES verdict:
    'HIGH', 'MEDIUM', 'LOW' or 'UNKNOWN' (a verdict SES did not return).
    """
    hasValidSyntax: Optional[str] = None      # The address follows RFC format rules (good value: HIGH)
    hasValidDnsRecords: Optional[str] = None  # The domain has DNS/MX records to receive mail (good value: HIGH)
    mailboxExists: Optional[str] = None       # The mailbox exists and can receive messages (good value: HIGH)
    isRoleAddress: Optional[str] = None       # A role address such as admin@ or info@ (good value: LOW)
    isDisposable: Optional[str] = None        # A disposable or temporary email provider (good value: LOW)
    isRandomInput: Optional[str] = None       # The address looks randomly generated (good value: LOW)


class EmailValidationResult(BaseModel):
    contactField: str
    type: str
    status: str
    metadata: Dict[str, Any] = {}

    # The fields below are read from `metadata`. They are None when the response does not have them: the
    # account does not have Email Address Validation, or the address was not checked (see `metadata["error"]`).

    @property
    def verdict(self) -> Optional[str]:
        """The overall verdict: 'HIGH', 'MEDIUM', 'LOW' or 'UNKNOWN'"""
        return self.metadata.get('verdict')

    @property
    def checks(self) -> Optional[EmailValidationChecks]:
        """The six checks, each with its own verdict"""
        checks = self.metadata.get('checks')
        return EmailValidationChecks(**checks) if isinstance(checks, dict) else None

    @property
    def validatedAt(self) -> Optional[str]:
        """When Amazon SES checked the address (ISO 8601). None when the address was rejected without a check."""
        return self.metadata.get('validatedAt')

    @property
    def reused(self) -> Optional[bool]:
        """True when the result is a saved check from the last 30 days, instead of a new one"""
        return self.metadata.get('reused')


class PhoneValidationResult(BaseModel):
    contactField: str
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
        """
        Validate a single email address with Amazon SES.

        Raises APIError with status_code 403 when Email Address Validation is not enabled for the account,
        and 502 when SES rejects the check (the message says why).
        """
        response = self.ccai.request('POST', '/v1/contact-validator/email', {'email': email})
        return EmailValidationResult(**response)

    def validate_emails(self, emails: List[str]) -> BulkEmailValidationResult:
        """
        Validate multiple email addresses (up to 10 per request).

        Raises APIError with status_code 403 when Email Address Validation is not enabled for the account.
        An address that SES fails to check comes back as 'invalid', with the reason in metadata["error"].
        """
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
