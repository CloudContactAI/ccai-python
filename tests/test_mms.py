"""
Tests for the MMS service

:license: MIT
:copyright: 2025 CloudContactAI LLC
"""

import hashlib
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock, mock_open

from ccai_python import CCAI, Account, SMSOptions, SMSResponse
from ccai_python.sms.mms import StoredUrlResponse


class TestMMS(unittest.TestCase):
    """Test cases for the MMS service"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client_id = "test-client-id"
        self.api_key = "test-api-key"
        self.ccai = CCAI(client_id=self.client_id, api_key=self.api_key)
        
        # Sample account
        self.account = Account(
            first_name="John",
            last_name="Doe",
            phone="+15551234567"
        )
        
        # Sample message and title
        self.message = "Hello ${first_name}, this is a test MMS message!"
        self.title = "Test MMS Campaign"
        
        # Sample file data
        self.file_name = "test_image.jpg"
        self.file_path = f"/path/to/{self.file_name}"
        self.content_type = "image/jpeg"
        self.picture_file_key = f"{self.client_id}/campaign/{self.file_name}"
    
    @patch('requests.Session.post')
    def test_get_signed_upload_url(self, mock_post):
        """Test getting a signed upload URL"""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "signedS3Url": "https://s3.amazonaws.com/bucket/signed-url",
            "fileKey": "original/file/key"
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Get signed upload URL
        response = self.ccai.mms.get_signed_upload_url(
            file_name=self.file_name,
            file_type=self.content_type
        )
        
        # Verify response
        self.assertEqual(response["signedS3Url"], "https://s3.amazonaws.com/bucket/signed-url")
        self.assertEqual(response["fileKey"], f"{self.client_id}/campaign/{self.file_name}")
        
        # Verify request was made correctly
        mock_post.assert_called_with(
            "https://files.cloudcontactai.com/upload/url",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "fileName": self.file_name,
                "fileType": self.content_type,
                "fileBasePath": f"{self.client_id}/campaign",
                "publicFile": True
            }
        )
    
    @patch('requests.Session.put')
    @patch('os.path.exists')
    def test_upload_image_to_signed_url(self, mock_exists, mock_put):
        """Test uploading an image to a signed URL"""
        # Mock file exists
        mock_exists.return_value = True
        
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_put.return_value = mock_response
        
        # Mock file open
        mock_file_data = b"test image data"
        with patch("builtins.open", mock_open(read_data=mock_file_data)):
            # Upload image
            result = self.ccai.mms.upload_image_to_signed_url(
                signed_url="https://s3.amazonaws.com/bucket/signed-url",
                file_path=self.file_path,
                content_type=self.content_type
            )
        
        # Verify result
        self.assertTrue(result)
        
        # Verify request was made correctly
        mock_put.assert_called_with(
            "https://s3.amazonaws.com/bucket/signed-url",
            headers={"Content-Type": self.content_type},
            data=mock_file_data
        )
    
    @patch('requests.Session.post')
    def test_send(self, mock_post):
        """Test sending MMS to multiple recipients"""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "msg-123",
            "status": "sent",
            "campaign_id": "camp-456",
            "messages_sent": 1,
            "timestamp": "2025-06-06T12:00:00Z"
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Send MMS
        response = self.ccai.mms.send(
            picture_file_key=self.picture_file_key,
            accounts=[self.account],
            message=self.message,
            title=self.title
        )
        
        # Verify response
        self.assertEqual(response.id, "msg-123")
        self.assertEqual(response.status, "sent")
        self.assertEqual(response.campaign_id, "camp-456")
        self.assertEqual(response.messages_sent, 1)
        self.assertEqual(response.timestamp, "2025-06-06T12:00:00Z")
        
        # Verify request was made correctly
        mock_post.assert_called_with(
            f"{self.ccai.base_url}/clients/{self.client_id}/campaigns/direct",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "ForceNewCampaign": "true"
            },
            json={
                "pictureFileKey": self.picture_file_key,
                "accounts": [
                    {
                        "firstName": "John",
                        "lastName": "Doe",
                        "phone": "+15551234567"
                    }
                ],
                "message": self.message,
                "title": self.title
            },
            timeout=30
        )
    
    @patch('requests.Session.post')
    def test_send_with_dict_accounts(self, mock_post):
        """Test sending MMS with dictionary accounts"""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "msg-123", "status": "sent"}
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Send MMS with dictionary accounts
        response = self.ccai.mms.send(
            picture_file_key=self.picture_file_key,
            accounts=[{
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+15551234567"
            }],
            message=self.message,
            title=self.title
        )
        
        # Verify response
        self.assertEqual(response.id, "msg-123")
        self.assertEqual(response.status, "sent")
        
        # Verify request was made correctly
        mock_post.assert_called_with(
            f"{self.ccai.base_url}/clients/{self.client_id}/campaigns/direct",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "ForceNewCampaign": "true"
            },
            json={
                "pictureFileKey": self.picture_file_key,
                "accounts": [
                    {
                        "firstName": "John",
                        "lastName": "Doe",
                        "phone": "+15551234567"
                    }
                ],
                "message": self.message,
                "title": self.title
            },
            timeout=30
        )
    
    @patch('requests.Session.post')
    def test_send_single(self, mock_post):
        """Test sending MMS to a single recipient"""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "msg-123", "status": "sent"}
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Send MMS to a single recipient
        response = self.ccai.mms.send_single(
            picture_file_key=self.picture_file_key,
            first_name="Jane",
            last_name="Smith",
            phone="+15559876543",
            message="Hi ${first_name}, thanks for your interest!",
            title="Single MMS Test"
        )
        
        # Verify response
        self.assertEqual(response.id, "msg-123")
        self.assertEqual(response.status, "sent")
        
        # Verify request was made correctly
        mock_post.assert_called_with(
            f"{self.ccai.base_url}/clients/{self.client_id}/campaigns/direct",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "ForceNewCampaign": "true"
            },
            json={
                "pictureFileKey": self.picture_file_key,
                "accounts": [
                    {
                        "firstName": "Jane",
                        "lastName": "Smith",
                        "phone": "+15559876543"
                    }
                ],
                "message": "Hi ${first_name}, thanks for your interest!",
                "title": "Single MMS Test"
            },
            timeout=30
        )
    
    @patch('requests.Session.post')
    def test_send_with_options(self, mock_post):
        """Test sending MMS with options"""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "msg-123", "status": "sent"}
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Create progress tracking callback
        progress_updates = []
        def track_progress(status: str):
            progress_updates.append(status)
        
        # Create options
        options = SMSOptions(
            timeout=60,
            retries=3,
            on_progress=track_progress
        )
        
        # Send MMS with options
        response = self.ccai.mms.send(
            picture_file_key=self.picture_file_key,
            accounts=[self.account],
            message=self.message,
            title=self.title,
            options=options
        )
        
        # Verify response
        self.assertEqual(response.id, "msg-123")
        self.assertEqual(response.status, "sent")
        
        # Verify progress updates
        self.assertEqual(progress_updates, [
            "Preparing to send MMS",
            "Sending MMS",
            "MMS sent successfully"
        ])
        
        # Verify request was made correctly
        mock_post.assert_called_with(
            f"{self.ccai.base_url}/clients/{self.client_id}/campaigns/direct",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "ForceNewCampaign": "true"
            },
            json={
                "pictureFileKey": self.picture_file_key,
                "accounts": [
                    {
                        "firstName": "John",
                        "lastName": "Doe",
                        "phone": "+15551234567"
                    }
                ],
                "message": self.message,
                "title": self.title
            },
            timeout=60
        )
    
    @patch('requests.Session.post')
    @patch('requests.Session.put')
    @patch('os.path.exists')
    def test_send_with_image(self, mock_exists, mock_put, mock_post):
        """Test complete MMS workflow: get URL, upload image, send MMS"""
        # Mock file exists
        mock_exists.return_value = True

        # Mock md5 and check_file_uploaded
        fake_md5 = "abc123def456"
        md5_name = f"{fake_md5}.jpg"
        self.ccai.mms.md5 = MagicMock(return_value=fake_md5)
        self.ccai.mms.check_file_uploaded = MagicMock(return_value=StoredUrlResponse(url=""))
        
        # Mock upload URL response
        upload_url_response = MagicMock()
        upload_url_response.json.return_value = {
            "signedS3Url": "https://s3.amazonaws.com/bucket/signed-url",
            "fileKey": "original/file/key"
        }
        upload_url_response.status_code = 200
        
        # Mock upload response
        upload_response = MagicMock()
        upload_response.status_code = 200
        
        # Mock send response
        send_response = MagicMock()
        send_response.json.return_value = {"id": "msg-123", "status": "sent"}
        send_response.status_code = 200
        
        # Configure mock to return different responses for different calls
        mock_post.side_effect = [upload_url_response, send_response]
        mock_put.return_value = upload_response
        
        # Mock file open
        mock_file_data = b"test image data"
        with patch("builtins.open", mock_open(read_data=mock_file_data)):
            # Send MMS with image
            response = self.ccai.mms.send_with_image(
                image_path=self.file_path,
                content_type=self.content_type,
                accounts=[self.account],
                message=self.message,
                title=self.title
            )
        
        # Verify response
        self.assertEqual(response.id, "msg-123")
        self.assertEqual(response.status, "sent")
        
        # Verify md5 was called with image_path
        self.ccai.mms.md5.assert_called_once_with(self.file_path)
        
        # Verify check_file_uploaded was called
        self.ccai.mms.check_file_uploaded.assert_called_once_with(
            f"{self.client_id}/campaign/{md5_name}"
        )
        
        # Verify upload URL request used md5_name
        mock_post.assert_any_call(
            "https://files.cloudcontactai.com/upload/url",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "fileName": md5_name,
                "fileType": self.content_type,
                "fileBasePath": f"{self.client_id}/campaign",
                "publicFile": True
            }
        )
        
        # Verify upload request
        mock_put.assert_called_with(
            "https://s3.amazonaws.com/bucket/signed-url",
            headers={"Content-Type": self.content_type},
            data=mock_file_data
        )
    
    def test_validation(self):
        """Test input validation"""
        # Test empty picture_file_key
        with self.assertRaises(ValueError):
            self.ccai.mms.send(
                picture_file_key="",
                accounts=[self.account],
                message=self.message,
                title=self.title
            )
        
        # Test empty accounts
        with self.assertRaises(ValueError):
            self.ccai.mms.send(
                picture_file_key=self.picture_file_key,
                accounts=[],
                message=self.message,
                title=self.title
            )
        
        # Test empty message
        with self.assertRaises(ValueError):
            self.ccai.mms.send(
                picture_file_key=self.picture_file_key,
                accounts=[self.account],
                message="",
                title=self.title
            )
        
        # Test empty title
        with self.assertRaises(ValueError):
            self.ccai.mms.send(
                picture_file_key=self.picture_file_key,
                accounts=[self.account],
                message=self.message,
                title=""
            )
        
        # Test get_signed_upload_url validation
        with self.assertRaises(ValueError):
            self.ccai.mms.get_signed_upload_url(
                file_name="",
                file_type=self.content_type
            )
        
        with self.assertRaises(ValueError):
            self.ccai.mms.get_signed_upload_url(
                file_name=self.file_name,
                file_type=""
            )
        
        # Test upload_image_to_signed_url validation
        with self.assertRaises(ValueError):
            self.ccai.mms.upload_image_to_signed_url(
                signed_url="",
                file_path=self.file_path,
                content_type=self.content_type
            )
        
        with self.assertRaises(ValueError):
            self.ccai.mms.upload_image_to_signed_url(
                signed_url="https://example.com",
                file_path="",
                content_type=self.content_type
            )
        
        with self.assertRaises(ValueError):
            self.ccai.mms.upload_image_to_signed_url(
                signed_url="https://example.com",
                file_path=self.file_path,
                content_type=""
            )


    def test_md5(self):
        """Test MD5 hash calculation of a file"""
        content = b"test image content for md5"
        expected = hashlib.md5(content).hexdigest()

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            result = self.ccai.mms.md5(tmp_path)
            self.assertEqual(result, expected)
        finally:
            os.unlink(tmp_path)

    def test_md5_empty_file(self):
        """Test MD5 hash of an empty file"""
        expected = hashlib.md5(b"").hexdigest()

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name

        try:
            result = self.ccai.mms.md5(tmp_path)
            self.assertEqual(result, expected)
        finally:
            os.unlink(tmp_path)

    def test_check_file_uploaded_found(self):
        """Test check_file_uploaded when file exists"""
        self.ccai.request = MagicMock(return_value={"storedUrl": "https://s3.amazonaws.com/bucket/file.jpg"})

        result = self.ccai.mms.check_file_uploaded("test-client-id/campaign/image.jpg")

        self.assertIsInstance(result, StoredUrlResponse)
        self.assertEqual(result.url, "https://s3.amazonaws.com/bucket/file.jpg")

    def test_check_file_uploaded_not_found(self):
        """Test check_file_uploaded when file does not exist"""
        self.ccai.request = MagicMock(side_effect=Exception("Not found"))

        result = self.ccai.mms.check_file_uploaded("test-client-id/campaign/missing.jpg")

        self.assertIsInstance(result, StoredUrlResponse)
        self.assertEqual(result.url, "")


if __name__ == '__main__':
    unittest.main()
