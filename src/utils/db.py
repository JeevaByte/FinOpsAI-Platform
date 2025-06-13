"""
Database utilities for CloudCostAI.
"""

import os
import sqlite3
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, MetaData, Table, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import DB_PATH

# Ensure data directory exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Create SQLAlchemy engine
engine = create_engine(f'sqlite:///{DB_PATH}')
Base = declarative_base()
Session = sessionmaker(bind=engine)

class CostData(Base):
    """Cost data table model."""
    __tablename__ = 'cost_data'
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    service = Column(String, nullable=False)
    cost = Column(Float, nullable=False)
    currency = Column(String, nullable=False)
    provider = Column(String, nullable=False)
    
class IdleResource(Base):
    """Idle resource table model."""
    __tablename__ = 'idle_resources'
    
    id = Column(Integer, primary_key=True)
    resource_id = Column(String, nullable=False)
    resource_type = Column(String, nullable=False)
    region = Column(String, nullable=False)
    estimated_monthly_savings = Column(Float, nullable=False)
    reason = Column(String, nullable=True)
    recommendation = Column(String, nullable=True)
    provider = Column(String, nullable=False)

class Budget(Base):
    """Budget table model."""
    __tablename__ = 'budgets'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    period = Column(String, nullable=False)  # monthly, quarterly, yearly
    provider = Column(String, nullable=True)
    service = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    
class BudgetAlert(Base):
    """Budget alert table model."""
    __tablename__ = 'budget_alerts'
    
    id = Column(Integer, primary_key=True)
    budget_id = Column(Integer, nullable=False)
    actual_cost = Column(Float, nullable=False)
    percentage = Column(Float, nullable=False)
    alert_date = Column(DateTime, default=datetime.datetime.now)
    notified = Column(Boolean, default=False)

class Recommendation(Base):
    """Recommendation table model."""
    __tablename__ = 'recommendations'
    
    id = Column(Integer, primary_key=True)
    resource_id = Column(String, nullable=False)
    resource_type = Column(String, nullable=False)
    provider = Column(String, nullable=False)
    recommendation_type = Column(String, nullable=False)
    current_config = Column(String, nullable=True)
    recommended_config = Column(String, nullable=True)
    estimated_savings = Column(Float, nullable=False)
    confidence = Column(String, nullable=False)  # High, Medium, Low
    justification = Column(Text, nullable=True)
    implementation_steps = Column(Text, nullable=True)  # JSON string of steps
    status = Column(String, default='Open')  # Open, Implemented, Rejected, Deferred
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

class AnomalyDetection(Base):
    """Anomaly detection table model."""
    __tablename__ = 'anomaly_detections'
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    service = Column(String, nullable=True)
    provider = Column(String, nullable=True)
    cost = Column(Float, nullable=False)
    percentage_change = Column(Float, nullable=False)
    direction = Column(String, nullable=False)  # increase, decrease
    severity = Column(String, nullable=False)  # High, Medium, Low
    message = Column(Text, nullable=False)
    possible_causes = Column(Text, nullable=True)  # JSON string of causes
    recommended_actions = Column(Text, nullable=True)  # JSON string of actions
    status = Column(String, default='Open')  # Open, Resolved, Ignored
    created_at = Column(DateTime, default=datetime.datetime.now)

class ResourceTag(Base):
    """Resource tag table model."""
    __tablename__ = 'resource_tags'
    
    id = Column(Integer, primary_key=True)
    resource_id = Column(String, nullable=False)
    provider = Column(String, nullable=False)
    key = Column(String, nullable=False)
    value = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now)

class CostAllocation(Base):
    """Cost allocation table model."""
    __tablename__ = 'cost_allocations'
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    cost = Column(Float, nullable=False)
    provider = Column(String, nullable=False)
    service = Column(String, nullable=False)
    business_unit = Column(String, nullable=True)
    project = Column(String, nullable=True)
    environment = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)

def init_db():
    """Initialize the database by creating all tables."""
    Base.metadata.create_all(engine)
    
def store_cost_data(df):
    """
    Store cost data DataFrame in the database.
    
    Args:
        df (pd.DataFrame): Cost data
    """
    df.to_sql('cost_data', engine, if_exists='append', index=False)
    
def store_idle_resources(df):
    """
    Store idle resources DataFrame in the database.
    
    Args:
        df (pd.DataFrame): Idle resources data
    """
    df.to_sql('idle_resources', engine, if_exists='append', index=False)
    
def get_cost_data(start_date=None, end_date=None, provider=None):
    """
    Retrieve cost data from the database with optional filters.
    
    Args:
        start_date (str, optional): Start date filter
        end_date (str, optional): End date filter
        provider (str, optional): Cloud provider filter
        
    Returns:
        pd.DataFrame: Cost data
    """
    query = "SELECT * FROM cost_data WHERE 1=1"
    params = []
    
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
        
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
        
    if provider:
        query += " AND provider = ?"
        params.append(provider)
        
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(query, conn, params=params)
    
def get_idle_resources(provider=None):
    """
    Retrieve idle resources from the database with optional filter.
    
    Args:
        provider (str, optional): Cloud provider filter
        
    Returns:
        pd.DataFrame: Idle resources data
    """
    query = "SELECT * FROM idle_resources"
    params = []
    
    if provider:
        query += " WHERE provider = ?"
        params.append(provider)
        
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(query, conn, params=params)

def create_budget(name, amount, period='monthly', provider=None, service=None):
    """
    Create a new budget.
    
    Args:
        name (str): Budget name
        amount (float): Budget amount
        period (str, optional): Budget period. Defaults to 'monthly'.
        provider (str, optional): Cloud provider filter. Defaults to None.
        service (str, optional): Service filter. Defaults to None.
        
    Returns:
        int: Budget ID
    """
    session = Session()
    budget = Budget(
        name=name,
        amount=amount,
        period=period,
        provider=provider,
        service=service
    )
    session.add(budget)
    session.commit()
    budget_id = budget.id
    session.close()
    return budget_id

def get_budgets():
    """
    Retrieve all budgets.
    
    Returns:
        pd.DataFrame: Budgets data
    """
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query("SELECT * FROM budgets", conn)

def store_budget_alert(budget_id, actual_cost, percentage):
    """
    Store a budget alert in the database.
    
    Args:
        budget_id (int): Budget ID
        actual_cost (float): Actual cost
        percentage (float): Percentage over budget
        
    Returns:
        int: Alert ID
    """
    session = Session()
    alert = BudgetAlert(
        budget_id=budget_id,
        actual_cost=actual_cost,
        percentage=percentage
    )
    session.add(alert)
    session.commit()
    alert_id = alert.id
    session.close()
    return alert_id

def get_budget_alerts(budget_id=None, notified=None):
    """
    Retrieve budget alerts with optional filters.
    
    Args:
        budget_id (int, optional): Budget ID filter
        notified (bool, optional): Notification status filter
        
    Returns:
        pd.DataFrame: Budget alerts data
    """
    query = "SELECT * FROM budget_alerts WHERE 1=1"
    params = []
    
    if budget_id is not None:
        query += " AND budget_id = ?"
        params.append(budget_id)
        
    if notified is not None:
        query += " AND notified = ?"
        params.append(1 if notified else 0)
        
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(query, conn, params=params)

def mark_alert_notified(alert_id):
    """
    Mark a budget alert as notified.
    
    Args:
        alert_id (int): Alert ID
    """
    session = Session()
    alert = session.query(BudgetAlert).filter(BudgetAlert.id == alert_id).first()
    if alert:
        alert.notified = True
        session.commit()
    session.close()

def store_recommendation(recommendation):
    """
    Store a recommendation in the database.
    
    Args:
        recommendation (dict): Recommendation data
        
    Returns:
        int: Recommendation ID
    """
    session = Session()
    
    # Convert implementation steps to JSON string if it's a list
    implementation_steps = recommendation.get('implementation_steps')
    if isinstance(implementation_steps, list):
        implementation_steps = json.dumps(implementation_steps)
    
    rec = Recommendation(
        resource_id=recommendation['resource_id'],
        resource_type=recommendation['resource_type'],
        provider=recommendation['provider'],
        recommendation_type=recommendation['recommendation_type'],
        current_config=recommendation.get('current_config'),
        recommended_config=recommendation.get('recommended_config'),
        estimated_savings=recommendation['estimated_savings'],
        confidence=recommendation['confidence'],
        justification=recommendation.get('justification'),
        implementation_steps=implementation_steps
    )
    session.add(rec)
    session.commit()
    rec_id = rec.id
    session.close()
    return rec_id

def store_recommendations(recommendations_df):
    """
    Store multiple recommendations from a DataFrame.
    
    Args:
        recommendations_df (pd.DataFrame): Recommendations data
    """
    for _, rec in recommendations_df.iterrows():
        store_recommendation(rec.to_dict())

def get_recommendations(status=None, provider=None):
    """
    Retrieve recommendations with optional filters.
    
    Args:
        status (str, optional): Status filter
        provider (str, optional): Provider filter
        
    Returns:
        pd.DataFrame: Recommendations data
    """
    query = "SELECT * FROM recommendations WHERE 1=1"
    params = []
    
    if status:
        query += " AND status = ?"
        params.append(status)
        
    if provider:
        query += " AND provider = ?"
        params.append(provider)
        
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query(query, conn, params=params)
        
        # Parse JSON strings
        if not df.empty and 'implementation_steps' in df.columns:
            df['implementation_steps'] = df['implementation_steps'].apply(
                lambda x: json.loads(x) if x else []
            )
            
        return df

def update_recommendation_status(rec_id, status):
    """
    Update the status of a recommendation.
    
    Args:
        rec_id (int): Recommendation ID
        status (str): New status
    """
    session = Session()
    rec = session.query(Recommendation).filter(Recommendation.id == rec_id).first()
    if rec:
        rec.status = status
        rec.updated_at = datetime.datetime.now()
        session.commit()
    session.close()

def store_anomaly(anomaly):
    """
    Store an anomaly detection in the database.
    
    Args:
        anomaly (dict): Anomaly data
        
    Returns:
        int: Anomaly ID
    """
    session = Session()
    
    # Convert lists to JSON strings
    possible_causes = anomaly.get('possible_causes')
    if isinstance(possible_causes, list):
        possible_causes = json.dumps(possible_causes)
        
    recommended_actions = anomaly.get('recommended_actions')
    if isinstance(recommended_actions, list):
        recommended_actions = json.dumps(recommended_actions)
    
    anom = AnomalyDetection(
        date=anomaly['date'],
        service=anomaly.get('service'),
        provider=anomaly.get('provider'),
        cost=anomaly['cost'],
        percentage_change=anomaly['percentage_change'],
        direction=anomaly['direction'],
        severity=anomaly['severity'],
        message=anomaly['message'],
        possible_causes=possible_causes,
        recommended_actions=recommended_actions
    )
    session.add(anom)
    session.commit()
    anom_id = anom.id
    session.close()
    return anom_id

def store_anomalies(anomalies):
    """
    Store multiple anomalies.
    
    Args:
        anomalies (list): List of anomaly dictionaries
    """
    for anomaly in anomalies:
        store_anomaly(anomaly)

def get_anomalies(status=None, severity=None, provider=None):
    """
    Retrieve anomalies with optional filters.
    
    Args:
        status (str, optional): Status filter
        severity (str, optional): Severity filter
        provider (str, optional): Provider filter
        
    Returns:
        pd.DataFrame: Anomalies data
    """
    query = "SELECT * FROM anomaly_detections WHERE 1=1"
    params = []
    
    if status:
        query += " AND status = ?"
        params.append(status)
        
    if severity:
        query += " AND severity = ?"
        params.append(severity)
        
    if provider:
        query += " AND provider = ?"
        params.append(provider)
        
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query(query, conn, params=params)
        
        # Parse JSON strings
        if not df.empty:
            if 'possible_causes' in df.columns:
                df['possible_causes'] = df['possible_causes'].apply(
                    lambda x: json.loads(x) if x else []
                )
            if 'recommended_actions' in df.columns:
                df['recommended_actions'] = df['recommended_actions'].apply(
                    lambda x: json.loads(x) if x else []
                )
            
        return df

def update_anomaly_status(anomaly_id, status):
    """
    Update the status of an anomaly.
    
    Args:
        anomaly_id (int): Anomaly ID
        status (str): New status
    """
    session = Session()
    anomaly = session.query(AnomalyDetection).filter(AnomalyDetection.id == anomaly_id).first()
    if anomaly:
        anomaly.status = status
        session.commit()
    session.close()

def store_resource_tag(resource_id, provider, key, value):
    """
    Store a resource tag in the database.
    
    Args:
        resource_id (str): Resource ID
        provider (str): Cloud provider
        key (str): Tag key
        value (str): Tag value
        
    Returns:
        int: Tag ID
    """
    session = Session()
    tag = ResourceTag(
        resource_id=resource_id,
        provider=provider,
        key=key,
        value=value
    )
    session.add(tag)
    session.commit()
    tag_id = tag.id
    session.close()
    return tag_id

def get_resource_tags(resource_id=None, provider=None, key=None):
    """
    Retrieve resource tags with optional filters.
    
    Args:
        resource_id (str, optional): Resource ID filter
        provider (str, optional): Provider filter
        key (str, optional): Tag key filter
        
    Returns:
        pd.DataFrame: Resource tags data
    """
    query = "SELECT * FROM resource_tags WHERE 1=1"
    params = []
    
    if resource_id:
        query += " AND resource_id = ?"
        params.append(resource_id)
        
    if provider:
        query += " AND provider = ?"
        params.append(provider)
        
    if key:
        query += " AND key = ?"
        params.append(key)
        
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(query, conn, params=params)

def store_cost_allocation(date, cost, provider, service, business_unit=None, project=None, environment=None):
    """
    Store a cost allocation in the database.
    
    Args:
        date (str): Date in YYYY-MM-DD format
        cost (float): Cost amount
        provider (str): Cloud provider
        service (str): Service name
        business_unit (str, optional): Business unit
        project (str, optional): Project
        environment (str, optional): Environment
        
    Returns:
        int: Cost allocation ID
    """
    session = Session()
    allocation = CostAllocation(
        date=date,
        cost=cost,
        provider=provider,
        service=service,
        business_unit=business_unit,
        project=project,
        environment=environment
    )
    session.add(allocation)
    session.commit()
    allocation_id = allocation.id
    session.close()
    return allocation_id

def get_cost_allocations(start_date=None, end_date=None, business_unit=None, project=None):
    """
    Retrieve cost allocations with optional filters.
    
    Args:
        start_date (str, optional): Start date filter
        end_date (str, optional): End date filter
        business_unit (str, optional): Business unit filter
        project (str, optional): Project filter
        
    Returns:
        pd.DataFrame: Cost allocations data
    """
    query = "SELECT * FROM cost_allocations WHERE 1=1"
    params = []
    
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
        
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
        
    if business_unit:
        query += " AND business_unit = ?"
        params.append(business_unit)
        
    if project:
        query += " AND project = ?"
        params.append(project)
        
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(query, conn, params=params)

# Initialize database if this script is run directly
if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")