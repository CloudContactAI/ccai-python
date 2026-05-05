"""
ccai.py - A Python module for interacting with the Cloud Contact AI API
This module provides functionality to send SMS messages through the CCAI platform.

:license: MIT
:copyright: 2025 CloudContactAI LLC
"""

from typing import Any, Dict, List, Optional, Union, cast
import os
import requests
from pydantic import BaseModel, Field

from .sms.sms import SMS, Account
from .sms.mms import MMS
from .email_service import Email
from .webhook import Webhook
from .contact_service import Contact
from .brand_service import Brand
from .campaign_service import Campaign as CampaignService


class CCAIConfig(BaseModel):
    """Configuration for the CCAI client"""
    client_id: str = Field(..., description="Client ID for authentication")
    api_key: str = Field(..., description="API key for authentication")
    base_url: str = Field(
        default="https://core.cloudcontactai.com/api",
        description="Base URL for the API"
    )
    email_base_url: str = Field(
        default="https://email-campaigns.cloudcontactai.com/api/v1",
        description="Base URL for the Email API"
    )
    file_base_url: str = Field(
        default="https://files.cloudcontactai.com",
        description="Base URL for File processor API"
    )
    use_test: bool = Field(
        default=False,
        description="Whether to use test environment URLs"
    )


class APIError(Exception):
    """Exception raised for API errors"""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"API Error: {status_code} - {message}")


class CCAI:
    """Main client for interacting with the CloudContactAI API"""

    # Production URLs
    PROD_BASE_URL = "https://core.cloudcontactai.com/api"
    PROD_EMAIL_URL = "https://email-campaigns.cloudcontactai.com/api/v1"
    PROD_FILES_URL = "https://files.cloudcontactai.com"
    PROD_COMPLIANCE_URL = "https://compliance.cloudcontactai.com/api"

    # Test environment URLs
    TEST_BASE_URL = "https://core-test-cloudcontactai.allcode.com/api"
    TEST_EMAIL_URL = "https://email-campaigns-test-cloudcontactai.allcode.com/api/v1"
    TEST_FILES_URL = "https://files-test-cloudcontactai.allcode.com"
    TEST_COMPLIANCE_URL = "https://compliance-test-cloudcontactai.allcode.com/api"

    def __init__(
        self,
        client_id: str,
        api_key: str,
        base_url: Optional[str] = None,
        email_base_url: Optional[str] = None,
        file_base_url: Optional[str] = None,
        compliance_base_url: Optional[str] = None,
        use_test: bool = False
    ) -> None:
        if not client_id:
            raise ValueError("Client ID is required")
        if not api_key:
            raise ValueError("API Key is required")

        # Resolve URLs: explicit override > env var > test/prod default
        resolved_base = self._resolve_url(
            base_url, "CCAI_BASE_URL", self.PROD_BASE_URL, self.TEST_BASE_URL, use_test
        )
        resolved_email = self._resolve_url(
            email_base_url, "CCAI_EMAIL_BASE_URL", self.PROD_EMAIL_URL, self.TEST_EMAIL_URL, use_test
        )
        resolved_files = self._resolve_url(
            file_base_url, "CCAI_FILES_BASE_URL", self.PROD_FILES_URL, self.TEST_FILES_URL, use_test
        )
        self._compliance_base_url = self._resolve_url(
            compliance_base_url, "CCAI_COMPLIANCE_BASE_URL", self.PROD_COMPLIANCE_URL, self.TEST_COMPLIANCE_URL, use_test
        )

        self._config = CCAIConfig(
            client_id=client_id,
            api_key=api_key,
            base_url=resolved_base,
            email_base_url=resolved_email,
            file_base_url=resolved_files,
            use_test=use_test
        )

        self.sms = SMS(self)
        self.mms = MMS(self)
        self.email = Email(self)
        self.webhook = Webhook(self)
        self.contact = Contact(self)
        self.brands = Brand(self)
        self.campaigns = CampaignService(self)

    def _resolve_url(
        self,
        explicit: Optional[str],
        env_var: str,
        prod_default: str,
        test_default: str,
        use_test: bool
    ) -> str:
        """Resolve URL with priority: explicit > env > prod/test default"""
        if explicit:
            return explicit
        env_val = os.environ.get(env_var)
        if env_val:
            return env_val
        return test_default if use_test else prod_default

    @property
    def client_id(self) -> str:
        return self._config.client_id

    @property
    def api_key(self) -> str:
        return self._config.api_key

    @property
    def base_url(self) -> str:
        return self._config.base_url

    @property
    def email_base_url(self) -> str:
        return self._config.email_base_url

    @property
    def file_base_url(self) -> str:
        return self._config.file_base_url

    @property
    def compliance_base_url(self) -> str:
        return self._compliance_base_url

    @property
    def use_test(self) -> bool:
        return self._config.use_test

    def request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Union[Dict[str, Any], List[Any]]] = None,
        timeout: int = 30
    ) -> Any:
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
            if response.status_code == 204:
                return cast(Dict[str, Any], {})
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

    def custom_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        base_url: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """Make a custom request to a different base URL"""
        url = f"{base_url or self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "*/*"
        }
        if extra_headers:
            headers.update(extra_headers)

        try:
            response = requests.request(
                method=method.upper(),
                url=url,
                headers=headers,
                json=data,
                timeout=timeout
            )
            response.raise_for_status()
            if response.status_code == 204:
                return cast(Dict[str, Any], {})
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
    parser.add_argument("--title", default="CLI Campaign", help="Campaign title")

    args = parser.parse_args()

    ccai = CCAI(client_id=args.client_id, api_key=args.api_key)

    from ccai_python.sms.sms import Account as SMSAccount
    account = SMSAccount(
        first_name=args.first_name,
        last_name=args.last_name,
        phone=args.phone
    )

    response = ccai.sms.send(accounts=[account], message=args.message, title=args.title)

    print("✅ SMS Sent!")
    print("📨 Response:", response)


if __name__ == "__main__":
    main()
