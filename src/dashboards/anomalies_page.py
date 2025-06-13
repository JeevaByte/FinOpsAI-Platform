"""
Anomalies page for the CloudCostAI dashboard.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.utils.db import get_anomalies, update_anomaly_status, get_cost_data
from src.analyzers.anomaly_detection import AnomalyDetector

def render_anomalies_page():
    """Render the anomalies page."""
    st.title("Cost Anomaly Detection")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["Active Anomalies", "Detect Anomalies", "Historical Analysis"])
    
    with tab1:
        render_active_anomalies()
        
    with tab2:
        render_detect_anomalies()
        
    with tab3:
        render_historical_analysis()

def render_active_anomalies():
    """Render active anomalies section."""
    st.subheader("Active Anomalies")
    
    # Filters
    col1, col2 = st.columns(2)
    
    with col1:
        severity_filter = st.multiselect(
            "Severity",
            ["High", "Medium", "Low"],
            default=["High", "Medium"]
        )
        
    with col2:
        provider_filter = st.multiselect(
            "Cloud Provider",
            ["AWS", "GCP", "Azure"],
            default=[]
        )
    
    # Get anomalies from database
    anomalies = get_anomalies(
        status="Open",
        severity=severity_filter[0] if len(severity_filter) == 1 else None,
        provider=provider_filter[0] if len(provider_filter) == 1 else None
    )
    
    if anomalies.empty:
        st.info("No active anomalies found.")
        return
    
    # Apply filters
    if severity_filter:
        anomalies = anomalies[anomalies['severity'].isin(severity_filter)]
        
    if provider_filter:
        anomalies = anomalies[anomalies['provider'].isin(provider_filter)]
    
    # Sort by severity and date
    severity_order = {'High': 0, 'Medium': 1, 'Low': 2}
    anomalies['severity_order'] = anomalies['severity'].map(severity_order)
    anomalies = anomalies.sort_values(['severity_order', 'date'], ascending=[True, False])
    
    # Display anomalies
    for _, anomaly in anomalies.iterrows():
        # Determine color based on severity
        severity_color = {
            'High': 'red',
            'Medium': 'orange',
            'Low': 'blue'
        }.get(anomaly['severity'], 'gray')
        
        with st.expander(f"{anomaly['severity']} severity anomaly on {anomaly['date']} - {anomaly.get('service', 'All services')}"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"<h4 style='color: {severity_color};'>{anomaly['message']}</h4>", unsafe_allow_html=True)
                st.write(f"**Cost:** ${anomaly['cost']:,.2f}")
                st.write(f"**Change:** {anomaly['percentage_change']:.1f}% {anomaly['direction']}")
                
                if 'provider' in anomaly and anomaly['provider']:
                    st.write(f"**Provider:** {anomaly['provider']}")
                
                if 'service' in anomaly and anomaly['service']:
                    st.write(f"**Service:** {anomaly['service']}")
                
                # Possible causes
                if 'possible_causes' in anomaly and anomaly['possible_causes']:
                    st.write("**Possible Causes:**")
                    for cause in anomaly['possible_causes']:
                        st.write(f"- {cause}")
                
                # Recommended actions
                if 'recommended_actions' in anomaly and anomaly['recommended_actions']:
                    st.write("**Recommended Actions:**")
                    for action in anomaly['recommended_actions']:
                        st.write(f"- {action}")
                
            with col2:
                # Action buttons
                if st.button(f"Mark Resolved #{anomaly['id']}", key=f"resolve_{anomaly['id']}"):
                    update_anomaly_status(anomaly['id'], 'Resolved')
                    st.experimental_rerun()
                    
                if st.button(f"Ignore #{anomaly['id']}", key=f"ignore_{anomaly['id']}"):
                    update_anomaly_status(anomaly['id'], 'Ignored')
                    st.experimental_rerun()

def render_detect_anomalies():
    """Render detect anomalies section."""
    st.subheader("Detect New Anomalies")
    
    col1, col2 = st.columns(2)
    
    with col1:
        days = st.slider("Analysis Period (days)", 7, 90, 30)
        
    with col2:
        providers = st.multiselect(
            "Cloud Providers",
            ["AWS", "GCP", "Azure"],
            default=["AWS", "GCP", "Azure"]
        )
    
    detection_type = st.radio(
        "Detection Type",
        ["Daily Total Cost", "Service-Level Cost"],
        horizontal=True
    )
    
    if st.button("Detect Anomalies"):
        with st.spinner("Analyzing cost patterns and detecting anomalies..."):
            detector = AnomalyDetector()
            
            all_anomalies = []
            
            if detection_type == "Daily Total Cost":
                for provider in providers:
                    anomalies = detector.detect_daily_anomalies(days=days, provider=provider)
                    if not anomalies.empty:
                        insights = detector.get_anomaly_insights(anomalies)
                        all_anomalies.extend(insights)
            else:  # Service-Level Cost
                for provider in providers:
                    anomalies = detector.detect_service_anomalies(days=days, provider=provider)
                    if not anomalies.empty:
                        insights = detector.get_anomaly_insights(anomalies)
                        all_anomalies.extend(insights)
            
            if all_anomalies:
                # Store in database
                from src.utils.db import store_anomalies
                store_anomalies(all_anomalies)
                
                st.success(f"Detected {len(all_anomalies)} anomalies!")
                st.experimental_rerun()
            else:
                st.info("No anomalies detected in the selected time period.")

def render_historical_analysis():
    """Render historical analysis section."""
    st.subheader("Historical Anomaly Analysis")
    
    # Get all anomalies from database
    anomalies = get_anomalies()
    
    if anomalies.empty:
        st.info("No historical anomaly data available.")
        return
    
    # Ensure date is datetime
    if 'date' in anomalies.columns and not pd.api.types.is_datetime64_any_dtype(anomalies['date']):
        anomalies['date'] = pd.to_datetime(anomalies['date'])
    
    # Calculate statistics
    total_anomalies = len(anomalies)
    resolved = len(anomalies[anomalies['status'] == 'Resolved'])
    ignored = len(anomalies[anomalies['status'] == 'Ignored'])
    open_anomalies = len(anomalies[anomalies['status'] == 'Open'])
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Anomalies", total_anomalies)
        
    with col2:
        st.metric("Resolved", resolved)
        
    with col3:
        st.metric("Open", open_anomalies)
    
    # Create timeline of anomalies
    if not anomalies.empty:
        # Group by date and count
        timeline = anomalies.groupby('date').size().reset_index()
        timeline.columns = ['date', 'count']
        
        # Get cost data for comparison
        start_date = anomalies['date'].min()
        end_date = anomalies['date'].max()
        
        cost_data = get_cost_data(
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        if not cost_data.empty:
            # Ensure date is datetime
            if 'date' in cost_data.columns and not pd.api.types.is_datetime64_any_dtype(cost_data['date']):
                cost_data['date'] = pd.to_datetime(cost_data['date'])
            
            # Group by date
            cost_column = 'cost' if 'cost' in cost_data.columns else 'amount'
            daily_costs = cost_data.groupby('date')[cost_column].sum().reset_index()
            
            # Create dual-axis chart
            fig = go.Figure()
            
            # Add cost line
            fig.add_trace(go.Scatter(
                x=daily_costs['date'],
                y=daily_costs[cost_column],
                name='Daily Cost',
                line=dict(color='blue', width=2)
            ))
            
            # Add anomaly markers
            fig.add_trace(go.Scatter(
                x=timeline['date'],
                y=timeline['count'],
                name='Anomalies',
                mode='markers',
                marker=dict(
                    color='red',
                    size=10,
                    symbol='circle'
                ),
                yaxis='y2'
            ))
            
            # Update layout for dual y-axes
            fig.update_layout(
                title='Daily Cost and Anomalies Over Time',
                xaxis=dict(title='Date'),
                yaxis=dict(
                    title='Daily Cost ($)',
                    titlefont=dict(color='blue'),
                    tickfont=dict(color='blue')
                ),
                yaxis2=dict(
                    title='Number of Anomalies',
                    titlefont=dict(color='red'),
                    tickfont=dict(color='red'),
                    anchor='x',
                    overlaying='y',
                    side='right'
                ),
                legend=dict(x=0, y=1)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Create pie chart for anomaly status
        status_counts = anomalies['status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']
        
        fig = px.pie(
            status_counts,
            values='Count',
            names='Status',
            title='Anomaly Status Distribution',
            color='Status',
            color_discrete_map={
                'Open': 'red',
                'Resolved': 'green',
                'Ignored': 'gray'
            }
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Create bar chart for anomalies by service
        if 'service' in anomalies.columns:
            service_counts = anomalies.groupby('service').size().reset_index()
            service_counts.columns = ['Service', 'Count']
            service_counts = service_counts.sort_values('Count', ascending=False)
            
            fig = px.bar(
                service_counts,
                x='Service',
                y='Count',
                title='Anomalies by Service',
                color='Count',
                color_continuous_scale='Reds'
            )
            st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    render_anomalies_page()