"""
Cost forecasting module using Facebook Prophet.
"""

import pandas as pd
import numpy as np
from prophet import Prophet
import matplotlib.pyplot as plt

class CostForecaster:
    """Forecasts cloud costs using time series analysis."""
    
    def __init__(self, forecast_days=30):
        """
        Initialize the forecaster.
        
        Args:
            forecast_days (int, optional): Number of days to forecast. Defaults to 30.
        """
        self.forecast_days = forecast_days
        self.model = None
        self.forecast = None
        
    def prepare_data(self, df):
        """
        Prepare data for Prophet model.
        
        Args:
            df (pd.DataFrame): Cost data with 'date' and 'cost' columns
            
        Returns:
            pd.DataFrame: DataFrame formatted for Prophet
        """
        # Prophet requires columns named 'ds' and 'y'
        prophet_df = df[['date', 'cost']].copy()
        prophet_df.columns = ['ds', 'y']
        return prophet_df
        
    def train(self, df):
        """
        Train the forecasting model.
        
        Args:
            df (pd.DataFrame): Cost data with 'date' and 'cost' columns
            
        Returns:
            self: For method chaining
        """
        prophet_df = self.prepare_data(df)
        
        # Initialize and fit the model
        self.model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            seasonality_mode='multiplicative'
        )
        self.model.fit(prophet_df)
        
        return self
        
    def predict(self):
        """
        Generate forecast for future periods.
        
        Returns:
            pd.DataFrame: Forecast results
        """
        if self.model is None:
            raise ValueError("Model must be trained before prediction")
            
        # Create future dataframe
        future = self.model.make_future_dataframe(periods=self.forecast_days)
        
        # Generate forecast
        self.forecast = self.model.predict(future)
        
        return self.forecast
        
    def plot_forecast(self, save_path=None):
        """
        Plot the forecast results.
        
        Args:
            save_path (str, optional): Path to save the plot. Defaults to None.
            
        Returns:
            matplotlib.figure.Figure: The forecast plot
        """
        if self.forecast is None:
            raise ValueError("Must run predict() before plotting")
            
        fig = self.model.plot(self.forecast)
        
        if save_path:
            plt.savefig(save_path)
            
        return fig
        
    def get_monthly_forecast(self):
        """
        Aggregate forecast by month.
        
        Returns:
            pd.DataFrame: Monthly forecast
        """
        if self.forecast is None:
            raise ValueError("Must run predict() before getting monthly forecast")
            
        # Extract date and forecast columns
        monthly_forecast = self.forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].copy()
        
        # Convert to datetime and extract month
        monthly_forecast['ds'] = pd.to_datetime(monthly_forecast['ds'])
        monthly_forecast['month'] = monthly_forecast['ds'].dt.strftime('%Y-%m')
        
        # Group by month and sum
        monthly_agg = monthly_forecast.groupby('month').agg({
            'yhat': 'sum',
            'yhat_lower': 'sum',
            'yhat_upper': 'sum'
        }).reset_index()
        
        return monthly_agg