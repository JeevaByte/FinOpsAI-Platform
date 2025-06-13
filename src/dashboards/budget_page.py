"""
Budget management page for the CloudCostAI dashboard.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.utils.db import get_budgets, create_budget, get_budget_alerts, get_cost_data
from src.analyzers.budget_alerts import BudgetAlert

def render_budget_page():
    """Render the budget management page."""
    st.title("Budget Management")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["Budget Overview", "Create Budget", "Alert History"])
    
    with tab1:
        render_budget_overview()
        
    with tab2:
        render_create_budget()
        
    with tab3:
        render_alert_history()

def render_budget_overview():
    """Render the budget overview section."""
    st.subheader("Budget Overview")
    
    # Get budgets from database
    budgets_df = get_budgets()
    
    if budgets_df.empty:
        st.info("No budgets defined yet. Create a budget to get started.")
        return
    
    # Get current date
    now = datetime.datetime.now()
    
    # Create a list to store budget status
    budget_status = []
    
    for _, budget in budgets_df.iterrows():
        # Determine date range based on period
        if budget['period'] == 'monthly':
            start_date = datetime.date(now.year, now.month, 1)
            period_name = f"{now.strftime('%B %Y')}"
        elif budget['period'] == 'quarterly':
            quarter = (now.month - 1) // 3 + 1
            quarter_month = ((now.month - 1) // 3) * 3 + 1
            start_date = datetime.date(now.year, quarter_month, 1)
            period_name = f"Q{quarter} {now.year}"
        elif budget['period'] == 'yearly':
            start_date = datetime.date(now.year, 1, 1)
            period_name = f"{now.year}"
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
            actual_cost = 0
        else:
            # Filter by service if specified
            if budget['service']:
                cost_data = cost_data[cost_data['service'] == budget['service']]
                
            # Calculate total cost
            cost_column = 'cost' if 'cost' in cost_data.columns else 'amount'
            actual_cost = cost_data[cost_column].sum()
        
        # Calculate percentage of budget used
        percentage = (actual_cost / budget['amount']) * 100
        
        # Add to budget status list
        budget_status.append({
            'name': budget['name'],
            'period': period_name,
            'budget': budget['amount'],
            'actual': actual_cost,
            'percentage': percentage,
            'provider': budget['provider'] or 'All',
            'service': budget['service'] or 'All'
        })
    
    # Convert to DataFrame
    status_df = pd.DataFrame(budget_status)
    
    # Display budget status
    for _, status in status_df.iterrows():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write(f"**{status['name']}** ({status['period']})")
            st.write(f"Provider: {status['provider']}, Service: {status['service']}")
            
            # Create progress bar
            progress_color = 'normal'
            if status['percentage'] > 90:
                progress_color = 'error'
            elif status['percentage'] > 75:
                progress_color = 'warning'
                
            st.progress(min(status['percentage'] / 100, 1.0), text=f"{status['percentage']:.1f}%")
            
        with col2:
            st.write(f"${status['actual']:,.2f} / ${status['budget']:,.2f}")
            
            # Show warning if over budget
            if status['percentage'] > 100:
                st.error(f"Over budget by ${status['actual'] - status['budget']:,.2f}")
                
        st.divider()
    
    # Create bar chart comparing budget vs actual
    fig = px.bar(
        status_df,
        x='name',
        y=['budget', 'actual'],
        barmode='group',
        title='Budget vs. Actual Spending',
        labels={'value': 'Amount ($)', 'name': 'Budget', 'variable': 'Type'},
        color_discrete_map={'budget': 'blue', 'actual': 'red'}
    )
    st.plotly_chart(fig, use_container_width=True)

def render_create_budget():
    """Render the create budget section."""
    st.subheader("Create Budget")
    
    # Budget form
    with st.form("budget_form"):
        name = st.text_input("Budget Name", placeholder="e.g., AWS Monthly Budget")
        amount = st.number_input("Budget Amount ($)", min_value=0.0, value=1000.0, step=100.0)
        
        col1, col2 = st.columns(2)
        
        with col1:
            period = st.selectbox("Budget Period", ["monthly", "quarterly", "yearly"], index=0)
            
        with col2:
            provider = st.selectbox("Cloud Provider", ["All", "AWS", "GCP", "Azure"], index=0)
            provider = None if provider == "All" else provider
            
        service = st.text_input("Service (optional)", placeholder="e.g., EC2, leave empty for all services")
        service = None if not service else service
        
        submit = st.form_submit_button("Create Budget")
        
        if submit:
            if not name:
                st.error("Budget name is required")
            else:
                # Create budget in database
                budget_id = create_budget(name, amount, period, provider, service)
                
                if budget_id:
                    st.success(f"Budget '{name}' created successfully")
                else:
                    st.error("Failed to create budget")

def render_alert_history():
    """Render the alert history section."""
    st.subheader("Alert History")
    
    # Get alerts from database
    alerts_df = get_budget_alerts()
    
    if alerts_df.empty:
        st.info("No budget alerts yet.")
        return
    
    # Get budget information
    budgets_df = get_budgets()
    
    # Merge alerts with budget information
    if not budgets_df.empty:
        merged_df = pd.merge(alerts_df, budgets_df, left_on='budget_id', right_on='id', suffixes=('', '_budget'))
        
        # Format for display
        display_df = merged_df[['name', 'actual_cost', 'amount', 'percentage', 'alert_date', 'notified']].copy()
        display_df.columns = ['Budget', 'Actual Cost', 'Budget Amount', 'Percentage', 'Alert Date', 'Notified']
        
        # Format values
        display_df['Actual Cost'] = display_df['Actual Cost'].map('${:,.2f}'.format)
        display_df['Budget Amount'] = display_df['Budget Amount'].map('${:,.2f}'.format)
        display_df['Percentage'] = display_df['Percentage'].map('{:.1f}%'.format)
        
        # Display alerts
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("No budget information available.")

if __name__ == "__main__":
    render_budget_page()