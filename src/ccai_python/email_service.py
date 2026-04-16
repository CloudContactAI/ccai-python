"""
email_service.py - Email service for the CCAI API
Handles sending email campaigns through the Cloud Contact AI platform.

:license: MIT
:copyright: 2025 CloudContactAI LLC
"""

from typing import Any, Dict, List, Optional, Callable
from pydantic import BaseModel, Field, model_validator
import requests


class EmailAccount(BaseModel):
    """Account model for email recipients"""
    first_name: str = Field(..., description="Recipient's first name")
    last_name: str = Field(..., description="Recipient's last name")
    email: str = Field(..., description="Recipient's email address")
    phone: str = Field(default="", description="Phone number (required by base Account type)")
    custom_account_id: Optional[str] = Field(
        default=None,
        description="External ID to link this account to an external system. Sent as 'customAccountId'."
    )
    data: Optional[Dict[str, str]] = Field(
        default=None,
        description="Additional key-value pairs for variable substitution in email templates. "
                    "Sent to the API as 'data'."
    )


class EmailCampaign(BaseModel):
    """Email campaign configuration"""
    subject: str = Field(..., description="Email subject")
    title: str = Field(..., description="Campaign title")
    message: str = Field(..., description="HTML message content")
    text_content: Optional[str] = Field(default=None, description="Plain-text version of the email body")
    sender_email: str = Field(..., description="Sender's email address")
    reply_email: str = Field(..., description="Reply-to email address")
    sender_name: str = Field(..., description="Sender's name")
    accounts: List[EmailAccount] = Field(..., description="List of recipients")
    campaign_type: str = Field(default="EMAIL", description="Campaign type")
    scheduled_timestamp: Optional[str] = Field(default=None, description="Scheduled delivery timestamp")
    scheduled_timezone: Optional[str] = Field(default=None, description="Scheduled delivery timezone")
    add_to_list: str = Field(default="noList", description="List management option")
    selected_list: Optional[Dict[str, Optional[str]]] = Field(default=None, description="Selected list")
    list_id: Optional[str] = Field(default=None, description="List ID")
    contact_input: str = Field(default="accounts", description="Contact input type")
    replace_contacts: Optional[bool] = Field(default=None, description="Replace contacts option")
    email_template_id: Optional[str] = Field(default=None, description="Email template ID")
    flux_id: Optional[str] = Field(default=None, description="Flux ID")
    from_type: str = Field(default="single", description="From type")
    senders: List[Any] = Field(default_factory=list, description="Senders list")
    editor: Optional[str] = Field(default=None, description="Editor type")
    file_key: Optional[str] = Field(default=None, description="File key")


class EmailResponse(BaseModel):
    """Response from email API"""
    id: Optional[int] = Field(default=None, description="Message ID")
    status: Optional[str] = Field(default=None, description="Status")
    campaign_id: Optional[str] = Field(default=None, description="Campaign ID")
    messages_sent: Optional[int] = Field(default=None, description="Number of messages sent")
    timestamp: Optional[str] = Field(default=None, description="Timestamp")
    message: Optional[str] = Field(default=None, description="Human-readable message from the API")
    response_id: Optional[str] = Field(default=None, description="Unique response identifier")

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, values):
        if "responseId" in values and "response_id" not in values:
            values["response_id"] = values.pop("responseId")
        if "campaignId" in values and "campaign_id" not in values:
            values["campaign_id"] = values.pop("campaignId")
        if "messagesSent" in values and "messages_sent" not in values:
            values["messages_sent"] = values.pop("messagesSent")
        return values

    model_config = {"extra": "allow"}


class EmailOptions(BaseModel):
    """Options for email operations"""
    timeout: Optional[int] = Field(default=30, description="Timeout in seconds")
    retries: Optional[int] = Field(default=3, description="Number of retries")
    on_progress: Optional[Callable[[str], None]] = Field(default=None, description="Progress callback")

    class Config:
        arbitrary_types_allowed = True


class Email:
    """Email service for sending email campaigns"""

    def __init__(self, ccai):
        self.ccai = ccai

    def _build_payload(self, campaign: "EmailCampaign") -> dict:
        """Build camelCase API payload from the campaign model."""
        def account_to_dict(acc: "EmailAccount") -> dict:
            d: dict = {
                "firstName": acc.first_name,
                "lastName": acc.last_name,
                "email": acc.email,
            }
            if acc.phone:
                d["phone"] = acc.phone
            if acc.custom_account_id is not None:
                d["customAccountId"] = acc.custom_account_id
            if acc.data is not None:
                d["data"] = acc.data
            return d

        payload: dict = {
            "subject": campaign.subject,
            "title": campaign.title,
            "message": campaign.message,
            "senderEmail": campaign.sender_email,
            "replyEmail": campaign.reply_email,
            "senderName": campaign.sender_name,
            "accounts": [account_to_dict(a) for a in campaign.accounts],
            "campaignType": campaign.campaign_type,
            "addToList": campaign.add_to_list,
            "contactInput": campaign.contact_input,
            "fromType": campaign.from_type,
            "senders": campaign.senders,
        }
        if campaign.scheduled_timestamp is not None:
            payload["scheduledTimestamp"] = campaign.scheduled_timestamp
        if campaign.scheduled_timezone is not None:
            payload["scheduledTimezone"] = campaign.scheduled_timezone
        if campaign.selected_list is not None:
            payload["selectedList"] = campaign.selected_list
        if campaign.list_id is not None:
            payload["listId"] = campaign.list_id
        if campaign.replace_contacts is not None:
            payload["replaceContacts"] = campaign.replace_contacts
        if campaign.email_template_id is not None:
            payload["emailTemplateId"] = campaign.email_template_id
        if campaign.flux_id is not None:
            payload["fluxId"] = campaign.flux_id
        if campaign.editor is not None:
            payload["editor"] = campaign.editor
        if campaign.file_key is not None:
            payload["fileKey"] = campaign.file_key
        if campaign.text_content is not None:
            payload["textContent"] = campaign.text_content
        return payload

    def make_email_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an authenticated API request to the email campaigns API with required headers"""
        url = f"{self.ccai.email_base_url}{endpoint}"

        headers = {
            "Authorization": f"Bearer {self.ccai.api_key}",
            "Content-Type": "application/json",
            "Accept": "*/*",
            "AccountId": str(self.ccai.client_id),
            "ClientId": str(self.ccai.client_id)
        }

        try:
            response = requests.request(
                method=method.upper(),
                url=url,
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            if e.response is not None:
                try:
                    error_data = e.response.json()
                    error_message = str(error_data)
                except (ValueError, TypeError):
                    error_message = e.response.text or str(e)
                raise Exception(f"API Error: {e.response.status_code} - {error_message}")
            raise
        except requests.RequestException as e:
            raise Exception(f"Network error: {str(e)}")

    def send(
        self,
        accounts: List[EmailAccount],
        subject: str,
        message: str,
        sender_email: str,
        reply_email: str,
        sender_name: str,
        title: Optional[str] = None,
        options: Optional[EmailOptions] = None
    ) -> EmailResponse:
        """Send an email campaign to multiple recipients"""
        campaign = EmailCampaign(
            subject=subject,
            title=title or subject,
            message=message,
            sender_email=sender_email,
            reply_email=reply_email,
            sender_name=sender_name,
            accounts=accounts
        )
        return self.send_campaign(campaign, options)

    def send_campaign(
        self,
        campaign: EmailCampaign,
        options: Optional[EmailOptions] = None
    ) -> EmailResponse:
        """Send an email campaign to multiple recipients"""
        if not campaign.accounts:
            raise ValueError("At least one account is required")

        if not campaign.subject:
            raise ValueError("Subject is required")
        if not campaign.title:
            raise ValueError("Campaign title is required")
        if not campaign.message:
            raise ValueError("Message content is required")
        if not campaign.sender_email:
            raise ValueError("Sender email is required")
        if not campaign.reply_email:
            raise ValueError("Reply email is required")
        if not campaign.sender_name:
            raise ValueError("Sender name is required")

        if options and options.on_progress:
            options.on_progress("Preparing to send email campaign")

        try:
            if options and options.on_progress:
                options.on_progress("Sending email campaign")

            response = self.make_email_request(
                "POST",
                "/campaigns",
                self._build_payload(campaign)
            )

            if options and options.on_progress:
                options.on_progress("Email campaign sent successfully")

            return EmailResponse(**response)
        except Exception as error:
            if options and options.on_progress:
                options.on_progress("Email campaign sending failed")
            raise error

    def send_single(
        self,
        first_name: str,
        last_name: str,
        email: str,
        subject: str,
        message: str,
        text_content: Optional[str] = None,
        sender_email: str = 'noreply@cloudcontactai.com',
        reply_email: str = 'noreply@cloudcontactai.com',
        sender_name: str = 'CloudContactAI',
        title: Optional[str] = None,
        options: Optional[EmailOptions] = None
    ) -> EmailResponse:
        """Send a single email to one recipient"""
        account = EmailAccount(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=""
        )

        campaign = EmailCampaign(
            subject=subject,
            title=title or subject,
            message=message,
            text_content=text_content,
            sender_email=sender_email,
            reply_email=reply_email,
            sender_name=sender_name,
            accounts=[account]
        )

        return self.send_campaign(campaign, options)
