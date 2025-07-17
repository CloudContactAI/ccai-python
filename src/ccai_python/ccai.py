"""
ccai.py - A Python module for interacting with the Cloud Contact AI API
This module provides functionality to send SMS messages through the CCAI platform.

:license: MIT
:copyright: 2025 CloudContactAI LLC
"""

from typing import Any, Dict, Optional, TypedDict, cast
import requests
from pydantic import BaseModel, Field

from .sms.sms import SMS
from .sms.mms import MMS


class Account(BaseModel):
    """Account model representing a recipient"""
    first_name: str = Field(..., description="Recipient's first name")
    last_name: str = Field(..., description="Recipient's last name")
    phone: str = Field(..., description="Recipient's phone number in E.164 format")


class CCAIConfig(BaseModel):
    """Configuration for the CCAI client"""
    client_id: str = Field(..., description="Client ID for authentication")
    api_key: str = Field(..., description="API key for authentication")
    base_url: str = Field(
        default="https://core.cloudcontactai.com/api",
        description="Base URL for the API"
    )


class APIError(Exception):
    """Exception raised for API errors"""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"API Error: {status_code} - {message}")


class CCAI:
    """Main client for interacting with the CloudContactAI API"""

    def __init__(
        self,
        client_id: str,
        api_key: str,
        base_url: Optional[str] = None
    ) -> None:
        if not client_id:
            raise ValueError("Client ID is required")
        if not api_key:
            raise ValueError("API Key is required")

        self._config = CCAIConfig(
            client_id=client_id,
            api_key=api_key,
            base_url=base_url or "https://core.cloudcontactai.com/api"
        )

        self.sms = SMS(self)
        self.mms = MMS(self)

    @property
    def client_id(self) -> str:
        return self._config.client_id

    @property
    def api_key(self) -> str:
        return self._config.api_key

    @property
    def base_url(self) -> str:
        return self._config.base_url

    def request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "*/*"
        }

        try:
            response = requests.request(
                method=method.upper(),
                url=url,
                headers=headers,
                json=data,
                timeout=timeout
            )
            response.raise_for_status()
            return cast(Dict[str, Any], response.json())
        except requests.HTTPError as e:
            if e.response is not None:
                try:
                    error_data = e.response.json()
                    error_message = str(error_data)
                except (ValueError, TypeError):
                    error_message = e.response.text or str(e)
                raise APIError(e.response.status_code, error_message)
            raise
        except requests.RequestException as e:
            raise APIError(0, f"Network error: {str(e)}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="CCAI CLI - Send SMS via CloudContactAI")
    parser.add_argument("--client_id", required=True, help="Your CloudContactAI client ID")
    parser.add_argument("--api_key", required=True, help="Your CloudContactAI API key")
    parser.add_argument("--phone", required=True, help="Recipient's phone number in E.164 format")
    parser.add_argument("--first_name", default="John", help="Recipient's first name")
    parser.add_argument("--last_name", default="Doe", help="Recipient's last name")
    parser.add_argument("--message", required=True, help="The message to send")

    args = parser.parse_args()

    ccai = CCAI(client_id=args.client_id, api_key=args.api_key)

    account = Account(
        first_name=args.first_name,
        last_name=args.last_name,
        phone=args.phone
    )

    response = ccai.sms.send(account=account, message=args.message)

    print("✅ SMS Sent!")
    print("📨 Response:", response)


if __name__ == "__main__":
    main()
