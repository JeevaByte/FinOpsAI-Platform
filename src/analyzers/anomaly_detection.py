"""
Anomaly detection module for identifying unusual cloud spending patterns.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.utils.db import get_cost_data

class AnomalyDetector:
    """Detects anomalies in cloud spending patterns."""
    
    def __init__(self, contamination=0.05):
        """
        Initialize the anomaly detector.
        
        Args:
            contamination (float): Expected proportion of anomalies in the dataset.
        """
        self.contamination = contamination
        self.model = None
        
    def detect_daily_anomalies(self, days=30, provider=None):
        """
        Detect anomalies in daily cloud spending.
        
        Args:
            days (int): Number of days to analyze
            provider (str, optional): Cloud provider filter
            
        Returns:
            pd.DataFrame: Detected anomalies
        """
        # Get cost data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        cost_data = get_cost_data(
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            provider=provider
        )
        
        if cost_data.empty:
            return pd.DataFrame()
        
        # Ensure date is datetime
        if 'date' in cost_data.columns and not pd.api.types.is_datetime64_any_dtype(cost_data['date']):
            cost_data['date'] = pd.to_datetime(cost_data['date'])
        
        # Group by date
        cost_column = 'cost' if 'cost' in cost_data.columns else 'amount'
        daily_costs = cost_data.groupby('date')[cost_column].sum().reset_index()
        
        # Need at least 7 data points for meaningful anomaly detection
        if len(daily_costs) < 7:
            return pd.DataFrame()
        
        # Prepare features
        X = daily_costs[cost_column].values.reshape(-1, 1)
        
        # Train isolation forest model
        self.model = IsolationForest(contamination=self.contamination, random_state=42)
        daily_costs['anomaly'] = self.model.fit_predict(X)
        
        # -1 indicates anomaly, 1 indicates normal
        anomalies = daily_costs[daily_costs['anomaly'] == -1].copy()
        
        if anomalies.empty:
            return pd.DataFrame()
        
        # Calculate anomaly score (higher means more anomalous)
        anomaly_scores = self.model.decision_function(X)
        daily_costs['anomaly_score'] = -anomaly_scores  # Negate so higher is more anomalous
        
        # Calculate percentage difference from mean
        mean_cost = daily_costs[daily_costs['anomaly'] == 1][cost_column].mean()
        anomalies['percentage_diff'] = ((anomalies[cost_column] - mean_cost) / mean_cost) * 100
        
        # Add severity level
        anomalies['severity'] = anomalies['percentage_diff'].apply(
            lambda x: 'High' if abs(x) > 50 else ('Medium' if abs(x) > 25 else 'Low')
        )
        
        return anomalies
    
    def detect_service_anomalies(self, days=30, provider=None):
        """
        Detect anomalies in service-level spending.
        
        Args:
            days (int): Number of days to analyze
            provider (str, optional): Cloud provider filter
            
        Returns:
            pd.DataFrame: Detected service-level anomalies
        """
        # Get cost data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        cost_data = get_cost_data(
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            provider=provider
        )
        
        if cost_data.empty:
            return pd.DataFrame()
        
        # Ensure date is datetime
        if 'date' in cost_data.columns and not pd.api.types.is_datetime64_any_dtype(cost_data['date']):
            cost_data['date'] = pd.to_datetime(cost_data['date'])
        
        # Group by date and service
        cost_column = 'cost' if 'cost' in cost_data.columns else 'amount'
        service_costs = cost_data.groupby(['date', 'service', 'provider'])[cost_column].sum().reset_index()
        
        # Get unique services
        services = service_costs['service'].unique()
        
        all_anomalies = []
        
        # Detect anomalies for each service
        for service in services:
            service_data = service_costs[service_costs['service'] == service].copy()
            
            # Need at least 7 data points for meaningful anomaly detection
            if len(service_data) < 7:
                continue
            
            # Prepare features
            X = service_data[cost_column].values.reshape(-1, 1)
            
            # Train isolation forest model
            model = IsolationForest(contamination=self.contamination, random_state=42)
            service_data['anomaly'] = model.fit_predict(X)
            
            # -1 indicates anomaly, 1 indicates normal
            anomalies = service_data[service_data['anomaly'] == -1].copy()
            
            if not anomalies.empty:
                # Calculate anomaly score
                anomaly_scores = model.decision_function(X)
                service_data['anomaly_score'] = -anomaly_scores
                
                # Calculate percentage difference from mean
                mean_cost = service_data[service_data['anomaly'] == 1][cost_column].mean()
                anomalies['percentage_diff'] = ((anomalies[cost_column] - mean_cost) / mean_cost) * 100
                
                # Add severity level
                anomalies['severity'] = anomalies['percentage_diff'].apply(
                    lambda x: 'High' if abs(x) > 50 else ('Medium' if abs(x) > 25 else 'Low')
                )
                
                all_anomalies.append(anomalies)
        
        if all_anomalies:
            return pd.concat(all_anomalies, ignore_index=True)
        else:
            return pd.DataFrame()
    
    def get_anomaly_insights(self, anomalies_df):
        """
        Generate insights for detected anomalies.
        
        Args:
            anomalies_df (pd.DataFrame): Detected anomalies
            
        Returns:
            list: Insights for each anomaly
        """
        if anomalies_df.empty:
            return []
        
        insights = []
        
        for _, anomaly in anomalies_df.iterrows():
            date = anomaly['date']
            cost = anomaly['cost'] if 'cost' in anomaly else anomaly['amount']
            
            if 'service' in anomaly:
                service = anomaly['service']
                provider = anomaly['provider']
                percentage_diff = anomaly['percentage_diff']
                severity = anomaly['severity']
                
                # Generate insight
                direction = 'increase' if percentage_diff > 0 else 'decrease'
                
                insight = {
                    'date': date,
                    'service': service,
                    'provider': provider,
                    'cost': cost,
                    'percentage_change': abs(percentage_diff),
                    'direction': direction,
                    'severity': severity,
                    'message': f"{severity} severity {direction} of {abs(percentage_diff):.1f}% in {service} costs on {date.strftime('%Y-%m-%d')}",
                    'possible_causes': self._get_possible_causes(service, provider, direction),
                    'recommended_actions': self._get_recommended_actions(service, provider, direction)
                }
            else:
                percentage_diff = anomaly['percentage_diff']
                severity = anomaly['severity']
                
                # Generate insight
                direction = 'increase' if percentage_diff > 0 else 'decrease'
                
                insight = {
                    'date': date,
                    'cost': cost,
                    'percentage_change': abs(percentage_diff),
                    'direction': direction,
                    'severity': severity,
                    'message': f"{severity} severity {direction} of {abs(percentage_diff):.1f}% in total costs on {date.strftime('%Y-%m-%d')}",
                    'possible_causes': self._get_possible_causes(None, None, direction),
                    'recommended_actions': self._get_recommended_actions(None, None, direction)
                }
            
            insights.append(insight)
        
        return insights
    
    def _get_possible_causes(self, service, provider, direction):
        """Get possible causes for an anomaly."""
        if direction == 'increase':
            if service == 'EC2' or service == 'Compute Engine' or service == 'Virtual Machines':
                return [
                    "New instances launched",
                    "Auto-scaling event",
                    "Instance type changes",
                    "Spot instance price fluctuation"
                ]
            elif service == 'S3' or service == 'Cloud Storage' or service == 'Storage':
                return [
                    "Large data upload",
                    "Increased data retrieval",
                    "Cross-region data transfer",
                    "Lifecycle policy changes"
                ]
            else:
                return [
                    "New resources provisioned",
                    "Increased usage of existing resources",
                    "Price changes",
                    "End of free tier or promotional pricing"
                ]
        else:  # decrease
            return [
                "Resources terminated or deleted",
                "Reduced usage",
                "Reserved instance or savings plan applied",
                "Price reduction"
            ]
    
    def _get_recommended_actions(self, service, provider, direction):
        """Get recommended actions for an anomaly."""
        if direction == 'increase':
            if service == 'EC2' or service == 'Compute Engine' or service == 'Virtual Machines':
                return [
                    "Review recently launched instances",
                    "Check auto-scaling policies",
                    "Verify instance types and sizes",
                    "Implement reserved instances for stable workloads"
                ]
            elif service == 'S3' or service == 'Cloud Storage' or service == 'Storage':
                return [
                    "Review data transfer patterns",
                    "Implement lifecycle policies",
                    "Check for unauthorized access",
                    "Optimize storage tiers"
                ]
            else:
                return [
                    "Review resource provisioning",
                    "Check for unauthorized usage",
                    "Implement tagging for cost allocation",
                    "Set up budget alerts"
                ]
        else:  # decrease
            return [
                "Verify expected resource termination",
                "Document cost optimization measures",
                "Share best practices with team"
            ]