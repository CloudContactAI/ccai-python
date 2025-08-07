"""
Examples of using the Email functionality in the CCAI Python library
"""

import asyncio
from datetime import datetime, timedelta
from ccai_python import CCAI
from ccai_python.email_service import EmailCampaign, EmailAccount, EmailOptions

# Initialize the CCAI client
ccai = CCAI(
    client_id="<YOUR_CLIENT_ID>",
    api_key="<YOUR_API_KEY>"
)

def send_single_email():
    """Example 1: Send a single email"""
    try:
        response = ccai.email.send_single(
            first_name="Andreas",
            last_name="Garcia",
            email="andreas@allcode.com",
            subject="Welcome to Our Service",
            message="<p>Hello Andreas,</p><p>Thank you for signing up for our service!</p><p>Best regards,<br>AllCode Team</p>",
            sender_email="noreply@allcode.com",
            reply_email="support@allcode.com",
            sender_name="AllCode",
            title="Welcome Email"
        )
        
        print("Email sent successfully:", response)
    except Exception as error:
        print("Error sending email:", error)

def send_email_campaign():
    """Example 2: Send an email campaign to multiple recipients"""
    try:
        accounts = [
            EmailAccount(
                first_name="John",
                last_name="Doe",
                email="john@example.com",
                phone=""
            ),
            EmailAccount(
                first_name="Jane",
                last_name="Smith",
                email="jane@example.com",
                phone=""
            ),
            EmailAccount(
                first_name="Bob",
                last_name="Johnson",
                email="bob@example.com",
                phone=""
            )
        ]
        
        campaign = EmailCampaign(
            subject="Monthly Newsletter",
            title="July 2025 Newsletter",
            message="""
                <h1>Monthly Newsletter - July 2025</h1>
                <p>Hello ${firstName},</p>
                <p>Here are our updates for this month:</p>
                <ul>
                    <li>New feature: Email campaigns</li>
                    <li>Improved performance</li>
                    <li>Bug fixes</li>
                </ul>
                <p>Thank you for being a valued customer!</p>
                <p>Best regards,<br>The Team</p>
            """,
            sender_email="newsletter@yourcompany.com",
            reply_email="support@yourcompany.com",
            sender_name="Your Company Newsletter",
            accounts=accounts
        )
        
        def progress_callback(status):
            print(f"Status: {status}")
        
        options = EmailOptions(on_progress=progress_callback)
        response = ccai.email.send_campaign(campaign, options)
        
        print("Email campaign sent successfully:", response)
    except Exception as error:
        print("Error sending email campaign:", error)

def schedule_email_campaign():
    """Example 3: Schedule an email campaign for future delivery"""
    try:
        # Schedule for tomorrow at 10:00 AM
        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        
        accounts = [
            EmailAccount(
                first_name="John",
                last_name="Doe",
                email="john@example.com",
                phone=""
            )
        ]
        
        campaign = EmailCampaign(
            subject="Upcoming Event Reminder",
            title="Event Reminder Campaign",
            message="""
                <h1>Reminder: Upcoming Event</h1>
                <p>Hello ${firstName},</p>
                <p>This is a reminder about our upcoming event tomorrow at 2:00 PM.</p>
                <p>We look forward to seeing you there!</p>
                <p>Best regards,<br>The Events Team</p>
            """,
            sender_email="events@yourcompany.com",
            reply_email="events@yourcompany.com",
            sender_name="Your Company Events",
            accounts=accounts,
            scheduled_timestamp=tomorrow.isoformat(),
            scheduled_timezone="America/New_York"
        )
        
        response = ccai.email.send_campaign(campaign)
        
        print("Email campaign scheduled successfully:", response)
    except Exception as error:
        print("Error scheduling email campaign:", error)

def send_html_template_email():
    """Example 4: Send an email with HTML template"""
    try:
        html_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; }
                    .header { background-color: #4CAF50; color: white; padding: 20px; text-align: center; }
                    .content { padding: 20px; }
                    .footer { background-color: #f1f1f1; padding: 10px; text-align: center; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Welcome, ${firstName}!</h1>
                </div>
                <div class="content">
                    <p>Thank you for joining our platform.</p>
                    <p>Here are some resources to get you started:</p>
                    <ul>
                        <li><a href="https://example.com/docs">Documentation</a></li>
                        <li><a href="https://example.com/tutorials">Tutorials</a></li>
                        <li><a href="https://example.com/support">Support</a></li>
                    </ul>
                </div>
                <div class="footer">
                    <p>&copy; 2025 Your Company. All rights reserved.</p>
                </div>
            </body>
            </html>
        """
        
        response = ccai.email.send_single(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            subject="Welcome to Our Platform",
            message=html_template,
            sender_email="welcome@yourcompany.com",
            reply_email="support@yourcompany.com",
            sender_name="Your Company",
            title="Welcome HTML Template Email"
        )
        
        print("HTML template email sent successfully:", response)
    except Exception as error:
        print("Error sending HTML template email:", error)

if __name__ == "__main__":
    # Run the examples
    # Uncomment the example you want to run
    send_single_email()
    send_email_campaign()
    schedule_email_campaign()
    send_html_template_email()