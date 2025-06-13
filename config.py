"""
Configuration settings for CloudCostAI.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# AWS Configuration
AWS_PROFILE = os.getenv('AWS_PROFILE', None)
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

# GCP Configuration
GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID', None)
GCP_BILLING_ACCOUNT = os.getenv('GCP_BILLING_ACCOUNT', None)
GCP_CREDENTIALS_PATH = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', None)

# Azure Configuration
AZURE_SUBSCRIPTION_ID = os.getenv('AZURE_SUBSCRIPTION_ID', None)

# Database Configuration
DB_PATH = os.getenv('DB_PATH', 'data/cloudcostai.db')

# Reporting Configuration
REPORT_PATH = os.getenv('REPORT_PATH', 'reports')

# Dashboard Configuration
DASHBOARD_TITLE = os.getenv('DASHBOARD_TITLE', 'CloudCostAI Dashboard')
REFRESH_INTERVAL = int(os.getenv('REFRESH_INTERVAL', '3600'))  # in seconds

# Email Notification Configuration
ENABLE_EMAIL = os.getenv('ENABLE_EMAIL', 'False').lower() == 'true'
EMAIL_SENDER = os.getenv('EMAIL_SENDER', '')
EMAIL_RECIPIENTS = os.getenv('EMAIL_RECIPIENTS', '').split(',') if os.getenv('EMAIL_RECIPIENTS') else []
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')

# Slack Notification Configuration
ENABLE_SLACK = os.getenv('ENABLE_SLACK', 'False').lower() == 'true'
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL', '')

# Budget Alert Configuration
BUDGET_CHECK_INTERVAL = int(os.getenv('BUDGET_CHECK_INTERVAL', '86400'))  # in seconds, default 24 hours