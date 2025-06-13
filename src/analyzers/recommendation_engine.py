"""
AI-powered recommendation engine for cloud cost optimization.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.utils.db import get_cost_data, get_idle_resources

class RecommendationEngine:
    """Generates intelligent cost optimization recommendations based on usage patterns."""
    
    def __init__(self):
        """Initialize the recommendation engine."""
        self.recommendations = []
        
    def analyze_compute_usage(self, provider=None, months=3):
        """
        Analyze compute resource usage patterns and generate rightsizing recommendations.
        
        Args:
            provider (str, optional): Cloud provider filter
            months (int, optional): Number of months to analyze
            
        Returns:
            list: Compute rightsizing recommendations
        """
        # Get idle resources
        idle_df = get_idle_resources(provider)
        
        recommendations = []
        
        if not idle_df.empty:
            # Filter for compute resources
            compute_types = ['EC2 Instance', 'Virtual Machine', 'GCE VM']
            compute_df = idle_df[idle_df['resource_type'].isin(compute_types)]
            
            for _, resource in compute_df.iterrows():
                # Generate recommendation
                if 'Low CPU utilization' in resource['reason']:
                    # Suggest downsizing
                    current_type = self._extract_instance_type(resource['resource_id'], resource['provider'])
                    recommended_type = self._recommend_instance_type(current_type, resource['provider'])
                    
                    recommendations.append({
                        'resource_id': resource['resource_id'],
                        'resource_type': resource['resource_type'],
                        'provider': resource['provider'],
                        'recommendation_type': 'Rightsizing',
                        'current_config': current_type,
                        'recommended_config': recommended_type,
                        'estimated_savings': resource['estimated_monthly_savings'],
                        'confidence': 'High' if resource['estimated_monthly_savings'] > 50 else 'Medium',
                        'justification': f"Instance has {resource['reason']}",
                        'implementation_steps': self._get_resize_steps(resource['resource_id'], 
                                                                      current_type, 
                                                                      recommended_type, 
                                                                      resource['provider'])
                    })
        
        return recommendations
    
    def analyze_storage_optimization(self, provider=None):
        """
        Analyze storage usage and generate optimization recommendations.
        
        Args:
            provider (str, optional): Cloud provider filter
            
        Returns:
            list: Storage optimization recommendations
        """
        # Get idle resources
        idle_df = get_idle_resources(provider)
        
        recommendations = []
        
        if not idle_df.empty:
            # Filter for storage resources
            storage_types = ['EBS Volume', 'Persistent Disk', 'Managed Disk']
            storage_df = idle_df[idle_df['resource_type'].isin(storage_types)]
            
            for _, resource in storage_df.iterrows():
                # Generate recommendation
                if 'Unattached' in resource['reason']:
                    # Suggest deletion
                    recommendations.append({
                        'resource_id': resource['resource_id'],
                        'resource_type': resource['resource_type'],
                        'provider': resource['provider'],
                        'recommendation_type': 'Deletion',
                        'current_config': 'Unattached volume',
                        'recommended_config': 'Delete volume',
                        'estimated_savings': resource['estimated_monthly_savings'],
                        'confidence': 'High',
                        'justification': f"Storage volume has been {resource['reason']}",
                        'implementation_steps': self._get_deletion_steps(resource['resource_id'], 
                                                                        resource['resource_type'], 
                                                                        resource['provider'])
                    })
                elif 'Low I/O' in resource['reason']:
                    # Suggest changing storage tier
                    current_tier = self._extract_storage_tier(resource['resource_id'], resource['provider'])
                    recommended_tier = self._recommend_storage_tier(current_tier, resource['provider'])
                    
                    recommendations.append({
                        'resource_id': resource['resource_id'],
                        'resource_type': resource['resource_type'],
                        'provider': resource['provider'],
                        'recommendation_type': 'Storage Tier Change',
                        'current_config': current_tier,
                        'recommended_config': recommended_tier,
                        'estimated_savings': resource['estimated_monthly_savings'] * 0.7,  # Estimate savings from tier change
                        'confidence': 'Medium',
                        'justification': f"Storage volume has {resource['reason']}",
                        'implementation_steps': self._get_storage_tier_change_steps(resource['resource_id'], 
                                                                                  current_tier, 
                                                                                  recommended_tier, 
                                                                                  resource['provider'])
                    })
        
        return recommendations
    
    def analyze_reserved_instance_opportunities(self, provider=None, months=6):
        """
        Analyze usage patterns and identify reserved instance/savings plan opportunities.
        
        Args:
            provider (str, optional): Cloud provider filter
            months (int, optional): Number of months to analyze
            
        Returns:
            list: Reserved instance recommendations
        """
        # Get cost data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30*months)
        
        cost_data = get_cost_data(
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            provider=provider
        )
        
        recommendations = []
        
        if not cost_data.empty:
            # Filter for compute services
            compute_services = {
                'AWS': ['EC2', 'RDS'],
                'GCP': ['Compute Engine'],
                'Azure': ['Virtual Machines']
            }
            
            # Group by provider and service
            cost_column = 'cost' if 'cost' in cost_data.columns else 'amount'
            grouped = cost_data.groupby(['provider', 'service'])[cost_column].sum().reset_index()
            
            for _, row in grouped.iterrows():
                provider = row['provider']
                service = row['service']
                total_cost = row[cost_column]
                
                # Check if service is eligible for reserved instances
                if provider in compute_services and service in compute_services[provider]:
                    # Calculate potential savings (typically 30-60% for 1-year commitment)
                    savings_percentage = 0.4  # 40% average savings
                    estimated_savings = total_cost * savings_percentage
                    
                    if estimated_savings > 100:  # Only recommend if savings are significant
                        commitment_term = '1-year'
                        if estimated_savings > 500:
                            # For higher spend, consider 3-year commitment
                            commitment_term = '3-year'
                            savings_percentage = 0.6  # 60% average savings for 3-year
                            estimated_savings = total_cost * savings_percentage
                        
                        recommendations.append({
                            'resource_id': f"{provider}-{service}",
                            'resource_type': service,
                            'provider': provider,
                            'recommendation_type': 'Reserved Instance/Savings Plan',
                            'current_config': 'On-demand pricing',
                            'recommended_config': f"{commitment_term} commitment",
                            'estimated_savings': estimated_savings,
                            'confidence': 'Medium',
                            'justification': f"Consistent usage of {service} over the past {months} months",
                            'implementation_steps': self._get_reserved_instance_steps(provider, service, commitment_term)
                        })
        
        return recommendations
    
    def get_all_recommendations(self):
        """
        Get all cost optimization recommendations.
        
        Returns:
            pd.DataFrame: All recommendations
        """
        all_recommendations = []
        
        # Get compute recommendations
        compute_recs = self.analyze_compute_usage()
        all_recommendations.extend(compute_recs)
        
        # Get storage recommendations
        storage_recs = self.analyze_storage_optimization()
        all_recommendations.extend(storage_recs)
        
        # Get reserved instance recommendations
        ri_recs = self.analyze_reserved_instance_opportunities()
        all_recommendations.extend(ri_recs)
        
        # Convert to DataFrame
        if all_recommendations:
            return pd.DataFrame(all_recommendations)
        else:
            return pd.DataFrame()
    
    def _extract_instance_type(self, resource_id, provider):
        """Extract instance type from resource ID."""
        # This would use cloud provider APIs in a real implementation
        # Placeholder implementation
        if provider == 'AWS':
            return 't3.large'
        elif provider == 'GCP':
            return 'n1-standard-2'
        elif provider == 'Azure':
            return 'Standard_D2s_v3'
        return 'Unknown'
    
    def _recommend_instance_type(self, current_type, provider):
        """Recommend a more appropriate instance type."""
        # This would use a more sophisticated algorithm in a real implementation
        # Placeholder implementation
        instance_mapping = {
            'AWS': {
                't3.large': 't3.medium',
                'm5.xlarge': 'm5.large',
                'c5.2xlarge': 'c5.xlarge'
            },
            'GCP': {
                'n1-standard-2': 'n1-standard-1',
                'n1-standard-4': 'n1-standard-2',
                'n2-standard-2': 'e2-standard-2'
            },
            'Azure': {
                'Standard_D2s_v3': 'Standard_B2s',
                'Standard_D4s_v3': 'Standard_D2s_v3',
                'Standard_F4s': 'Standard_F2s'
            }
        }
        
        if provider in instance_mapping and current_type in instance_mapping[provider]:
            return instance_mapping[provider][current_type]
        return current_type
    
    def _get_resize_steps(self, resource_id, current_type, recommended_type, provider):
        """Get steps to resize a compute instance."""
        if provider == 'AWS':
            return [
                f"Stop the EC2 instance {resource_id}",
                f"Change instance type from {current_type} to {recommended_type}",
                f"Start the instance"
            ]
        elif provider == 'GCP':
            return [
                f"Stop the VM instance {resource_id}",
                f"Change machine type from {current_type} to {recommended_type}",
                f"Start the instance"
            ]
        elif provider == 'Azure':
            return [
                f"Stop the VM {resource_id}",
                f"Resize from {current_type} to {recommended_type}",
                f"Start the VM"
            ]
        return []
    
    def _extract_storage_tier(self, resource_id, provider):
        """Extract storage tier from resource ID."""
        # Placeholder implementation
        if provider == 'AWS':
            return 'gp2'
        elif provider == 'GCP':
            return 'Standard'
        elif provider == 'Azure':
            return 'Premium SSD'
        return 'Unknown'
    
    def _recommend_storage_tier(self, current_tier, provider):
        """Recommend a more appropriate storage tier."""
        # Placeholder implementation
        tier_mapping = {
            'AWS': {
                'gp2': 'gp3',
                'io1': 'gp3',
                'standard': 'sc1'
            },
            'GCP': {
                'Standard': 'Nearline',
                'SSD': 'Standard'
            },
            'Azure': {
                'Premium SSD': 'Standard SSD',
                'Standard SSD': 'Standard HDD'
            }
        }
        
        if provider in tier_mapping and current_tier in tier_mapping[provider]:
            return tier_mapping[provider][current_tier]
        return current_tier
    
    def _get_storage_tier_change_steps(self, resource_id, current_tier, recommended_tier, provider):
        """Get steps to change storage tier."""
        if provider == 'AWS':
            return [
                f"Create a snapshot of volume {resource_id}",
                f"Create a new volume with type {recommended_tier} from the snapshot",
                f"Detach the old volume and attach the new volume"
            ]
        elif provider == 'GCP':
            return [
                f"Create a snapshot of disk {resource_id}",
                f"Create a new disk with type {recommended_tier} from the snapshot",
                f"Detach the old disk and attach the new disk"
            ]
        elif provider == 'Azure':
            return [
                f"Create a snapshot of disk {resource_id}",
                f"Create a new disk with type {recommended_tier} from the snapshot",
                f"Detach the old disk and attach the new disk"
            ]
        return []
    
    def _get_deletion_steps(self, resource_id, resource_type, provider):
        """Get steps to delete a resource."""
        if provider == 'AWS':
            return [
                f"Verify that volume {resource_id} is not needed",
                f"Create a final snapshot if needed",
                f"Delete the volume using AWS Console or CLI"
            ]
        elif provider == 'GCP':
            return [
                f"Verify that disk {resource_id} is not needed",
                f"Create a final snapshot if needed",
                f"Delete the disk using GCP Console or gcloud"
            ]
        elif provider == 'Azure':
            return [
                f"Verify that disk {resource_id} is not needed",
                f"Create a final snapshot if needed",
                f"Delete the disk using Azure Portal or CLI"
            ]
        return []
    
    def _get_reserved_instance_steps(self, provider, service, term):
        """Get steps to purchase reserved instances or savings plans."""
        if provider == 'AWS':
            if service == 'EC2':
                return [
                    f"Analyze EC2 usage patterns to determine instance types to reserve",
                    f"Purchase {term} EC2 Reserved Instances or Savings Plan through AWS Console",
                    "Monitor utilization of reserved capacity"
                ]
            elif service == 'RDS':
                return [
                    f"Analyze RDS usage patterns to determine instance types to reserve",
                    f"Purchase {term} RDS Reserved Instances through AWS Console",
                    "Monitor utilization of reserved capacity"
                ]
        elif provider == 'GCP':
            return [
                f"Analyze {service} usage patterns",
                f"Purchase {term} commitment discounts through GCP Console",
                "Monitor utilization of committed resources"
            ]
        elif provider == 'Azure':
            return [
                f"Analyze {service} usage patterns",
                f"Purchase {term} reserved instances through Azure Portal",
                "Monitor utilization of reserved capacity"
            ]
        return []