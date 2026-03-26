"""
Main export file for the CCAI Python module

:license: MIT
:copyright: 2025 CloudContactAI LLC
"""

from .ccai import CCAI, Account, CCAIConfig
from .sms.sms import SMS, SMSCampaign, SMSResponse, SMSOptions
from .sms.mms import MMS
from .email_service import Email, EmailAccount, EmailCampaign, EmailResponse, EmailOptions
from .webhook import Webhook, WebhookConfig, WebhookEventType, MessageSentEvent, MessageReceivedEvent
from .contact_service import Contact, ContactDoNotTextRequest, ContactDoNotTextResponse

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
    'MessageSentEvent',
    'MessageReceivedEvent',
    'Contact',
    'ContactDoNotTextRequest',
    'ContactDoNotTextResponse'
]

__version__ = '1.0.1'
