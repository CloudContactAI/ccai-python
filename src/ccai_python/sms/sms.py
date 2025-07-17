"""
sms.py - SMS service for the CCAI API
Handles sending SMS messages through the Cloud Contact AI platform.

:license: MIT
:copyright: 2025 CloudContactAI LLC
"""

from typing import Any, Callable, Dict, List, Optional, Protocol, TypedDict, Union, cast
from pydantic import BaseModel, Field, model_validator


class Account(BaseModel):
    """Account model representing a recipient"""
    first_name: str = Field(..., description="Recipient's first name")
    last_name: str = Field(..., description="Recipient's last name")
    phone: str = Field(..., description="Recipient's phone number in E.164 format")


class SMSCampaign(BaseModel):
    """SMS campaign data model"""
    accounts: List[Account] = Field(..., description="List of recipient accounts")
    message: str = Field(..., description="Message content with optional variables")
    title: str = Field(..., description="Campaign title")


class SMSResponse(BaseModel):
    """Response from the SMS API"""
    id: Optional[str] = Field(None, description="Message ID")
    status: Optional[str] = Field(None, description="Message status")
    campaign_id: Optional[str] = Field(None, description="Campaign ID")
    messages_sent: Optional[int] = Field(None, description="Number of messages sent")
    timestamp: Optional[str] = Field(None, description="Timestamp of the operation")

    @model_validator(mode="before")
    def coerce_id(cls, values):
        if "id" in values and isinstance(values["id"], int):
            values["id"] = str(values["id"])
        return values

    model_config = {
        "extra": "allow",
    }


class SMSOptions(BaseModel):
    """Options for SMS operations"""
    timeout: Optional[int] = Field(None, description="Request timeout in seconds")
    retries: Optional[int] = Field(None, description="Number of retry attempts")
    on_progress: Optional[Callable[[str], None]] = Field(
        None, description="Callback for tracking progress"
    )


class CCAIProtocol(Protocol):
    """Protocol defining the required methods for the CCAI client"""
    @property
    def client_id(self) -> str:
        ...

    def request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        ...


class SMS:
    """SMS service for sending messages through the CCAI API"""

    def __init__(self, ccai: CCAIProtocol) -> None:
        self._ccai = ccai

    def send(
        self,
        accounts: List[Union[Account, Dict[str, str]]],
        message: str,
        title: str,
        options: Optional[SMSOptions] = None
    ) -> SMSResponse:
        if not accounts:
            raise ValueError("At least one account is required")
        if not message:
            raise ValueError("Message is required")
        if not title:
            raise ValueError("Campaign title is required")

        # Convert dict accounts to Account models
        normalized_accounts: List[Account] = []
        for idx, account in enumerate(accounts):
            if isinstance(account, dict):
                try:
                    account_data = {}
                    for key, value in account.items():
                        if key in {"first_name", "firstName"}:
                            account_data["first_name"] = value
                        elif key in {"last_name", "lastName"}:
                            account_data["last_name"] = value
                        else:
                            account_data[key] = value
                    normalized_accounts.append(Account(**account_data))
                except Exception as e:
                    raise ValueError(f"Invalid account at index {idx}: {str(e)}")
            else:
                normalized_accounts.append(account)

        if options and options.on_progress:
            options.on_progress("Preparing to send SMS")

        endpoint = f"/clients/{self._ccai.client_id}/campaigns/direct"
        accounts_data = [
            {
                "firstName": acct.first_name,
                "lastName": acct.last_name,
                "phone": acct.phone
            } for acct in normalized_accounts
        ]

        payload = {
            "accounts": accounts_data,
            "message": message,
            "title": title
        }

        try:
            if options and options.on_progress:
                options.on_progress("Sending SMS")

            timeout = options.timeout if options else None
            response_data = self._ccai.request(
                method="post",
                endpoint=endpoint,
                data=payload,
                timeout=timeout
            )

            if options and options.on_progress:
                options.on_progress("SMS sent successfully")

            return SMSResponse(**response_data)

        except Exception as e:
            if options and options.on_progress:
                options.on_progress("SMS sending failed")
            raise e

    def send_single(
        self,
        first_name: str,
        last_name: str,
        phone: str,
        message: str,
        title: str,
        options: Optional[SMSOptions] = None
    ) -> SMSResponse:
        account = Account(
            first_name=first_name,
            last_name=last_name,
            phone=phone
        )
        return self.send([account], message, title, options)

