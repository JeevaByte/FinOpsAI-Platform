"""
Notification utilities for CloudCostAI.
"""

import smtplib
import requests
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import (
    EMAIL_SENDER, EMAIL_RECIPIENTS, SMTP_SERVER, SMTP_PORT, 
    SMTP_USERNAME, SMTP_PASSWORD, ENABLE_EMAIL,
    SLACK_WEBHOOK_URL, ENABLE_SLACK
)

def send_email(subject, body, recipients=None, html=True):
    """
    Send an email notification.
    
    Args:
        subject (str): Email subject
        body (str): Email body
        recipients (list, optional): List of recipients. Defaults to config value.
        html (bool, optional): Whether body is HTML. Defaults to True.
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    if not ENABLE_EMAIL or not EMAIL_SENDER:
        return False
        
    recipients = recipients or EMAIL_RECIPIENTS
    if not recipients:
        return False
        
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = ', '.join(recipients)
        msg['Subject'] = subject
        
        # Attach body
        msg.attach(MIMEText(body, 'html' if html else 'plain'))
        
        # Connect to SMTP server and send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            if SMTP_USERNAME and SMTP_PASSWORD:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
            
        return True
        
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_slack_notification(message, webhook_url=None):
    """
    Send a Slack notification.
    
    Args:
        message (str): Message to send
        webhook_url (str, optional): Slack webhook URL. Defaults to config value.
        
    Returns:
        bool: True if notification was sent successfully, False otherwise
    """
    if not ENABLE_SLACK:
        return False
        
    webhook_url = webhook_url or SLACK_WEBHOOK_URL
    if not webhook_url:
        return False
        
    try:
        payload = {"text": message}
        response = requests.post(
            webhook_url,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"}
        )
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error sending Slack notification: {e}")
        return False