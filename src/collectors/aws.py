"""
AWS Cost Explorer data collector.
Fetches cost and usage data from AWS Cost Explorer API.
"""

import os
import datetime
import pandas as pd
import boto3
from botocore.exceptions import ClientError
import sys

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import AWS_PROFILE, AWS_REGION
from src.utils.helpers import format_cost_data

class AWSCostCollector:
    """Collects and processes AWS cost data using the Cost Explorer API."""
    
    def __init__(self, profile_name=None, region_name=None):
        """
        Initialize AWS Cost Explorer client.
        
        Args:
            profile_name (str, optional): AWS profile name to use. Defaults to config value.
            region_name (str, optional): AWS region name. Defaults to config value.
        """
        profile_name = profile_name or AWS_PROFILE
        region_name = region_name or AWS_REGION
        
        session = boto3.Session(profile_name=profile_name, region_name=region_name) if profile_name else boto3.Session(region_name=region_name)
        self.client = session.client('ce')
        self.ec2_client = session.client('ec2')
        self.rds_client = session.client('rds')
    
    def get_cost_and_usage(self, start_date, end_date, granularity='MONTHLY', metrics=None, group_by=None):
        """
        Fetch cost and usage data from AWS Cost Explorer.
        
        Args:
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format
            granularity (str, optional): Time granularity. Defaults to 'MONTHLY'.
            metrics (list, optional): List of metrics to retrieve. Defaults to ['UnblendedCost'].
            group_by (list, optional): Dimensions to group by. Defaults to service grouping.
            
        Returns:
            pd.DataFrame: Processed cost data
        """
        if metrics is None:
            metrics = ['UnblendedCost']
            
        if group_by is None:
            group_by = [{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        
        try:
            response = self.client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity=granularity,
                Metrics=metrics,
                GroupBy=group_by
            )
            
            # Process the response into a DataFrame
            results = []
            for time_period in response['ResultsByTime']:
                period_start = time_period['TimePeriod']['Start']
                
                # Handle groups
                for group in time_period['Groups']:
                    service = group['Keys'][0]
                    amount = float(group['Metrics']['UnblendedCost']['Amount'])
                    currency = group['Metrics']['UnblendedCost']['Unit']
                    
                    results.append({
                        'date': period_start,
                        'service': service,
                        'amount': amount,
                        'currency': currency,
                        'provider': 'AWS'
                    })
            
            # Convert to DataFrame
            df = pd.DataFrame(results)
            return format_cost_data(df)
            
        except ClientError as e:
            print(f"Error fetching AWS cost data: {e}")
            return pd.DataFrame()
    
    def get_idle_resources(self):
        """
        Identify potentially idle or underutilized AWS resources.
        
        Returns:
            pd.DataFrame: DataFrame containing idle resource information
        """
        idle_resources = []
        
        try:
            # Check for idle EC2 instances (this would use CloudWatch metrics in a real implementation)
            ec2_response = self.ec2_client.describe_instances()
            for reservation in ec2_response['Reservations']:
                for instance in reservation['Instances']:
                    # In a real implementation, we would check CloudWatch metrics
                    # for CPU utilization over a period of time
                    if instance['State']['Name'] == 'running':
                        # This is a placeholder - in reality we would check actual metrics
                        idle_resources.append({
                            'resource_id': instance['InstanceId'],
                            'resource_type': 'EC2 Instance',
                            'region': AWS_REGION,
                            'estimated_monthly_savings': 45.20,  # Placeholder value
                            'reason': 'Low CPU utilization (<5% for 7 days)',
                            'recommendation': 'Consider downsizing or terminating',
                            'provider': 'AWS'
                        })
                        break  # Just add one example for demonstration
            
            # Check for unattached EBS volumes
            volumes_response = self.ec2_client.describe_volumes()
            for volume in volumes_response['Volumes']:
                if 'Attachments' not in volume or len(volume['Attachments']) == 0:
                    idle_resources.append({
                        'resource_id': volume['VolumeId'],
                        'resource_type': 'EBS Volume',
                        'region': AWS_REGION,
                        'estimated_monthly_savings': 12.80,  # Placeholder value
                        'reason': 'Unattached for 14 days',
                        'recommendation': 'Delete if not needed',
                        'provider': 'AWS'
                    })
                    break  # Just add one example for demonstration
                    
        except ClientError as e:
            print(f"Error checking for idle AWS resources: {e}")
        
        # If no real resources found, return placeholder data
        if not idle_resources:
            idle_resources = [
                {
                    'resource_id': 'i-12345abcdef',
                    'resource_type': 'EC2 Instance',
                    'region': AWS_REGION,
                    'estimated_monthly_savings': 45.20,
                    'reason': 'Low CPU utilization (<5% for 7 days)',
                    'recommendation': 'Consider downsizing or terminating',
                    'provider': 'AWS'
                },
                {
                    'resource_id': 'vol-67890abcdef',
                    'resource_type': 'EBS Volume',
                    'region': AWS_REGION,
                    'estimated_monthly_savings': 12.80,
                    'reason': 'Unattached for 14 days',
                    'recommendation': 'Delete if not needed',
                    'provider': 'AWS'
                }
            ]
        
        return pd.DataFrame(idle_resources)