"""
mms.py - MMS service for the CCAI API
Handles sending MMS messages through the Cloud Contact AI platform.

:license: MIT
:copyright: 2025 CloudContactAI LLC
"""

import os
import hashlib
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, Union
import requests

from .sms import Account, SMSOptions, SMSResponse


@dataclass
class StoredUrlResponse:
    url: str


class CCAIProtocol(Protocol):
    """Protocol defining the required methods for the CCAI client"""
    @property
    def client_id(self) -> str:
        ...
    
    @property
    def api_key(self) -> str:
        ...
    
    @property
    def base_url(self) -> str:
        ...

    @property
    def file_base_url(self) -> str:
        ...
    
    def request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Union[Dict[str, Any], List[Any]]] = None,
        timeout: int = 30
    ) -> Any:
        ...


class MMS:
    """
    MMS service for sending multimedia messages through the CCAI API
    """
    
    def __init__(self, ccai: CCAIProtocol) -> None:
        """
        Create a new MMS service instance
        
        Args:
            ccai: The parent CCAI instance
        """
        self._ccai = ccai
        self._http_client = requests.Session()
    
    @staticmethod
    def md5(file_path: str) -> str:
        digest = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                digest.update(chunk)
        return digest.hexdigest()
    
    def check_file_uploaded(self, file_key: str) -> StoredUrlResponse:
        try:
            response = self._ccai.request(
                method="GET",
                endpoint=f"/clients/{self._ccai.client_id}/storedUrl?fileKey={file_key}"
            )
            return StoredUrlResponse(url=response.get("storedUrl", ""))
        except Exception as e:
            import traceback
            traceback.print_exc()
            return StoredUrlResponse(url="")
    
    def get_signed_upload_url(
        self,
        file_name: str,
        file_type: str,
        file_base_path: Optional[str] = None,
        public_file: bool = True
    ) -> Dict[str, Any]:
        """
        Get a signed S3 URL to upload an image file
        
        Args:
            file_name: Name of the file to upload
            file_type: MIME type of the file
            file_base_path: Base path for the file in S3 (default: clientId/campaign)
            public_file: Whether the file should be public (default: True)
            
        Returns:
            Response containing the signed URL and file key
            
        Raises:
            ValueError: If required parameters are missing or invalid
            RuntimeError: If the API request fails
        """
        if not file_name:
            raise ValueError("File name is required")
        
        if not file_type:
            raise ValueError("File type is required")
        
        # Use default file_base_path if not provided
        file_base_path = file_base_path or f"{self._ccai.client_id}/campaign"
        
        # Define file_key explicitly as clientId/campaign/filename
        file_key = f"{self._ccai.client_id}/campaign/{file_name}"
        
        data = {
            "fileName": file_name,
            "fileType": file_type,
            "fileBasePath": file_base_path,
            "publicFile": public_file
        }
        
        try:
            response = self._http_client.post(
                f"{self._ccai.file_base_url}/upload/url",
                headers={
                    "Authorization": f"Bearer {self._ccai.api_key}",
                    "Content-Type": "application/json"
                },
                json=data
            )
            
            response.raise_for_status()
            response_data = response.json()
            
            if "signedS3Url" not in response_data:
                raise RuntimeError("Invalid response from upload URL API")
            
            # Override the fileKey with our explicitly defined one
            response_data["fileKey"] = file_key
            
            return response_data
        except Exception as e:
            raise RuntimeError(f"Failed to get signed upload URL: {str(e)}")
    
    def upload_image_to_signed_url(
        self,
        signed_url: str,
        file_path: str,
        content_type: str
    ) -> bool:
        """
        Upload an image file to a signed S3 URL
        
        Args:
            signed_url: The signed S3 URL to upload to
            file_path: Path to the file to upload
            content_type: MIME type of the file
            
        Returns:
            True if upload was successful
            
        Raises:
            ValueError: If required parameters are missing or invalid
            RuntimeError: If the file upload fails
        """
        if not signed_url:
            raise ValueError("Signed URL is required")
        
        if not file_path:
            raise ValueError("File path is required")
        
        if not os.path.exists(file_path):
            raise ValueError(f"File does not exist: {file_path}")
        
        if not content_type:
            raise ValueError("Content type is required")
        
        try:
            with open(file_path, "rb") as file:
                file_contents = file.read()
            
            response = self._http_client.put(
                signed_url,
                headers={"Content-Type": content_type},
                data=file_contents
            )
            
            return 200 <= response.status_code < 300
        except Exception as e:
            raise RuntimeError(f"Failed to upload file: {str(e)}")
    
    def send(
        self,
        picture_file_key: str,
        accounts: List[Union[Account, Dict[str, str]]],
        message: str,
        title: str,
        sender_phone: Optional[str] = None,
        options: Optional[SMSOptions] = None,
        force_new_campaign: bool = True
    ) -> SMSResponse:
        """
        Send an MMS message to one or more recipients
        
        Args:
            picture_file_key: S3 file key for the image
            accounts: List of recipient accounts
            message: Message content (can include ${first_name} and ${last_name} variables)
            title: Campaign title
            options: Optional settings for the MMS send operation
            force_new_campaign: Whether to force a new campaign (default: True)
            
        Returns:
            API response
            
        Raises:
            ValueError: If required parameters are missing or invalid
        """
        # Validate inputs
        if not picture_file_key:
            raise ValueError("Picture file key is required")
        
        if not accounts:
            raise ValueError("At least one account is required")
        
        if not message:
            raise ValueError("Message is required")
        
        if not title:
            raise ValueError("Campaign title is required")
        
        # Create options if not provided
        options = options or SMSOptions()
        
        # Convert dict accounts to Account objects if needed
        normalized_accounts: List[Account] = []
        for idx, account in enumerate(accounts):
            if isinstance(account, dict):
                try:
                    # Convert dictionary keys from snake_case to camelCase if needed
                    account_data = {}
                    for key, value in account.items():
                        if key == "first_name":
                            account_data["first_name"] = value
                        elif key == "lastName":
                            account_data["last_name"] = value
                        elif key == "firstName":
                            account_data["first_name"] = value
                        elif key == "last_name":
                            account_data["last_name"] = value
                        else:
                            account_data[key] = value
                    
                    normalized_accounts.append(Account(**account_data))
                except Exception as e:
                    raise ValueError(f"Invalid account at index {idx}: {str(e)}")
            else:
                normalized_accounts.append(account)
        
        # Notify progress if callback provided
        if options.on_progress:
            options.on_progress("Preparing to send MMS")
        
        # Prepare the endpoint and data
        endpoint = f"/clients/{self._ccai.client_id}/campaigns/direct"
        
        # Convert Account objects to dictionaries with camelCase keys for API compatibility
        accounts_data = []
        for account in normalized_accounts:
            acc: Dict[str, Any] = {
                "firstName": account.first_name,
                "lastName": account.last_name,
                "phone": account.phone,
            }
            if account.data:
                acc["data"] = account.data
            if account.message_data:
                acc["messageData"] = account.message_data
            accounts_data.append(acc)
        
        campaign_data = {
            "pictureFileKey": picture_file_key,
            "accounts": accounts_data,
            "message": message,
            "title": title
        }
        if sender_phone:
            campaign_data["senderPhone"] = sender_phone
        
        try:
            # Notify progress if callback provided
            if options.on_progress:
                options.on_progress("Sending MMS")
            
            # Set up headers
            headers = {
                "Authorization": f"Bearer {self._ccai.api_key}",
                "Content-Type": "application/json"
            }
            
            if force_new_campaign:
                headers["ForceNewCampaign"] = "true"
            
            # Make the API request
            response = self._http_client.post(
                f"{self._ccai.base_url}{endpoint}",
                headers=headers,
                json=campaign_data,
                timeout=options.timeout or 30
            )
            
            response.raise_for_status()
            response_data = response.json()
            
            # Notify progress if callback provided
            if options.on_progress:
                options.on_progress("MMS sent successfully")
            
            # Convert response to SMSResponse object
            return SMSResponse(**response_data)
        except Exception as e:
            # Notify progress if callback provided
            if options.on_progress:
                options.on_progress("MMS sending failed")
            
            raise RuntimeError(f"Failed to send MMS: {str(e)}")
    
    def send_single(
        self,
        picture_file_key: str,
        first_name: str,
        last_name: str,
        phone: str,
        message: str,
        title: str,
        custom_data: Optional[str] = None,
        sender_phone: Optional[str] = None,
        options: Optional[SMSOptions] = None,
        force_new_campaign: bool = True
    ) -> SMSResponse:
        """
        Send a single MMS message to one recipient
        
        Args:
            picture_file_key: S3 file key for the image
            first_name: Recipient's first name
            last_name: Recipient's last name
            phone: Recipient's phone number (E.164 format)
            message: Message content (can include ${first_name} and ${last_name} variables)
            title: Campaign title
            custom_data: Optional arbitrary string forwarded to your webhook handler (sent as messageData)
            sender_phone: Optional sender phone number
            options: Optional settings for the MMS send operation
            force_new_campaign: Whether to force a new campaign (default: True)
            
        Returns:
            API response
        """
        account = Account(
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            message_data=custom_data
        )
        
        return self.send(
            picture_file_key=picture_file_key,
            accounts=[account],
            message=message,
            title=title,
            sender_phone=sender_phone,
            options=options,
            force_new_campaign=force_new_campaign
        )
    
    def send_with_image(
        self,
        image_path: str,
        content_type: str,
        accounts: List[Union[Account, Dict[str, str]]],
        message: str,
        title: str,
        sender_phone: Optional[str] = None,
        options: Optional[SMSOptions] = None,
        force_new_campaign: bool = True
    ) -> SMSResponse:
        """
        Complete MMS workflow: get signed URL, upload image, and send MMS
        
        Args:
            image_path: Path to the image file
            content_type: MIME type of the image
            accounts: List of recipient accounts
            message: Message content (can include ${first_name} and ${last_name} variables)
            title: Campaign title
            options: Optional settings for the MMS send operation
            force_new_campaign: Whether to force a new campaign (default: True)
            
        Returns:
            API response
            
        Raises:
            ValueError: If required parameters are missing or invalid
            RuntimeError: If any step of the process fails
        """
        # Create options if not provided
        options = options or SMSOptions()

        # Step 1: Get the file name, extension and md5 from the path
        md5_image = self.md5(image_path)
        file_name = os.path.basename(image_path)
        file_extension = os.path.splitext(file_name)[1]
        md5_name = f"{md5_image}{file_extension}"

        # Check if the same image has already been uploaded
        file_key = f"{self._ccai.client_id}/campaign/{md5_name}"
        stored_url_response = self.check_file_uploaded(file_key)

        if stored_url_response.url:
            return self.send(
                picture_file_key=file_key,
                accounts=accounts,
                message=message,
                title=title,
                sender_phone=sender_phone,
                options=options,
                force_new_campaign=force_new_campaign
            )
        
        # Notify progress if callback provided
        if options.on_progress:
            options.on_progress("Getting signed upload URL")
        
        # Step 2: Get a signed URL for uploading
        upload_response = self.get_signed_upload_url(md5_name, content_type)
        signed_url = upload_response["signedS3Url"]
        file_key = upload_response["fileKey"]
        
        # Notify progress if callback provided
        if options.on_progress:
            options.on_progress("Uploading image to S3")
        
        # Step 3: Upload the image to the signed URL
        upload_success = self.upload_image_to_signed_url(signed_url, image_path, content_type)
        
        if not upload_success:
            raise RuntimeError("Failed to upload image to S3")
        
        # Notify progress if callback provided
        if options.on_progress:
            options.on_progress("Image uploaded successfully, sending MMS")
        
        # Step 4: Send the MMS with the uploaded image
        return self.send(
            picture_file_key=file_key,
            accounts=accounts,
            message=message,
            title=title,
            sender_phone=sender_phone,
            options=options,
            force_new_campaign=force_new_campaign
        )
