"""
MMS Example - Demonstrates how to use the MMS functionality

:license: MIT
:copyright: 2025 CloudContactAI LLC
"""

import os
from ccai_python import CCAI, Account, SMSOptions

# Replace with your actual credentials
CLIENT_ID = "your-client-id"
API_KEY = "your-api-key"

# Initialize the CCAI client
ccai = CCAI(client_id=CLIENT_ID, api_key=API_KEY)

# Define a progress callback
def track_progress(status):
    print(f"Progress: {status}")

# Create options with progress tracking
options = SMSOptions(
    timeout=60,
    retries=3,
    on_progress=track_progress
)

# Example 1: Complete MMS workflow (get URL, upload image, send MMS)
def send_mms_with_image():
    # Path to your image file
    image_path = "path/to/your/image.jpg"
    content_type = "image/jpeg"
    
    # Define recipient
    account = Account(
        first_name="John",
        last_name="Doe",
        phone="+15551234567"  # Use E.164 format
    )
    
    # Message content and campaign title
    message = "Hello ${first_name}, check out this image!"
    title = "MMS Campaign Example"
    
    # Send MMS with image in one step
    response = ccai.mms.send_with_image(
        image_path=image_path,
        content_type=content_type,
        accounts=[account],
        message=message,
        title=title,
        options=options
    )
    
    print(f"MMS sent! Campaign ID: {response.campaign_id}")
    print(f"Messages sent: {response.messages_sent}")
    print(f"Status: {response.status}")

# Example 2: Step-by-step MMS workflow
def send_mms_step_by_step():
    # Path to your image file
    image_path = "path/to/your/image.jpg"
    file_name = os.path.basename(image_path)
    content_type = "image/jpeg"
    
    # Step 1: Get a signed URL for uploading
    print("Getting signed upload URL...")
    upload_response = ccai.mms.get_signed_upload_url(
        file_name=file_name,
        file_type=content_type
    )
    
    signed_url = upload_response["signedS3Url"]
    file_key = upload_response["fileKey"]
    
    print(f"Got signed URL: {signed_url}")
    print(f"File key: {file_key}")
    
    # Step 2: Upload the image to the signed URL
    print("Uploading image...")
    upload_success = ccai.mms.upload_image_to_signed_url(
        signed_url=signed_url,
        file_path=image_path,
        content_type=content_type
    )
    
    if not upload_success:
        print("Failed to upload image")
        return
    
    print("Image uploaded successfully")
    
    # Step 3: Send the MMS with the uploaded image
    print("Sending MMS...")
    
    # Define recipients
    accounts = [
        Account(first_name="John", last_name="Doe", phone="+15551234567"),
        Account(first_name="Jane", last_name="Smith", phone="+15559876543")
    ]
    
    # Message content and campaign title
    message = "Hello ${first_name}, check out this image!"
    title = "MMS Campaign Example"
    
    # Send the MMS
    response = ccai.mms.send(
        picture_file_key=file_key,
        accounts=accounts,
        message=message,
        title=title,
        options=options
    )
    
    print(f"MMS sent! Campaign ID: {response.campaign_id}")
    print(f"Messages sent: {response.messages_sent}")
    print(f"Status: {response.status}")

# Example 3: Send a single MMS
def send_single_mms():
    # Define the file key of an already uploaded image
    picture_file_key = f"{CLIENT_ID}/campaign/your-image.jpg"
    
    # Send a single MMS
    response = ccai.mms.send_single(
        picture_file_key=picture_file_key,
        first_name="John",
        last_name="Doe",
        phone="+15551234567",
        message="Hello ${first_name}, check out this image!",
        title="Single MMS Example",
        options=options
    )
    
    print(f"MMS sent! Campaign ID: {response.campaign_id}")
    print(f"Status: {response.status}")

if __name__ == "__main__":
    # Uncomment the example you want to run
    # send_mms_with_image()
    # send_mms_step_by_step()
    # send_single_mms()
    pass
