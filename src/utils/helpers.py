"""
Helper functions for the CloudCostAI platform.
"""

import pandas as pd
import datetime

def format_cost_data(df):
    """
    Standardize cost data format across different cloud providers.
    
    Args:
        df (pd.DataFrame): Raw cost data from a cloud provider
        
    Returns:
        pd.DataFrame: Standardized cost data
    """
    # Ensure date column is datetime
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    
    # Ensure consistent column names
    column_mapping = {
        'service': 'service',
        'amount': 'cost',
        'currency': 'currency',
        'provider': 'provider'
    }
    
    df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
    
    return df

def generate_date_range(months_back=3):
    """
    Generate start and end dates for cost queries.
    
    Args:
        months_back (int): Number of months to look back
        
    Returns:
        tuple: (start_date, end_date) as strings in YYYY-MM-DD format
    """
    end_date = datetime.date.today()
    start_date = (end_date - datetime.timedelta(days=30*months_back))
    
    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

def calculate_savings_potential(idle_resources_df):
    """
    Calculate total potential savings from idle resources.
    
    Args:
        idle_resources_df (pd.DataFrame): DataFrame with idle resource information
        
    Returns:
        float: Total potential monthly savings
    """
    if 'estimated_monthly_savings' in idle_resources_df.columns:
        return idle_resources_df['estimated_monthly_savings'].sum()
    return 0.0