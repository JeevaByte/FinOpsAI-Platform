"""
Cost allocation page for the CloudCostAI dashboard.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.utils.db import get_cost_data, get_cost_allocations, store_cost_allocation

def render_allocation_page():
    """Render the cost allocation page."""
    st.title("Cost Allocation")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["Cost Distribution", "Manage Allocations", "Tag Compliance"])
    
    with tab1:
        render_cost_distribution()
        
    with tab2:
        render_manage_allocations()
        
    with tab3:
        render_tag_compliance()

def render_cost_distribution():
    """Render cost distribution section."""
    st.subheader("Cost Distribution")
    
    # Date range selector
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.date.today().replace(day=1)
        )
        
    with col2:
        end_date = st.date_input(
            "End Date",
            value=datetime.date.today()
        )
    
    # Get cost allocations from database
    allocations = get_cost_allocations(
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d')
    )
    
    if allocations.empty:
        # If no allocations, check if we have cost data
        cost_data = get_cost_data(
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        if cost_data.empty:
            st.info("No cost data available for the selected period.")
            return
        else:
            st.warning("No cost allocations defined. Please allocate costs in the 'Manage Allocations' tab.")
            
            # Show unallocated costs
            cost_column = 'cost' if 'cost' in cost_data.columns else 'amount'
            
            # By provider
            provider_costs = cost_data.groupby('provider')[cost_column].sum().reset_index()
            
            fig = px.pie(
                provider_costs,
                values=cost_column,
                names='provider',
                title='Unallocated Costs by Provider'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # By service
            service_costs = cost_data.groupby('service')[cost_column].sum().reset_index()
            service_costs = service_costs.sort_values(cost_column, ascending=False)
            
            fig = px.bar(
                service_costs,
                x='service',
                y=cost_column,
                title='Unallocated Costs by Service',
                labels={cost_column: 'Cost ($)', 'service': 'Service'}
            )
            st.plotly_chart(fig, use_container_width=True)
            
            return
    
    # Display cost allocation visualizations
    
    # By business unit
    if 'business_unit' in allocations.columns:
        bu_costs = allocations.groupby('business_unit')['cost'].sum().reset_index()
        bu_costs = bu_costs.sort_values('cost', ascending=False)
        
        fig = px.pie(
            bu_costs,
            values='cost',
            names='business_unit',
            title='Cost by Business Unit'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # By project
    if 'project' in allocations.columns:
        project_costs = allocations.groupby('project')['cost'].sum().reset_index()
        project_costs = project_costs.sort_values('cost', ascending=False)
        
        fig = px.bar(
            project_costs,
            x='project',
            y='cost',
            title='Cost by Project',
            labels={'cost': 'Cost ($)', 'project': 'Project'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # By environment
    if 'environment' in allocations.columns:
        env_costs = allocations.groupby('environment')['cost'].sum().reset_index()
        
        fig = px.pie(
            env_costs,
            values='cost',
            names='environment',
            title='Cost by Environment'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # By provider and business unit
    if 'business_unit' in allocations.columns and 'provider' in allocations.columns:
        provider_bu_costs = allocations.groupby(['provider', 'business_unit'])['cost'].sum().reset_index()
        
        fig = px.bar(
            provider_bu_costs,
            x='provider',
            y='cost',
            color='business_unit',
            title='Cost by Provider and Business Unit',
            labels={'cost': 'Cost ($)', 'provider': 'Provider', 'business_unit': 'Business Unit'}
        )
        st.plotly_chart(fig, use_container_width=True)

def render_manage_allocations():
    """Render manage allocations section."""
    st.subheader("Manage Cost Allocations")
    
    # Get cost data
    cost_data = get_cost_data()
    
    if cost_data.empty:
        st.info("No cost data available. Please collect cost data first.")
        return
    
    # Ensure date is datetime
    if 'date' in cost_data.columns and not pd.api.types.is_datetime64_any_dtype(cost_data['date']):
        cost_data['date'] = pd.to_datetime(cost_data['date'])
    
    # Get unique dates, providers, and services
    dates = sorted(cost_data['date'].dt.strftime('%Y-%m-%d').unique())
    providers = sorted(cost_data['provider'].unique())
    services = sorted(cost_data['service'].unique())
    
    # Form for adding cost allocation
    with st.form("allocation_form"):
        st.write("Add Cost Allocation")
        
        col1, col2 = st.columns(2)
        
        with col1:
            date = st.selectbox("Date", dates)
            provider = st.selectbox("Provider", providers)
            
        with col2:
            service = st.selectbox("Service", services)
            
            # Filter cost data to get the amount
            filtered_data = cost_data[
                (cost_data['date'].dt.strftime('%Y-%m-%d') == date) & 
                (cost_data['provider'] == provider) & 
                (cost_data['service'] == service)
            ]
            
            cost_column = 'cost' if 'cost' in filtered_data.columns else 'amount'
            amount = filtered_data[cost_column].sum() if not filtered_data.empty else 0
            
            st.write(f"Cost: ${amount:.2f}")
        
        # Allocation fields
        st.write("Allocation Details")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            business_unit = st.selectbox(
                "Business Unit",
                ["Engineering", "Marketing", "Sales", "Finance", "HR", "Operations", "Other"]
            )
            
        with col2:
            project = st.text_input("Project", placeholder="e.g., Website Redesign")
            
        with col3:
            environment = st.selectbox(
                "Environment",
                ["Production", "Development", "Testing", "Staging"]
            )
        
        submitted = st.form_submit_button("Add Allocation")
        
        if submitted:
            if amount > 0:
                # Store allocation in database
                allocation_id = store_cost_allocation(
                    date=date,
                    cost=amount,
                    provider=provider,
                    service=service,
                    business_unit=business_unit,
                    project=project,
                    environment=environment
                )
                
                if allocation_id:
                    st.success(f"Cost allocation added for {service} on {date}")
                else:
                    st.error("Failed to add cost allocation")
            else:
                st.error("No cost data found for the selected date, provider, and service")
    
    # Display existing allocations
    st.subheader("Existing Allocations")
    
    allocations = get_cost_allocations()
    
    if allocations.empty:
        st.info("No cost allocations defined yet.")
    else:
        # Format for display
        display_df = allocations[['date', 'provider', 'service', 'cost', 'business_unit', 'project', 'environment']].copy()
        display_df.columns = ['Date', 'Provider', 'Service', 'Cost', 'Business Unit', 'Project', 'Environment']
        
        # Format cost
        display_df['Cost'] = display_df['Cost'].map('${:,.2f}'.format)
        
        st.dataframe(display_df, use_container_width=True)

def render_tag_compliance():
    """Render tag compliance section."""
    st.subheader("Tag Compliance")
    
    # Define required tags
    required_tags = {
        'AWS': ['Name', 'Environment', 'Project', 'Owner', 'CostCenter'],
        'GCP': ['name', 'environment', 'project', 'owner', 'cost-center'],
        'Azure': ['Name', 'Environment', 'Project', 'Owner', 'CostCenter']
    }
    
    # Placeholder for tag compliance data
    # In a real implementation, this would come from the cloud providers' APIs
    
    # Sample compliance data
    compliance_data = [
        {'provider': 'AWS', 'resource_type': 'EC2 Instance', 'total': 10, 'tagged': 8, 'compliance': 80},
        {'provider': 'AWS', 'resource_type': 'EBS Volume', 'total': 15, 'tagged': 10, 'compliance': 67},
        {'provider': 'AWS', 'resource_type': 'S3 Bucket', 'total': 5, 'tagged': 5, 'compliance': 100},
        {'provider': 'GCP', 'resource_type': 'Compute Engine', 'total': 8, 'tagged': 6, 'compliance': 75},
        {'provider': 'GCP', 'resource_type': 'Cloud Storage', 'total': 3, 'tagged': 2, 'compliance': 67},
        {'provider': 'Azure', 'resource_type': 'Virtual Machine', 'total': 12, 'tagged': 9, 'compliance': 75},
        {'provider': 'Azure', 'resource_type': 'Storage Account', 'total': 4, 'tagged': 3, 'compliance': 75}
    ]
    
    compliance_df = pd.DataFrame(compliance_data)
    
    # Display overall compliance
    overall_compliance = compliance_df['compliance'].mean()
    
    st.metric("Overall Tag Compliance", f"{overall_compliance:.1f}%")
    
    # Display compliance by provider
    provider_compliance = compliance_df.groupby('provider')['compliance'].mean().reset_index()
    
    fig = px.bar(
        provider_compliance,
        x='provider',
        y='compliance',
        title='Tag Compliance by Provider',
        labels={'compliance': 'Compliance (%)', 'provider': 'Provider'},
        color='compliance',
        color_continuous_scale='RdYlGn',
        range_color=[0, 100]
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Display compliance by resource type
    fig = px.bar(
        compliance_df,
        x='resource_type',
        y='compliance',
        color='provider',
        title='Tag Compliance by Resource Type',
        labels={'compliance': 'Compliance (%)', 'resource_type': 'Resource Type', 'provider': 'Provider'},
        barmode='group'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Display required tags
    st.subheader("Required Tags")
    
    for provider, tags in required_tags.items():
        st.write(f"**{provider}**")
        st.write(", ".join(tags))
    
    # Tag policy recommendations
    st.subheader("Tag Policy Recommendations")
    
    st.write("""
    1. **Implement automated tagging** - Use Infrastructure as Code to ensure all resources are tagged at creation
    2. **Set up tag enforcement** - Use cloud provider policies to require tags on resource creation
    3. **Regular compliance audits** - Schedule weekly tag compliance checks
    4. **Tag remediation** - Identify and tag untagged resources
    5. **Education** - Train teams on the importance of proper resource tagging
    """)

if __name__ == "__main__":
    render_allocation_page()