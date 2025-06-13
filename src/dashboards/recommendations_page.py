"""
Recommendations page for the CloudCostAI dashboard.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.utils.db import get_recommendations, update_recommendation_status
from src.analyzers.recommendation_engine import RecommendationEngine

def render_recommendations_page():
    """Render the recommendations page."""
    st.title("Cost Optimization Recommendations")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["All Recommendations", "Generate Recommendations", "Implementation Tracking"])
    
    with tab1:
        render_all_recommendations()
        
    with tab2:
        render_generate_recommendations()
        
    with tab3:
        render_implementation_tracking()

def render_all_recommendations():
    """Render all recommendations section."""
    st.subheader("All Recommendations")
    
    # Filters
    col1, col2 = st.columns(2)
    
    with col1:
        status_filter = st.multiselect(
            "Status",
            ["Open", "Implemented", "Rejected", "Deferred"],
            default=["Open"]
        )
        
    with col2:
        provider_filter = st.multiselect(
            "Cloud Provider",
            ["AWS", "GCP", "Azure"],
            default=[]
        )
    
    # Get recommendations from database
    recommendations = get_recommendations(
        status=status_filter[0] if len(status_filter) == 1 else None,
        provider=provider_filter[0] if len(provider_filter) == 1 else None
    )
    
    if recommendations.empty:
        st.info("No recommendations found. Generate recommendations to get started.")
        return
    
    # Apply filters
    if status_filter:
        recommendations = recommendations[recommendations['status'].isin(status_filter)]
        
    if provider_filter:
        recommendations = recommendations[recommendations['provider'].isin(provider_filter)]
    
    # Calculate total potential savings
    total_savings = recommendations['estimated_savings'].sum()
    st.metric("Total Potential Monthly Savings", f"${total_savings:,.2f}")
    
    # Display recommendations
    for _, rec in recommendations.iterrows():
        with st.expander(f"{rec['recommendation_type']}: {rec['resource_type']} ({rec['provider']})"):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.write(f"**Resource ID:** {rec['resource_id']}")
                st.write(f"**Current:** {rec['current_config']}")
                st.write(f"**Recommended:** {rec['recommended_config']}")
                st.write(f"**Justification:** {rec['justification']}")
                
            with col2:
                st.write(f"**Estimated Savings:** ${rec['estimated_savings']:,.2f}/month")
                st.write(f"**Confidence:** {rec['confidence']}")
                st.write(f"**Status:** {rec['status']}")
                
            with col3:
                # Status update buttons
                if rec['status'] == 'Open':
                    if st.button(f"Mark Implemented #{rec['id']}", key=f"impl_{rec['id']}"):
                        update_recommendation_status(rec['id'], 'Implemented')
                        st.experimental_rerun()
                        
                    if st.button(f"Reject #{rec['id']}", key=f"rej_{rec['id']}"):
                        update_recommendation_status(rec['id'], 'Rejected')
                        st.experimental_rerun()
                        
                    if st.button(f"Defer #{rec['id']}", key=f"def_{rec['id']}"):
                        update_recommendation_status(rec['id'], 'Deferred')
                        st.experimental_rerun()
                else:
                    if st.button(f"Reopen #{rec['id']}", key=f"reopen_{rec['id']}"):
                        update_recommendation_status(rec['id'], 'Open')
                        st.experimental_rerun()
            
            # Implementation steps
            if 'implementation_steps' in rec and rec['implementation_steps']:
                st.write("**Implementation Steps:**")
                for i, step in enumerate(rec['implementation_steps'], 1):
                    st.write(f"{i}. {step}")

def render_generate_recommendations():
    """Render generate recommendations section."""
    st.subheader("Generate New Recommendations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        recommendation_types = st.multiselect(
            "Recommendation Types",
            ["Compute Rightsizing", "Storage Optimization", "Reserved Instances/Savings Plans"],
            default=["Compute Rightsizing", "Storage Optimization", "Reserved Instances/Savings Plans"]
        )
        
    with col2:
        providers = st.multiselect(
            "Cloud Providers",
            ["AWS", "GCP", "Azure"],
            default=["AWS", "GCP", "Azure"]
        )
    
    if st.button("Generate Recommendations"):
        with st.spinner("Analyzing resources and generating recommendations..."):
            engine = RecommendationEngine()
            
            all_recommendations = []
            
            if "Compute Rightsizing" in recommendation_types:
                for provider in providers:
                    compute_recs = engine.analyze_compute_usage(provider=provider)
                    all_recommendations.extend(compute_recs)
            
            if "Storage Optimization" in recommendation_types:
                for provider in providers:
                    storage_recs = engine.analyze_storage_optimization(provider=provider)
                    all_recommendations.extend(storage_recs)
            
            if "Reserved Instances/Savings Plans" in recommendation_types:
                for provider in providers:
                    ri_recs = engine.analyze_reserved_instance_opportunities(provider=provider)
                    all_recommendations.extend(ri_recs)
            
            if all_recommendations:
                # Convert to DataFrame
                recommendations_df = pd.DataFrame(all_recommendations)
                
                # Store in database
                from src.utils.db import store_recommendations
                store_recommendations(recommendations_df)
                
                st.success(f"Generated {len(all_recommendations)} recommendations!")
                st.experimental_rerun()
            else:
                st.info("No new recommendations found.")

def render_implementation_tracking():
    """Render implementation tracking section."""
    st.subheader("Implementation Tracking")
    
    # Get recommendations from database
    recommendations = get_recommendations()
    
    if recommendations.empty:
        st.info("No recommendations found.")
        return
    
    # Calculate statistics
    total_recommendations = len(recommendations)
    implemented = len(recommendations[recommendations['status'] == 'Implemented'])
    rejected = len(recommendations[recommendations['status'] == 'Rejected'])
    deferred = len(recommendations[recommendations['status'] == 'Deferred'])
    open_recs = len(recommendations[recommendations['status'] == 'Open'])
    
    # Calculate potential and realized savings
    potential_savings = recommendations['estimated_savings'].sum()
    realized_savings = recommendations[recommendations['status'] == 'Implemented']['estimated_savings'].sum()
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Recommendations", total_recommendations)
        st.metric("Implemented", implemented)
        
    with col2:
        st.metric("Open", open_recs)
        st.metric("Rejected", rejected)
        
    with col3:
        st.metric("Potential Monthly Savings", f"${potential_savings:,.2f}")
        st.metric("Realized Monthly Savings", f"${realized_savings:,.2f}")
    
    # Create pie chart for recommendation status
    status_counts = recommendations['status'].value_counts().reset_index()
    status_counts.columns = ['Status', 'Count']
    
    fig = px.pie(
        status_counts,
        values='Count',
        names='Status',
        title='Recommendation Status Distribution',
        color='Status',
        color_discrete_map={
            'Open': 'blue',
            'Implemented': 'green',
            'Rejected': 'red',
            'Deferred': 'orange'
        }
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Create bar chart for savings by recommendation type
    if not recommendations.empty:
        savings_by_type = recommendations.groupby('recommendation_type')['estimated_savings'].sum().reset_index()
        savings_by_type = savings_by_type.sort_values('estimated_savings', ascending=False)
        
        fig = px.bar(
            savings_by_type,
            x='recommendation_type',
            y='estimated_savings',
            title='Potential Savings by Recommendation Type',
            labels={'recommendation_type': 'Recommendation Type', 'estimated_savings': 'Potential Monthly Savings ($)'}
        )
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    render_recommendations_page()