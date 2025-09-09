"""
Machine Learning service for air quality forecasting
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import structlog
import pickle
import os
from pathlib import Path

# ML libraries
import xgboost as xgb
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib

from config.config import Config
from backend.services.weather_service import WeatherService
from backend.utils.data_processor import DataCache

logger = structlog.get_logger()

class MLService:
    """Machine Learning service for air quality prediction"""
    
    def __init__(self):
        self.weather_service = WeatherService()
        self.cache = DataCache()
        
        # Model storage paths
        self.model_dir = Path("data/models")
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize models
        self.aqi_model = None
        self.scaler = StandardScaler()
        self.feature_columns = []
        self.model_metadata = {}
        
        # Load existing model if available
        self._load_model()
        
        # If no model exists, train a basic one
        if self.aqi_model is None:
            logger.info("No existing model found, training new model")
            self._train_initial_model()
    
    def predict_air_quality(
        self,
        lat: float,
        lon: float,
        forecast_hours: int = 24,
        historical_data: Optional[pd.DataFrame] = None
    ) -> List[Dict[str, Any]]:
        """
        Predict air quality for specified location and time horizon
        
        Args:
            lat: Latitude
            lon: Longitude
            forecast_hours: Number of hours to forecast (1-72)
            historical_data: Recent historical data for context
            
        Returns:
            List of forecast data points
        """
        try:
            # Validate inputs
            if not (1 <= forecast_hours <= 72):
                raise ValueError("Forecast hours must be between 1 and 72")
            
            logger.info(f"Generating {forecast_hours}-hour forecast for {lat}, {lon}")
            
            # Get weather forecast for ML features
            weather_forecast = self.weather_service.get_forecast(
                lat, lon, units='metric', days=min(5, (forecast_hours + 23) // 24)
            )
            
            if not weather_forecast:
                logger.warning("No weather forecast available, using mock data")
                weather_forecast = self._generate_mock_weather_forecast(forecast_hours)
            
            # Generate features for prediction
            feature_data = self._prepare_forecast_features(
                lat, lon, weather_forecast, historical_data
            )
            
            # Make predictions
            if self.aqi_model and len(feature_data) > 0:
                predictions = self._predict_with_model(feature_data[:forecast_hours])
            else:
                logger.warning("No trained model available, using statistical forecast")
                predictions = self._statistical_forecast(
                    lat, lon, forecast_hours, historical_data
                )
            
            # Format predictions
            forecast_data = self._format_predictions(predictions, weather_forecast)
            
            logger.info(f"Generated forecast with {len(forecast_data)} data points")
            return forecast_data
            
        except Exception as e:
            logger.error(f"Error generating air quality forecast: {str(e)}")
            # Return fallback statistical forecast
            return self._statistical_forecast(lat, lon, forecast_hours, historical_data)
    
    def train_model(
        self, 
        training_data: pd.DataFrame,
        target_column: str = 'aqi',
        save_model: bool = True
    ) -> Dict[str, Any]:
        """
        Train or retrain the air quality prediction model
        
        Args:
            training_data: DataFrame with historical air quality and weather data
            target_column: Column name for target variable (AQI)
            save_model: Whether to save the trained model
            
        Returns:
            Dict with training metrics and model info
        """
        try:
            logger.info(f"Training model with {len(training_data)} data points")
            
            # Prepare features
            X, y = self._prepare_training_features(training_data, target_column)
            
            if len(X) == 0:
                raise ValueError("No valid training features generated")
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, shuffle=True
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train XGBoost model
            model_params = {
                'n_estimators': 100,
                'max_depth': 6,
                'learning_rate': 0.1,
                'subsample': 0.8,
                'colsample_bytree': 0.8,
                'random_state': 42
            }
            
            self.aqi_model = xgb.XGBRegressor(**model_params)
            self.aqi_model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            y_pred = self.aqi_model.predict(X_test_scaled)
            
            metrics = {
                'mse': mean_squared_error(y_test, y_pred),
                'mae': mean_absolute_error(y_test, y_pred),
                'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
                'r2': r2_score(y_test, y_pred),
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'features': len(X.columns)
            }
            
            # Cross-validation
            cv_scores = cross_val_score(
                self.aqi_model, X_train_scaled, y_train, cv=5, scoring='neg_mean_squared_error'
            )
            metrics['cv_rmse'] = np.sqrt(-cv_scores.mean())
            metrics['cv_rmse_std'] = np.sqrt(cv_scores.std())
            
            # Store feature columns and metadata
            self.feature_columns = list(X.columns)
            self.model_metadata = {
                'trained_at': datetime.utcnow().isoformat(),
                'model_type': 'XGBRegressor',
                'feature_columns': self.feature_columns,
                'metrics': metrics,
                'model_params': model_params
            }
            
            if save_model:
                self._save_model()
            
            logger.info(f"Model training completed. RMSE: {metrics['rmse']:.2f}, R²: {metrics['r2']:.3f}")
            
            return {
                'status': 'success',
                'metrics': metrics,
                'model_info': {
                    'type': 'XGBRegressor',
                    'features': len(self.feature_columns),
                    'trained_at': self.model_metadata['trained_at']
                }
            }
            
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        if self.aqi_model is None:
            return {
                'status': 'no_model',
                'message': 'No trained model available'
            }
        
        return {
            'status': 'ready',
            'metadata': self.model_metadata,
            'feature_count': len(self.feature_columns),
            'model_type': type(self.aqi_model).__name__
        }
    
    def _prepare_forecast_features(
        self,
        lat: float,
        lon: float,
        weather_forecast: List[Dict],
        historical_data: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """Prepare features for forecasting"""
        try:
            features_list = []
            
            for i, weather_point in enumerate(weather_forecast):
                timestamp = pd.to_datetime(weather_point['timestamp'])
                
                # Basic features
                features = {
                    'lat': lat,
                    'lon': lon,
                    'hour': timestamp.hour,
                    'day_of_week': timestamp.weekday(),
                    'month': timestamp.month,
                    'is_weekend': int(timestamp.weekday() >= 5),
                    'temperature': weather_point.get('temperature', 20),
                    'humidity': weather_point.get('humidity', 50),
                    'pressure': weather_point.get('pressure', 1013),
                    'wind_speed': weather_point.get('wind_speed', 5),
                    'wind_direction': weather_point.get('wind_direction', 0),
                    'cloudiness': weather_point.get('cloudiness', 50)
                }
                
                # Add time-based features
                features.update(self._extract_time_features(timestamp))
                
                # Add historical context if available
                if historical_data is not None and len(historical_data) > 0:
                    features.update(self._extract_historical_features(historical_data, i))
                
                features_list.append(features)
            
            return pd.DataFrame(features_list)
            
        except Exception as e:
            logger.error(f"Error preparing forecast features: {str(e)}")
            return pd.DataFrame()
    
    def _prepare_training_features(
        self, 
        data: pd.DataFrame, 
        target_column: str
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare features for model training"""
        try:
            # Ensure timestamp column exists
            if 'timestamp' not in data.columns:
                data['timestamp'] = pd.to_datetime(data.index)
            
            data['timestamp'] = pd.to_datetime(data['timestamp'])
