"""
Async example using the CCAI Python client with asyncio

:license: MIT
:copyright: 2025 CloudContactAI LLC
"""

import asyncio
from typing import Dict, Any, List

import aiohttp
from pydantic import BaseModel, Field

# Import the synchronous client for type definitions
from ccai_python import Account, SMSResponse, SMSOptions


class AsyncCCAI:
    """
    Async version of the CCAI client for CloudContactAI API
    """
    
    def __init__(
        self, 
        client_id: str, 
        api_key: str, 
        base_url: str = "https://core.cloudcontactai.com/api"
    ) -> None:
        """
        Create a new async CCAI client instance
        
        Args:
            client_id: Client ID for authentication
            api_key: API key for authentication
            base_url: Base URL for the API
        """
        if not client_id:
            raise ValueError("Client ID is required")
        if not api_key:
            raise ValueError("API Key is required")
        
        self._client_id = client_id
        self._api_key = api_key
        self._base_url = base_url
        self.sms = AsyncSMS(self)
    
    @property
    def client_id(self) -> str:
        """Get the client ID"""
        return self._client_id
    
    async def request(
        self, 
        method: str, 
        endpoint: str, 
        data: Dict[str, Any] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Make an authenticated API request to the CCAI API
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request data
            timeout: Request timeout in seconds
            
        Returns:
            API response as a dictionary
        """
        url = f"{self._base_url}{endpoint}"
        
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Accept": "*/*"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=method.upper(),
                url=url,
                headers=headers,
                json=data,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                # Raise an exception for HTTP errors
                response.raise_for_status()
                
                # Parse the response as JSON
                return await response.json()


class AsyncSMS:
    """
    Async SMS service for sending messages through the CCAI API
    """
    
    def __init__(self, ccai: AsyncCCAI) -> None:
        """
        Create a new async SMS service instance
        
        Args:
            ccai: The parent AsyncCCAI instance
        """
        self._ccai = ccai
    
    async def send(
        self,
        accounts: List[Account],
        message: str,
        title: str,
        options: SMSOptions = None
    ) -> SMSResponse:
        """
        Send an SMS message to one or more recipients asynchronously
        
        Args:
            accounts: List of recipient accounts
            message: Message content
            title: Campaign title
            options: Optional settings for the SMS send operation
            
        Returns:
            API response
        """
        # Validate inputs
        if not accounts:
            raise ValueError("At least one account is required")
        if not message:
            raise ValueError("Message is required")
        if not title:
            raise ValueError("Campaign title is required")
        
        # Prepare the endpoint and data
        endpoint = f"/clients/{self._ccai.client_id}/campaigns/direct"
        
        # Convert Account objects to dictionaries with camelCase keys for API compatibility
        accounts_data = [
            {
                "firstName": account.first_name,
                "lastName": account.last_name,
                "phone": account.phone
            }
            for account in accounts
        ]
        
        campaign_data = {
            "accounts": accounts_data,
            "message": message,
            "title": title
        }
        
        # Make the API request
        timeout = options.timeout if options else 30
        response_data = await self._ccai.request(
            method="post", 
            endpoint=endpoint, 
            data=campaign_data,
            timeout=timeout
        )
        
        # Convert response to SMSResponse object
        return SMSResponse(**response_data)
    
    async def send_single(
        self,
        first_name: str,
        last_name: str,
        phone: str,
        message: str,
        title: str,
        options: SMSOptions = None
    ) -> SMSResponse:
        """
        Send a single SMS message to one recipient asynchronously
        
        Args:
            first_name: Recipient's first name
            last_name: Recipient's last name
            phone: Recipient's phone number (E.164 format)
            message: Message content
            title: Campaign title
            options: Optional settings for the SMS send operation
            
        Returns:
            API response
        """
        account = Account(
            first_name=first_name,
            last_name=last_name,
            phone=phone
        )
        
        return await self.send([account], message, title, options)


async def main() -> None:
    """Example of using the async CCAI client"""
    # Create a new async CCAI client
    ccai = AsyncCCAI(
        client_id="YOUR-CLIENT-ID",
        api_key="API-KEY-TOKEN"
    )
    
    # Example recipients
    accounts = [
        Account(
            first_name="John",
            last_name="Doe",
            phone="+15551234567"  # Use E.164 format
        )
    ]
    
    # Message with variable placeholders
    message = "Hello ${first_name} ${last_name}, this is a test message!"
    title = "Async Test Campaign"
    
    try:
        # Send SMS to multiple recipients
        print('Sending campaign to multiple recipients asynchronously...')
        campaign_response = await ccai.sms.send(
            accounts=accounts,
            message=message,
            title=title
        )
        print('SMS campaign sent successfully!')
        print(campaign_response.model_dump())
        
        # Send SMS to a single recipient
        print('\nSending message to a single recipient asynchronously...')
        single_response = await ccai.sms.send_single(
            first_name="Jane",
            last_name="Smith",
            phone="+15559876543",
            message="Hi ${first_name}, thanks for your interest!",
            title="Single Async Message Test"
        )
        print('Single SMS sent successfully!')
        print(single_response.model_dump())
        
        print('\nAll messages sent successfully!')
    except Exception as error:
        print(f'Error sending SMS: {str(error)}')


if __name__ == "__main__":
    asyncio.run(main())
