"""
Streamlit dashboard for CloudCostAI.
"""

import os
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import datetime
from dateutil.relativedelta import relativedelta
import sys

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import DASHBOARD_TITLE, REFRESH_INTERVAL
from src.collectors.aws import AWSCostCollector
from src.collectors.gcp import GCPCostCollector
from src.collectors.azure import AzureCostCollector
from src.analyzers.idle_resources import IdleResourceAnalyzer
from src.analyzers.forecast import CostForecaster
from src.utils.helpers import generate_date_range
from src.utils.db import get_cost_data, get_idle_resources, store_cost_data, store_idle_resources, init_db
from src.dashboards.budget_page import render_budget_page
from src.dashboards.recommendations_page import render_recommendations_page
from src.dashboards.anomalies_page import render_anomalies_page
from src.dashboards.allocation_page import render_allocation_page

# Initialize database
init_db()

# Page configuration
st.set_page_config(
    page_title=DASHBOARD_TITLE,
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar for configuration
st.sidebar.title("CloudCostAI")
st.sidebar.image("https://img.icons8.com/fluency/96/000000/cloud-cost.png", width=100)

# Navigation
page = st.sidebar.radio(
    "Navigation", 
    ["Dashboard", "Budget Management", "Recommendations", "Anomaly Detection", "Cost Allocation"]
)

if page == "Budget Management":
    render_budget_page()
elif page == "Recommendations":
    render_recommendations_page()
elif page == "Anomaly Detection":
    render_anomalies_page()
elif page == "Cost Allocation":
    render_allocation_page()
else:
    # Date range selector
    st.sidebar.subheader("Date Range")
    months_back = st.sidebar.slider("Months to analyze:", 1, 12, 3)

    # Cloud provider selector
    st.sidebar.subheader("Cloud Providers")
    use_aws = st.sidebar.checkbox("AWS", value=True)
    use_gcp = st.sidebar.checkbox("Google Cloud", value=True)
    use_azure = st.sidebar.checkbox("Azure", value=True)

    # Data source selector
    st.sidebar.subheader("Data Source")
    use_live_data = st.sidebar.checkbox("Use Live Data", value=False, 
                                      help="If checked, will attempt to fetch data from cloud providers. Otherwise, uses sample data.")

    # Main dashboard
    st.title("Cloud Cost Optimization Dashboard")

    # Initialize collectors
    @st.cache_data(ttl=REFRESH_INTERVAL)
    def load_data(months, use_live=False):
        """Load and cache cloud cost data"""
        start_date, end_date = generate_date_range(months)
        
        all_data = []
        
        # Check if we have data in the database first
        db_data = get_cost_data(start_date=start_date, end_date=end_date)
        
        if not db_data.empty and not use_live:
            return db_data
        
        if use_aws:
            try:
                aws_collector = AWSCostCollector()
                if use_live:
                    aws_data = aws_collector.get_cost_and_usage(start_date, end_date)
                else:
                    # Use sample data
                    sample_data = pd.read_csv('data/sample_billing_data.csv')
                    aws_data = sample_data[sample_data['provider'] == 'AWS'].copy()
                
                all_data.append(aws_data)
            except Exception as e:
                st.error(f"Error loading AWS data: {e}")
        
        if use_gcp:
            try:
                gcp_collector = GCPCostCollector()
                if use_live:
                    gcp_data = gcp_collector.get_cost_data(start_date=start_date, end_date=end_date)
                else:
                    # Use sample data
                    sample_data = pd.read_csv('data/sample_billing_data.csv')
                    gcp_data = sample_data[sample_data['provider'] == 'GCP'].copy()
                    
                all_data.append(gcp_data)
            except Exception as e:
                st.error(f"Error loading GCP data: {e}")
        
        if use_azure:
            try:
                azure_collector = AzureCostCollector()
                if use_live:
                    azure_data = azure_collector.get_cost_data(start_date=start_date, end_date=end_date)
                else:
                    # Use sample data
                    sample_data = pd.read_csv('data/sample_billing_data.csv')
                    azure_data = sample_data[sample_data['provider'] == 'Azure'].copy()
                    
                all_data.append(azure_data)
            except Exception as e:
                st.error(f"Error loading Azure data: {e}")
        
        if all_data:
            combined_data = pd.concat(all_data, ignore_index=True)
            # Store in database for future use
            try:
                store_cost_data(combined_data)
            except Exception as e:
                st.warning(f"Could not store data in database: {e}")
            return combined_data
        return pd.DataFrame()

    # Load data
    with st.spinner("Loading cloud cost data..."):
        df = load_data(months_back, use_live=use_live_data)

    if df.empty:
        st.warning("No data available. Please check your cloud provider credentials and selections.")
    else:
        # Display metrics
        col1, col2, col3 = st.columns(3)
        
        # Total cost
        total_cost = df['cost'].sum() if 'cost' in df.columns else df['amount'].sum()
        col1.metric("Total Cloud Spend", f"${total_cost:,.2f}")
        
        # Cost by provider
        cost_column = 'cost' if 'cost' in df.columns else 'amount'
        provider_costs = df.groupby('provider')[cost_column].sum()
        if 'AWS' in provider_costs:
            col2.metric("AWS Cost", f"${provider_costs.get('AWS', 0):,.2f}")
        if 'GCP' in provider_costs:
            col2.metric("GCP Cost", f"${provider_costs.get('GCP', 0):,.2f}")
        if 'Azure' in provider_costs:
            col3.metric("Azure Cost", f"${provider_costs.get('Azure', 0):,.2f}")
        
        # Cost trend over time
        st.subheader("Cost Trend Over Time")
        
        # Ensure date is datetime
        if 'date' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['date']):
            df['date'] = pd.to_datetime(df['date'])
        
        # Group by date and provider
        time_df = df.groupby(['date', 'provider'])[cost_column].sum().reset_index()
        
        # Create line chart
        fig = px.line(
            time_df, 
            x='date', 
            y=cost_column, 
            color='provider',
            title='Cloud Costs Over Time',
            labels={cost_column: 'Cost ($)', 'date': 'Date', 'provider': 'Cloud Provider'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Cost breakdown by service
        st.subheader("Cost Breakdown by Service")
        
        # Group by service and provider
        service_df = df.groupby(['service', 'provider'])[cost_column].sum().reset_index()
        
        # Create bar chart
        fig = px.bar(
            service_df, 
            x='service', 
            y=cost_column, 
            color='provider',
            title='Cost by Service',
            labels={cost_column: 'Cost ($)', 'service': 'Service', 'provider': 'Cloud Provider'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Create tabs for additional insights
        tab1, tab2, tab3 = st.tabs(["Idle Resources", "Cost Forecast", "Optimization Summary"])
        
        with tab1:
            # Idle resources
            st.subheader("Idle Resource Analysis")
            
            # Get idle resources
            with st.spinner("Analyzing idle resources..."):
                # Check if we have idle resources in the database
                idle_df = get_idle_resources()
                
                if idle_df.empty or use_live_data:
                    analyzer = IdleResourceAnalyzer()
                    idle_df = analyzer.get_all_idle_resources()
                    
                    # Store in database
                    if not idle_df.empty:
                        try:
                            store_idle_resources(idle_df)
                        except Exception as e:
                            st.warning(f"Could not store idle resources in database: {e}")
            
            if not idle_df.empty:
                # Calculate total potential savings
                total_savings = idle_df['estimated_monthly_savings'].sum()
                st.info(f"Potential monthly savings: ${total_savings:,.2f}")
                
                # Display idle resources
                st.dataframe(idle_df)
                
                # Savings by provider
                if 'provider' in idle_df.columns:
                    savings_by_provider = idle_df.groupby('provider')['estimated_monthly_savings'].sum().reset_index()
                    savings_by_provider.columns = ['provider', 'potential_monthly_savings']
                    
                    if not savings_by_provider.empty:
                        fig = px.pie(
                            savings_by_provider, 
                            values='potential_monthly_savings', 
                            names='provider',
                            title='Potential Savings by Provider'
                        )
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No idle resources detected.")
        
        with tab2:
            # Cost forecasting
            st.subheader("Cost Forecast")
            
            # Prepare data for forecasting
            forecast_data = df.groupby('date')[cost_column].sum().reset_index()
            
            if len(forecast_data) >= 3:  # Need enough data points for forecasting
                with st.spinner("Generating forecast..."):
                    forecaster = CostForecaster(forecast_days=30)
                    forecaster.train(forecast_data)
                    forecast = forecaster.predict()
                    monthly_forecast = forecaster.get_monthly_forecast()
                
                # Display monthly forecast
                st.write("Projected Monthly Costs:")
                st.dataframe(monthly_forecast)
                
                # Plot forecast
                fig = go.Figure()
                
                # Historical data
                fig.add_trace(go.Scatter(
                    x=forecast_data['date'],
                    y=forecast_data[cost_column],
                    mode='markers+lines',
                    name='Historical Cost',
                    line=dict(color='blue')
                ))
                
                # Forecast
                fig.add_trace(go.Scatter(
                    x=forecast['ds'],
                    y=forecast['yhat'],
                    mode='lines',
                    name='Forecast',
                    line=dict(color='red')
                ))
                
                # Confidence interval
                fig.add_trace(go.Scatter(
                    x=forecast['ds'].tolist() + forecast['ds'].tolist()[::-1],
                    y=forecast['yhat_upper'].tolist() + forecast['yhat_lower'].tolist()[::-1],
                    fill='toself',
                    fillcolor='rgba(255,0,0,0.2)',
                    line=dict(color='rgba(255,255,255,0)'),
                    name='Confidence Interval'
                ))
                
                fig.update_layout(
                    title='Cost Forecast',
                    xaxis_title='Date',
                    yaxis_title='Cost ($)',
                    legend=dict(x=0, y=1)
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Not enough data for forecasting. Need at least 3 data points.")
        
        with tab3:
            # Optimization summary
            st.subheader("Optimization Summary")
            
            # Get recommendations from database
            from src.utils.db import get_recommendations
            recommendations = get_recommendations(status='Open')
            
            # Get anomalies from database
            from src.utils.db import get_anomalies
            anomalies = get_anomalies(status='Open')
            
            # Calculate metrics
            total_recommendations = len(recommendations)
            total_anomalies = len(anomalies)
            
            potential_savings = recommendations['estimated_savings'].sum() if not recommendations.empty else 0
            
            # Display metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Open Recommendations", total_recommendations)
                
            with col2:
                st.metric("Potential Monthly Savings", f"${potential_savings:,.2f}")
                
            with col3:
                st.metric("Active Anomalies", total_anomalies)
            
            # Display top recommendations
            if not recommendations.empty:
                st.subheader("Top Recommendations")
                
                # Sort by estimated savings
                top_recs = recommendations.sort_values('estimated_savings', ascending=False).head(5)
                
                for _, rec in top_recs.iterrows():
                    st.write(f"**{rec['recommendation_type']}**: {rec['resource_type']} - ${rec['estimated_savings']:,.2f}/month")
            
            # Display recent anomalies
            if not anomalies.empty:
                st.subheader("Recent Anomalies")
                
                # Sort by date
                recent_anomalies = anomalies.sort_values('date', ascending=False).head(5)
                
                for _, anomaly in recent_anomalies.iterrows():
                    st.write(f"**{anomaly['severity']} severity**: {anomaly['message']}")

# Footer
st.markdown("---")
st.markdown("CloudCostAI - Multi-Cloud Cost Optimization & Forecasting System")

if __name__ == "__main__":
    # This will be executed when the script is run directly
    pass