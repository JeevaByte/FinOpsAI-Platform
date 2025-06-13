"""
Budget alerts and notifications module.
Monitors cloud costs against defined budgets and sends alerts when thresholds are exceeded.
"""

import pandas as pd
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import EMAIL_SENDER, EMAIL_RECIPIENTS, SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, ENABLE_EMAIL
from src.utils.db import get_cost_data

class BudgetAlert:
    """Monitors cloud costs against defined budgets and sends alerts."""
    
    def __init__(self):
        """Initialize the budget alert system."""
        self.budgets = {}
        self.notifications = []
    
    def add_budget(self, name, amount, period='monthly', provider=None, service=None):
        """
        Add a budget to monitor.
        
        Args:
            name (str): Budget name
            amount (float): Budget amount
            period (str): Budget period ('monthly', 'quarterly', 'yearly')
            provider (str, optional): Cloud provider filter. Defaults to None (all providers).
            service (str, optional): Service filter. Defaults to None (all services).
        """
        self.budgets[name] = {
            'amount': amount,
            'period': period,
            'provider': provider,
            'service': service,
            'last_alert': None
        }
        
    def check_budgets(self):
        """
        Check all budgets against current spending.
        
        Returns:
            list: List of triggered alerts
        """
        alerts = []
        
        # Get current date
        now = datetime.datetime.now()
        
        for name, budget in self.budgets.items():
            # Determine date range based on period
            if budget['period'] == 'monthly':
                start_date = datetime.date(now.year, now.month, 1)
            elif budget['period'] == 'quarterly':
                quarter_month = ((now.month - 1) // 3) * 3 + 1
                start_date = datetime.date(now.year, quarter_month, 1)
            elif budget['period'] == 'yearly':
                start_date = datetime.date(now.year, 1, 1)
            else:
                continue
                
            end_date = now.date()
            
            # Get cost data for the period
            cost_data = get_cost_data(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                provider=budget['provider']
            )
            
            if cost_data.empty:
                continue
                
            # Filter by service if specified
            if budget['service']:
                cost_data = cost_data[cost_data['service'] == budget['service']]
                
            # Calculate total cost
            cost_column = 'cost' if 'cost' in cost_data.columns else 'amount'
            total_cost = cost_data[cost_column].sum()
            
            # Check if budget is exceeded
            if total_cost > budget['amount']:
                # Calculate percentage over budget
                percentage = (total_cost - budget['amount']) / budget['amount'] * 100
                
                # Create alert
                alert = {
                    'name': name,
                    'budget': budget['amount'],
                    'actual': total_cost,
                    'percentage': percentage,
                    'period': budget['period'],
                    'provider': budget['provider'] or 'All',
                    'service': budget['service'] or 'All',
                    'date': now.strftime('%Y-%m-%d')
                }
                
                alerts.append(alert)
                
                # Update last alert time
                self.budgets[name]['last_alert'] = now
                
        return alerts
    
    def send_alert_email(self, alert):
        """
        Send an email alert for a budget threshold breach.
        
        Args:
            alert (dict): Alert information
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        if not ENABLE_EMAIL or not EMAIL_SENDER or not EMAIL_RECIPIENTS:
            return False
            
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = EMAIL_SENDER
            msg['To'] = ', '.join(EMAIL_RECIPIENTS)
            msg['Subject'] = f"Budget Alert: {alert['name']} exceeded by {alert['percentage']:.1f}%"
            
            # Create message body
            body = f"""
            <html>
            <body>
                <h2>Budget Alert</h2>
                <p>The following budget has been exceeded:</p>
                <ul>
                    <li><strong>Budget:</strong> {alert['name']}</li>
                    <li><strong>Amount:</strong> ${alert['budget']:,.2f}</li>
                    <li><strong>Actual Spend:</strong> ${alert['actual']:,.2f}</li>
                    <li><strong>Over Budget:</strong> ${alert['actual'] - alert['budget']:,.2f} ({alert['percentage']:.1f}%)</li>
                    <li><strong>Period:</strong> {alert['period']}</li>
                    <li><strong>Provider:</strong> {alert['provider']}</li>
                    <li><strong>Service:</strong> {alert['service']}</li>
                </ul>
                <p>Please review your cloud spending and take appropriate action.</p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            # Connect to SMTP server and send email
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                if SMTP_USERNAME and SMTP_PASSWORD:
                    server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)
                
            return True
            
        except Exception as e:
            print(f"Error sending email alert: {e}")
            return False
            
    def process_alerts(self):
        """
        Check budgets and send alerts if thresholds are exceeded.
        
        Returns:
            list: List of processed alerts
        """
        alerts = self.check_budgets()
        
        for alert in alerts:
            # Add to notifications list
            self.notifications.append(alert)
            
            # Send email alert
            if ENABLE_EMAIL:
                self.send_alert_email(alert)
                
        return alerts