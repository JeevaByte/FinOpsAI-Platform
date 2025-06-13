"""
Azure Cost Management data collector.
Fetches cost data from Azure Cost Management API.
"""

import os
import pandas as pd
from azure.identity import DefaultAzureCredential
from azure.mgmt.costmanagement import CostManagementClient
import sys

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import AZURE_SUBSCRIPTION_ID
from src.utils.helpers import format_cost_data

class AzureCostCollector:
    """Collects and processes Azure cost data using the Cost Management API."""
    
    def __init__(self, subscription_id=None):
        """
        Initialize Azure Cost Management client.
        
        Args:
            subscription_id (str, optional): Azure subscription ID. Defaults to config value.
        """
        self.subscription_id = subscription_id or AZURE_SUBSCRIPTION_ID
        
        try:
            self.credential = DefaultAzureCredential()
            self.client = CostManagementClient(self.credential, self.subscription_id) if self.subscription_id else None
        except Exception as e:
            print(f"Error initializing Azure client: {e}")
            self.client = None
    
    def get_cost_data(self, start_date=None, end_date=None, granularity='Monthly'):
        """
        Fetch cost data from Azure Cost Management API.
        
        Args:
            start_date (str, optional): Start date in YYYY-MM-DD format
            end_date (str, optional): End date in YYYY-MM-DD format
            granularity (str, optional): Time granularity. Defaults to 'Monthly'.
            
        Returns:
            pd.DataFrame: Processed cost data
        """
        # In a real implementation, we would use the Azure Cost Management API
        # to fetch actual billing data using the provided dates
        
        # For now, return sample data
        data = [
            {'date': '2023-05-01', 'service': 'Virtual Machines', 'amount': 145.75, 'currency': 'USD'},
            {'date': '2023-05-01', 'service': 'Storage', 'amount': 38.20, 'currency': 'USD'},
            {'date': '2023-05-01', 'service': 'Azure SQL', 'amount': 95.50, 'currency': 'USD'},
            {'date': '2023-06-01', 'service': 'Virtual Machines', 'amount': 152.30, 'currency': 'USD'},
            {'date': '2023-06-01', 'service': 'Storage', 'amount': 41.15, 'currency': 'USD'},
            {'date': '2023-06-01', 'service': 'Azure SQL', 'amount': 98.75, 'currency': 'USD'},
        ]
        
        # Add provider information
        for item in data:
            item['provider'] = 'Azure'
            
        df = pd.DataFrame(data)
        return format_cost_data(df)
    
    def get_idle_resources(self):
        """
        Identify potentially idle or underutilized Azure resources.
        
        Returns:
            pd.DataFrame: DataFrame containing idle resource information
        """
        # In a real implementation, we would use the Azure APIs to check:
        # - VMs with low CPU utilization
        # - Disks not attached to VMs
        # - Underutilized App Service plans
        # - Idle SQL databases
        
        # Return placeholder data
        return pd.DataFrame({
            'resource_id': ['/subscriptions/sub-id/resourceGroups/rg1/providers/Microsoft.Compute/virtualMachines/vm1', 
                           '/subscriptions/sub-id/resourceGroups/rg1/providers/Microsoft.Compute/disks/disk1'],
            'resource_type': ['Virtual Machine', 'Managed Disk'],
            'region': ['eastus', 'eastus'],
            'estimated_monthly_savings': [65.40, 22.10],
            'reason': ['Low CPU utilization (<5% for 7 days)', 'Unattached for 14 days'],
            'recommendation': ['Consider downsizing or terminating', 'Delete if not needed'],
            'provider': ['Azure', 'Azure']
        })