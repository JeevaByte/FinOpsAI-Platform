"""
Idle resource analyzer module.
Aggregates and analyzes idle resource data from multiple cloud providers.
"""

import pandas as pd
from ..collectors.aws import AWSCostCollector
from ..collectors.gcp import GCPCostCollector
from ..collectors.azure import AzureCostCollector
from ..utils.helpers import calculate_savings_potential

class IdleResourceAnalyzer:
    """Analyzes idle resources across cloud providers."""
    
    def __init__(self):
        """Initialize the analyzer with cloud collectors."""
        self.aws_collector = AWSCostCollector()
        self.gcp_collector = GCPCostCollector()
        self.azure_collector = AzureCostCollector()
        
    def get_all_idle_resources(self, gcp_project_id=None):
        """
        Get idle resources from all configured cloud providers.
        
        Args:
            gcp_project_id (str, optional): GCP project ID. Defaults to None.
            
        Returns:
            pd.DataFrame: Combined idle resources data
        """
        # Get idle resources from each provider
        aws_idle = self.aws_collector.get_idle_resources()
        azure_idle = self.azure_collector.get_idle_resources()
        
        # GCP requires a project ID
        gcp_idle = pd.DataFrame()
        if gcp_project_id:
            gcp_idle = self.gcp_collector.get_idle_resources(gcp_project_id)
        
        # Add provider column if not present
        if not 'provider' in aws_idle.columns:
            aws_idle['provider'] = 'AWS'
        if not 'provider' in gcp_idle.columns and not gcp_idle.empty:
            gcp_idle['provider'] = 'GCP'
        if not 'provider' in azure_idle.columns:
            azure_idle['provider'] = 'Azure'
        
        # Combine all data
        all_idle = pd.concat([aws_idle, gcp_idle, azure_idle], ignore_index=True)
        
        return all_idle
    
    def get_savings_by_provider(self, idle_df):
        """
        Calculate potential savings grouped by cloud provider.
        
        Args:
            idle_df (pd.DataFrame): DataFrame with idle resource information
            
        Returns:
            pd.DataFrame: Savings by provider
        """
        if idle_df.empty or 'estimated_monthly_savings' not in idle_df.columns:
            return pd.DataFrame()
            
        savings_by_provider = idle_df.groupby('provider')['estimated_monthly_savings'].sum().reset_index()
        savings_by_provider.columns = ['provider', 'potential_monthly_savings']
        
        return savings_by_provider
    
    def get_savings_by_resource_type(self, idle_df):
        """
        Calculate potential savings grouped by resource type.
        
        Args:
            idle_df (pd.DataFrame): DataFrame with idle resource information
            
        Returns:
            pd.DataFrame: Savings by resource type
        """
        if idle_df.empty or 'estimated_monthly_savings' not in idle_df.columns:
            return pd.DataFrame()
            
        savings_by_type = idle_df.groupby('resource_type')['estimated_monthly_savings'].sum().reset_index()
        savings_by_type.columns = ['resource_type', 'potential_monthly_savings']
        
        return savings_by_type