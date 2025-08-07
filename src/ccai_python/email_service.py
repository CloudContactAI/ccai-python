"""
email_service.py - Email service for the CCAI API
Handles sending email campaigns through the Cloud Contact AI platform.

:license: MIT
:copyright: 2025 CloudContactAI LLC
"""

from typing import Any, Dict, List, Optional, Callable
from pydantic import BaseModel, Field
import requests


class EmailAccount(BaseModel):
    """Account model for email recipients"""
    first_name: str = Field(..., description="Recipient's first name")
    last_name: str = Field(..., description="Recipient's last name")
    email: str = Field(..., description="Recipient's email address")
    phone: str = Field(default="", description="Phone number (required by base Account type)")


class EmailCampaign(BaseModel):
    """Email campaign configuration"""
    subject: str = Field(..., description="Email subject")
    title: str = Field(..., description="Campaign title")
    message: str = Field(..., description="HTML message content")
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
        self.base_url = "https://email-campaigns-test-cloudcontactai.allcode.com/api/v1"
    
    def make_email_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an authenticated API request to the email campaigns API with required headers"""
        url = f"{self.base_url}{endpoint}"
        
        # Print curl command for debugging (matching Node.js behavior)
        curl_cmd = f"curl -X {method.upper()} \"{url}\" \\"
        curl_cmd += f"\n  -H \"Authorization: Bearer {self.ccai.api_key}\" \\"
        curl_cmd += f"\n  -H \"Content-Type: application/json\" \\"
        curl_cmd += f"\n  -H \"Accept: */*\" \\"
        curl_cmd += f"\n  -H \"clientId: {self.ccai.client_id}\" \\"
        curl_cmd += f"\n  -H \"accountId: 1223\""
        if data:
            import json
            curl_cmd += f" \\\n  -d '{json.dumps(data)}'"
        
        print("\n📡 Equivalent curl command:")
        print(curl_cmd)
        print("")
        
        headers = {
            "Authorization": f"Bearer {self.ccai.api_key}",
            "Content-Type": "application/json",
            "Accept": "*/*",
            "clientId": str(self.ccai.client_id),
            "accountId": "1223"
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
                campaign.dict()
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
        sender_email: str,
        reply_email: str,
        sender_name: str,
        title: str,
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
            title=title,
            message=message,
            sender_email=sender_email,
            reply_email=reply_email,
            sender_name=sender_name,
            accounts=[account]
        )
        
        return self.send_campaign(campaign, options)