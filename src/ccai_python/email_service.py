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
    add_to_list: str = Field(default="noList", description="List management option")
    contact_input: str = Field(default="accounts", description="Contact input type")
    from_type: str = Field(default="single", description="From type")
    senders: List[Any] = Field(default_factory=list, description="Senders list")


class EmailResponse(BaseModel):
    """Response from email API"""
    id: Optional[str] = Field(default=None, description="Message ID")
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
        self.base_url = "https://email-campaigns.cloudcontactai.com/api/v1"
    
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
            
            response = self.ccai.custom_request(
                "POST",
                "/campaigns",
                campaign.dict(),
                self.base_url
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