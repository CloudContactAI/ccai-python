"""
Tests for the SMS service

:license: MIT
:copyright: 2025 CloudContactAI LLC
"""

import unittest
from unittest.mock import patch, MagicMock

from ccai_python import CCAI, Account, SMSOptions



class TestSMS(unittest.TestCase):
    """Test cases for the SMS service"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client_id = "2682"
        self.api_key = "eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJpbmZvQGFsbGNvZGUuY29tIiwiaXNzIjoiY2xvdWRjb250YWN0IiwibmJmIjoxNzE5NDQwMjM2LCJpYXQiOjE3MTk0NDAyMzYsInJvbGUiOiJVU0VSIiwiY2xpZW50SWQiOjI2ODIsImlkIjoyNzY0LCJ0eXBlIjoiQVBJX0tFWSIsImtleV9yYW5kb21faWQiOiI1MGRiOTUzZC1hMjUxLTRmZjMtODI5Yi01NjIyOGRhOGE1YTAifQ.PKVjXYHdjBMum9cTgLzFeY2KIb9b2tjawJ0WXalsb8Bckw1RuxeiYKS1bw5Cc36_Rfmivze0T7r-Zy0PVj2omDLq65io0zkBzIEJRNGDn3gx_AqmBrJ3yGnz9s0WTMr2-F1TFPUByzbj1eSOASIKeI7DGufTA5LDrRclVkz32Oo"
        self.ccai = CCAI(client_id=self.client_id, api_key=self.api_key)
        
        # Sample account
        self.account = Account(
            first_name="John",
            last_name="Doe",
            phone="+14156961732"
        )
        
        # Sample message and title
        self.message = "Hello ${first_name}, this is a test message!"
        self.title = "Test Campaign"
    
    @patch.object(CCAI, 'request')
    def test_send(self, mock_request):
        """Test sending SMS to multiple recipients"""
        # Mock response
        mock_request.return_value = {
            "id": "msg-123",
            "status": "sent",
            "campaign_id": "camp-456",
            "messages_sent": 1,
            "timestamp": "2025-06-06T12:00:00Z"
        }
        
        # Send SMS
        response = self.ccai.sms.send(
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
        mock_request.assert_called_with(
            method="post",
            endpoint=f"/clients/{self.client_id}/campaigns/direct",
            data={
                "accounts": [
                    {
                        "firstName": "John",
                        "lastName": "Doe",
                        "phone": "+14156961732"
                    }
                ],
                "message": self.message,
                "title": self.title
            },
            timeout=None
        )
    
    @patch.object(CCAI, 'request')
    def test_send_with_dict_accounts(self, mock_request):
        """Test sending SMS with dictionary accounts"""
        # Mock response
        mock_request.return_value = {"id": "msg-123", "status": "sent"}
        
        # Send SMS with dictionary accounts
        response = self.ccai.sms.send(
            accounts=[{
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+14156961732"
            }],
            message=self.message,
            title=self.title
        )
        
        # Verify response
        self.assertEqual(response.id, "msg-123")
        self.assertEqual(response.status, "sent")
        
        # Verify request was made correctly
        mock_request.assert_called_with(
            method="post",
            endpoint=f"/clients/{self.client_id}/campaigns/direct",
            data={
                "accounts": [
                    {
                        "firstName": "John",
                        "lastName": "Doe",
                        "phone": "+14156961732"
                    }
                ],
                "message": self.message,
                "title": self.title
            },
            timeout=None
        )
    
    @patch.object(CCAI, 'request')
    def test_send_single(self, mock_request):
        """Test sending SMS to a single recipient"""
        # Mock response
        mock_request.return_value = {"id": "msg-123", "status": "sent"}
        
        # Send SMS to a single recipient
        response = self.ccai.sms.send_single(
            first_name="Jane",
            last_name="Smith",
            phone="+14156961732",
            message="Hi ${first_name}, thanks for your interest!",
            title="Single Message Test"
        )
        
        # Verify response
        self.assertEqual(response.id, "msg-123")
        self.assertEqual(response.status, "sent")
        
        # Verify request was made correctly
        mock_request.assert_called_with(
            method="post",
            endpoint=f"/clients/{self.client_id}/campaigns/direct",
            data={
                "accounts": [
                    {
                        "firstName": "Jane",
                        "lastName": "Smith",
                        "phone": "+14156961732"
                    }
                ],
                "message": "Hi ${first_name}, thanks for your interest!",
                "title": "Single Message Test"
            },
            timeout=None
        )
    
    @patch.object(CCAI, 'request')
    def test_send_with_options(self, mock_request):
        """Test sending SMS with options"""
        # Mock response
        mock_request.return_value = {"id": "msg-123", "status": "sent"}
        
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
        
        # Send SMS with options
        response = self.ccai.sms.send(
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
            "Preparing to send SMS",
            "Sending SMS",
            "SMS sent successfully"
        ])
        
        # Verify request was made correctly
        mock_request.assert_called_with(
            method="post",
            endpoint=f"/clients/{self.client_id}/campaigns/direct",
            data={
                "accounts": [
                    {
                        "firstName": "John",
                        "lastName": "Doe",
                        "phone": "+14156961732"
                    }
                ],
                "message": self.message,
                "title": self.title
            },
            timeout=60
        )
    
    def test_validation(self):
        """Test input validation"""
        # Test empty accounts
        with self.assertRaises(ValueError):
            self.ccai.sms.send(
                accounts=[],
                message=self.message,
                title=self.title
            )
        
        # Test empty message
        with self.assertRaises(ValueError):
            self.ccai.sms.send(
                accounts=[self.account],
                message="",
                title=self.title
            )
        
        # Test empty title
        with self.assertRaises(ValueError):
            self.ccai.sms.send(
                accounts=[self.account],
                message=self.message,
                title=""
            )


if __name__ == '__main__':
    unittest.main()
