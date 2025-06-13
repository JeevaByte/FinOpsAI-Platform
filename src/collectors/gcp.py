"""
Google Cloud Platform billing data collector.
Fetches cost data from GCP Billing API.
"""

import os
import pandas as pd
from google.cloud import billing
from google.cloud.billing import CloudCatalogClient, CloudBillingClient
import sys

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import GCP_PROJECT_ID, GCP_BILLING_ACCOUNT, GCP_CREDENTIALS_PATH
from src.utils.helpers import format_cost_data

class GCPCostCollector:
    """Collects and processes GCP billing data."""
    
    def __init__(self, credentials_path=None, project_id=None, billing_account=None):
        """
        Initialize GCP billing clients.
        
        Args:
            credentials_path (str, optional): Path to GCP service account credentials.
            project_id (str, optional): GCP project ID.
            billing_account (str, optional): GCP billing account ID.
        """
        self.credentials_path = credentials_path or GCP_CREDENTIALS_PATH
        self.project_id = project_id or GCP_PROJECT_ID
        self.billing_account = billing_account or GCP_BILLING_ACCOUNT
        
        if self.credentials_path:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.credentials_path
            
        try:
            self.billing_client = CloudBillingClient()
            self.catalog_client = CloudCatalogClient()
        except Exception as e:
            print(f"Error initializing GCP clients: {e}")
            self.billing_client = None
            self.catalog_client = None
    
    def get_cost_data(self, billing_account=None, start_date=None, end_date=None):
        """
        Fetch cost data from GCP Billing API.
        
        Args:
            billing_account (str, optional): GCP billing account ID
            start_date (str, optional): Start date in YYYY-MM-DD format
            end_date (str, optional): End date in YYYY-MM-DD format
            
        Returns:
            pd.DataFrame: Processed cost data
        """
        billing_account = billing_account or self.billing_account
        
        # In a real implementation, we would use the Cloud Billing API
        # to fetch actual billing data using the provided dates and billing account
        
        # For now, return sample data
        data = [
            {'date': '2023-05-01', 'service': 'Compute Engine', 'amount': 125.45, 'currency': 'USD'},
            {'date': '2023-05-01', 'service': 'Cloud Storage', 'amount': 42.10, 'currency': 'USD'},
            {'date': '2023-05-01', 'service': 'BigQuery', 'amount': 78.32, 'currency': 'USD'},
            {'date': '2023-06-01', 'service': 'Compute Engine', 'amount': 131.87, 'currency': 'USD'},
            {'date': '2023-06-01', 'service': 'Cloud Storage', 'amount': 45.22, 'currency': 'USD'},
            {'date': '2023-06-01', 'service': 'BigQuery', 'amount': 82.15, 'currency': 'USD'},
        ]
        
        # Add provider information
        for item in data:
            item['provider'] = 'GCP'
            
        df = pd.DataFrame(data)
        return format_cost_data(df)
    
    def get_idle_resources(self, project_id=None):
        """
        Identify potentially idle or underutilized GCP resources.
        
        Args:
            project_id (str, optional): GCP project ID
            
        Returns:
            pd.DataFrame: DataFrame containing idle resource information
        """
        project_id = project_id or self.project_id
        
        # In a real implementation, we would use the GCP APIs to check:
        # - VM instances with low CPU utilization
        # - Persistent disks not attached to instances
        # - Idle load balancers
        # - Underutilized Cloud SQL instances
        
        # Return placeholder data
        return pd.DataFrame({
            'resource_id': ['instance-1', 'disk-1'],
            'resource_type': ['GCE VM', 'Persistent Disk'],
            'region': ['us-central1', 'us-central1'],
            'estimated_monthly_savings': [52.80, 18.40],
            'reason': ['Low CPU utilization (<5% for 7 days)', 'Unattached for 14 days'],
            'recommendation': ['Consider downsizing or terminating', 'Delete if not needed'],
            'provider': ['GCP', 'GCP']
        })