"""
Main entry point for the CloudCostAI application.
"""

import os
import sys
import argparse

def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description='CloudCostAI - Multi-Cloud Cost Optimization & Forecasting System')
    
    # Add subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Dashboard command
    dashboard_parser = subparsers.add_parser('dashboard', help='Run the Streamlit dashboard')
    
    # Collect command
    collect_parser = subparsers.add_parser('collect', help='Collect cost data from cloud providers')
    collect_parser.add_argument('--aws', action='store_true', help='Collect AWS data')
    collect_parser.add_argument('--gcp', action='store_true', help='Collect GCP data')
    collect_parser.add_argument('--azure', action='store_true', help='Collect Azure data')
    collect_parser.add_argument('--months', type=int, default=3, help='Number of months to collect')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze cost data and generate reports')
    analyze_parser.add_argument('--report', action='store_true', help='Generate cost report')
    analyze_parser.add_argument('--forecast', action='store_true', help='Generate cost forecast')
    analyze_parser.add_argument('--idle', action='store_true', help='Find idle resources')
    
    # Budget command
    budget_parser = subparsers.add_parser('budget', help='Budget management')
    budget_subparsers = budget_parser.add_subparsers(dest='budget_command', help='Budget command')
    
    # Add budget command
    add_budget_parser = budget_subparsers.add_parser('add', help='Add a new budget')
    add_budget_parser.add_argument('--name', required=True, help='Budget name')
    add_budget_parser.add_argument('--amount', type=float, required=True, help='Budget amount')
    add_budget_parser.add_argument('--period', choices=['monthly', 'quarterly', 'yearly'], default='monthly', help='Budget period')
    add_budget_parser.add_argument('--provider', help='Cloud provider (AWS, GCP, Azure)')
    add_budget_parser.add_argument('--service', help='Service name')
    
    # List budgets command
    list_budgets_parser = budget_subparsers.add_parser('list', help='List all budgets')
    
    # Check budgets command
    check_budgets_parser = budget_subparsers.add_parser('check', help='Check budgets and send alerts')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute the appropriate command
    if args.command == 'dashboard':
        print("Starting CloudCostAI dashboard...")
        os.system('streamlit run src/dashboards/streamlit_app.py')
        
    elif args.command == 'collect':
        from src.utils.db import init_db, store_cost_data
        from src.utils.helpers import generate_date_range
        
        print("Collecting cost data...")
        init_db()
        
        start_date, end_date = generate_date_range(args.months)
        
        if args.aws or not (args.gcp or args.azure):
            from src.collectors.aws import AWSCostCollector
            print("Collecting AWS cost data...")
            collector = AWSCostCollector()
            data = collector.get_cost_and_usage(start_date, end_date)
            store_cost_data(data)
            print(f"Collected {len(data)} AWS cost records")
            
        if args.gcp:
            from src.collectors.gcp import GCPCostCollector
            print("Collecting GCP cost data...")
            collector = GCPCostCollector()
            data = collector.get_cost_data(start_date=start_date, end_date=end_date)
            store_cost_data(data)
            print(f"Collected {len(data)} GCP cost records")
            
        if args.azure:
            from src.collectors.azure import AzureCostCollector
            print("Collecting Azure cost data...")
            collector = AzureCostCollector()
            data = collector.get_cost_data(start_date=start_date, end_date=end_date)
            store_cost_data(data)
            print(f"Collected {len(data)} Azure cost records")
            
    elif args.command == 'analyze':
        if args.report:
            print("Generating cost report...")
            # Code to generate cost report
            
        if args.forecast:
            print("Generating cost forecast...")
            from src.analyzers.forecast import CostForecaster
            from src.utils.db import get_cost_data
            import pandas as pd
            
            # Get data from database
            data = get_cost_data()
            if not data.empty:
                # Group by date for forecasting
                cost_column = 'cost' if 'cost' in data.columns else 'amount'
                forecast_data = data.groupby('date')[cost_column].sum().reset_index()
                
                # Generate forecast
                forecaster = CostForecaster(forecast_days=30)
                forecaster.train(forecast_data)
                forecast = forecaster.predict()
                monthly_forecast = forecaster.get_monthly_forecast()
                
                print("Monthly forecast:")
                print(monthly_forecast)
            else:
                print("No data available for forecasting")
            
        if args.idle:
            print("Finding idle resources...")
            from src.analyzers.idle_resources import IdleResourceAnalyzer
            from src.utils.db import store_idle_resources
            
            analyzer = IdleResourceAnalyzer()
            idle_resources = analyzer.get_all_idle_resources()
            
            if not idle_resources.empty:
                store_idle_resources(idle_resources)
                print(f"Found {len(idle_resources)} idle resources")
                print(f"Potential monthly savings: ${idle_resources['estimated_monthly_savings'].sum():.2f}")
            else:
                print("No idle resources found")
    
    elif args.command == 'budget':
        from src.utils.db import init_db, create_budget, get_budgets
        
        init_db()
        
        if args.budget_command == 'add':
            print(f"Adding budget '{args.name}'...")
            budget_id = create_budget(
                name=args.name,
                amount=args.amount,
                period=args.period,
                provider=args.provider,
                service=args.service
            )
            if budget_id:
                print(f"Budget '{args.name}' added successfully with ID {budget_id}")
            else:
                print(f"Failed to add budget '{args.name}'")
                
        elif args.budget_command == 'list':
            print("Listing budgets...")
            budgets = get_budgets()
            if budgets.empty:
                print("No budgets defined")
            else:
                for _, budget in budgets.iterrows():
                    provider = budget['provider'] or 'All'
                    service = budget['service'] or 'All'
                    print(f"{budget['id']}: {budget['name']} - ${budget['amount']:.2f} ({budget['period']}) - Provider: {provider}, Service: {service}")
                    
        elif args.budget_command == 'check':
            print("Checking budgets...")
            from src.scripts.check_budgets import check_budgets_and_send_alerts
            check_budgets_and_send_alerts()
            
        else:
            parser.print_help()
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()