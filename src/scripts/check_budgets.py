"""
Script to check budgets and send alerts.
Can be run as a scheduled task or cron job.
"""

import os
import sys
import datetime

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.analyzers.budget_alerts import BudgetAlert
from src.utils.db import get_budgets, store_budget_alert, mark_alert_notified
from src.utils.notification import send_email, send_slack_notification

def check_budgets_and_send_alerts():
    """
    Check all budgets and send alerts for any that exceed their threshold.
    """
    print(f"[{datetime.datetime.now()}] Checking budgets...")
    
    # Get budgets from database
    budgets_df = get_budgets()
    
    if budgets_df.empty:
        print("No budgets defined.")
        return
    
    # Initialize budget alert system
    alert_system = BudgetAlert()
    
    # Add budgets to the alert system
    for _, budget in budgets_df.iterrows():
        alert_system.add_budget(
            name=budget['name'],
            amount=budget['amount'],
            period=budget['period'],
            provider=budget['provider'],
            service=budget['service']
        )
    
    # Check budgets and get alerts
    alerts = alert_system.check_budgets()
    
    if not alerts:
        print("No budget alerts triggered.")
        return
    
    print(f"Found {len(alerts)} budget alerts.")
    
    # Process each alert
    for alert in alerts:
        print(f"Processing alert for budget '{alert['name']}'...")
        
        # Find the budget ID
        budget_id = None
        for _, budget in budgets_df.iterrows():
            if budget['name'] == alert['name']:
                budget_id = budget['id']
                break
        
        if budget_id is None:
            print(f"Could not find budget ID for '{alert['name']}'")
            continue
        
        # Store alert in database
        alert_id = store_budget_alert(
            budget_id=budget_id,
            actual_cost=alert['actual'],
            percentage=alert['percentage']
        )
        
        if not alert_id:
            print(f"Failed to store alert for budget '{alert['name']}'")
            continue
        
        # Send email notification
        email_sent = send_email(
            subject=f"Budget Alert: {alert['name']} exceeded by {alert['percentage']:.1f}%",
            body=f"""
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
            """,
            html=True
        )
        
        # Send Slack notification
        slack_sent = send_slack_notification(
            message=f"*Budget Alert*: {alert['name']} exceeded by {alert['percentage']:.1f}%\n" +
                   f"Budget: ${alert['budget']:,.2f}, Actual: ${alert['actual']:,.2f}\n" +
                   f"Please review your cloud spending."
        )
        
        # Mark alert as notified if either notification was sent
        if email_sent or slack_sent:
            mark_alert_notified(alert_id)
            print(f"Notifications sent for budget '{alert['name']}'")
        else:
            print(f"Failed to send notifications for budget '{alert['name']}'")

if __name__ == "__main__":
    check_budgets_and_send_alerts()