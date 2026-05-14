"""
Main export file for the CCAI Python module

:license: MIT
:copyright: 2025 CloudContactAI LLC
"""

from .ccai import CCAI, Account, CCAIConfig
from .sms.sms import SMS, SMSCampaign, SMSResponse, SMSOptions
from .sms.mms import MMS
from .email_service import Email, EmailAccount, EmailCampaign, EmailResponse, EmailOptions
from .webhook import Webhook, WebhookConfig, WebhookEventType, WebhookEvent
from .contact_service import Contact, ContactDoNotTextRequest, ContactDoNotTextResponse
from .brand_service import Brand
from .campaign_service import Campaign as CampaignService
from .contact_validator_service import (
    ContactValidator,
    EmailValidationResult,
    PhoneValidationResult,
    ValidationSummary,
    BulkEmailValidationResult,
    BulkPhoneValidationResult,
    PhoneInput,
)

__all__ = [
    'CCAI',
    'SMS',
    'MMS',
    'Email',
    'Webhook',
    'Account',
    'EmailAccount',
    'CCAIConfig',
    'SMSCampaign',
    'SMSResponse',
    'SMSOptions',
    'EmailCampaign',
    'EmailResponse',
    'EmailOptions',
    'WebhookConfig',
    'WebhookEventType',
    'WebhookEvent',
    'Contact',
    'ContactDoNotTextRequest',
    'ContactDoNotTextResponse',
    'Brand',
    'CampaignService',
    'ContactValidator',
    'EmailValidationResult',
    'PhoneValidationResult',
    'ValidationSummary',
    'BulkEmailValidationResult',
    'BulkPhoneValidationResult',
    'PhoneInput',
]

__version__ = '1.0.1'
