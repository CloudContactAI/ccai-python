import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ccai_python import CCAI, EmailAccount

ccai = CCAI(client_id="2682", api_key="eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJpbmZvQGFsbGNvZGUuY29tIiwiaXNzIjoiY2xvdWRjb250YWN0IiwibmJmIjoxNzE5NDQwMjM2LCJpYXQiOjE3MTk0NDAyMzYsInJvbGUiOiJVU0VSIiwiY2xpZW50SWQiOjI2ODIsImlkIjoyNzY0LCJ0eXBlIjoiQVBJX0tFWSIsImtleV9yYW5kb21faWQiOiI1MGRiOTUzZC1hMjUxLTRmZjMtODI5Yi01NjIyOGRhOGE1YTAifQ.PKVjXYHdjBMum9cTgLzFeY2KIb9b2tjawJ0WXalsb8Bckw1RuxeiYKS1bw5Cc36_Rfmivze0T7r-Zy0PVj2omDLq65io0zkBzIEJRNGDn3gx_AqmBrJ3yGnz9s0WTMr2-F1TFPUByzbj1eSOASIKeI7DGufTA5LDrRclVkz32Oo")

response = ccai.email.send_single(
    first_name="Andreas",
    last_name="Developer",
    email="info@allcode.com",
    subject="Test Email from Python",
    message="<h1>Hello Andreas!</h1><p>This is a test email from the Python CCAI client.</p>",
    sender_email="noreply@cloudcontactai.com",
    reply_email="support@cloudcontactai.com",
    sender_name="CloudContactAI",
    title="Python Email Test"
)

print("✅ Email Sent!")
print("📨 Response:", response)