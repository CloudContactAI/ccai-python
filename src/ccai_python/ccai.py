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
    """
    Main client for interacting with the CloudContactAI API
    """
    
    def __init__(
        self, 
        client_id: str, 
        api_key: str, 
        base_url: Optional[str] = None
    ) -> None:
        """
        Create a new CCAI client instance
        
        Args:
            client_id: Client ID for authentication
            api_key: API key for authentication
            base_url: Optional base URL for the API
        
        Raises:
            ValueError: If client_id or api_key is not provided
        """
        if not client_id:
            raise ValueError("Client ID is required")
        if not api_key:
            raise ValueError("API Key is required")
        
        self._config = CCAIConfig(
            client_id=client_id,
            api_key=api_key,
            base_url=base_url or "https://core.cloudcontactai.com/api"
        )
        
        # Initialize the SMS service
        self.sms = SMS(self)
    
    @property
    def client_id(self) -> str:
        """Get the client ID"""
        return self._config.client_id
    
    @property
    def api_key(self) -> str:
        """Get the API key"""
        return self._config.api_key
    
    @property
    def base_url(self) -> str:
        """Get the base URL"""
        return self._config.base_url
    
    def request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Make an authenticated API request to the CCAI API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            data: Request data
            timeout: Request timeout in seconds
            
        Returns:
            API response as a dictionary
            
        Raises:
            APIError: If the API returns an error
            requests.RequestException: For network-related errors
        """
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
            
            # Raise an exception for HTTP errors
            response.raise_for_status()
            
            return cast(Dict[str, Any], response.json())
        except requests.HTTPError as e:
            # Handle API errors with response
            if e.response is not None:
                try:
                    error_data = e.response.json()
                    error_message = str(error_data)
                except (ValueError, TypeError):
                    error_message = e.response.text or str(e)
                
                raise APIError(e.response.status_code, error_message)
            raise
        except requests.RequestException as e:
            # Handle network errors
            raise APIError(0, f"Network error: {str(e)}")
