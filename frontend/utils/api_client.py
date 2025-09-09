"""
API Client for CleanSky AI Frontend
"""
import requests
import json
from typing import Dict, List, Optional, Any
import structlog
from datetime import datetime, timedelta
import streamlit as st

logger = structlog.get_logger()

class APIClient:
    """Client for communicating with CleanSky AI backend API"""
    
    def __init__(self, base_url: str = "http://localhost:5000/api/v1"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        # Set timeout for all requests
        self.timeout = 30
    
    def get_health_status(self) -> Dict[str, Any]:
        """Check API health status"""
        try:
            response = self.session.get(
                f"{self.base_url.replace('/api/v1', '')}/health",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Health check failed: {str(e)}")
            return {'status': 'unhealthy', 'error': str(e)}
    
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def get_air_quality(
        self, 
        lat: float, 
        lon: float, 
        radius: int = 25,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get air quality data for a location"""
        try:
            params = {
                'lat': lat,
                'lon': lon,
                'radius': radius
            }
            
            if start_date:
                params['start_date'] = start_date
            if end_date:
                params['end_date'] = end_date
            
            response = self.session.get(
                f"{self.base_url}/air-quality",
                params=params,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch air quality data: {str(e)}")
            # Return mock data for development/demo
            return self._get_mock_air_quality_data(lat, lon)
    
    @st.cache_data(ttl=900)  # Cache for 15 minutes
    def get_tempo_data(
        self,
        lat: float,
        lon: float,
        parameters: List[str] = ['NO2'],
        date: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get TEMPO satellite data"""
        try:
            params = {
                'lat': lat,
                'lon': lon,
                'parameter': parameters
            }
            
            if date:
                params['date'] = date
            
            response = self.session.get(
                f"{self.base_url}/tempo",
                params=params,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch TEMPO data: {str(e)}")
            # Return mock data for development/demo
            return self._get_mock_tempo_data(lat, lon, parameters)
    
    @st.cache_data(ttl=600)  # Cache for 10 minutes
    def get_weather(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Get weather data for a location"""
        try:
            params = {'lat': lat, 'lon': lon}
            
            response = self.session.get(
                f"{self.base_url}/weather",
                params=params,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            data = response.json()
            return data.get('data', {})
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch weather data: {str(e)}")
            # Return mock weather data
            return self._get_mock_weather_data()
    
    def get_forecast(
        self,
        lat: float,
        lon: float,
        forecast_hours: int = 24
    ) -> Optional[Dict[str, Any]]:
        """Get air quality forecast"""
        try:
            payload = {
                'lat': lat,
                'lon': lon,
                'forecast_hours': forecast_hours
            }
            
            response = self.session.post(
                f"{self.base_url}/air-quality",
                json=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch forecast: {str(e)}")
            return self._get_mock_forecast_data(forecast_hours)
    
    def send_notification(
        self,
        user_id: int,
        message: str,
        notification_type: str = 'alert',
        channels: List[str] = ['email']
    ) -> bool:
        """Send notification to user"""
        try:
            payload = {
                'user_id': user_id,
                'message': message,
                'type': notification_type,
                'channels': channels
            }
            
            response = self.session.post(
                f"{self.base_url}/notifications",
                json=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return True
            
        except requests.RequestException as e:
            logger.error(f"Failed to send notification: {str(e)}")
            return False
    
    def _get_mock_air_quality_data(self, lat: float, lon: float) -> Dict[str, Any]:
        """Generate mock air quality data for development"""
        import random
        import numpy as np
        
        # Generate realistic AQI based on location (higher for urban areas)
        base_aqi = random.uniform(30, 120)
        
        # Add some location-based variation
        if abs(lat - 34.0522) < 2 and abs(lon + 118.2437) < 2:  # LA area
            base_aqi += random.uniform(20, 50)
        elif abs(lat - 40.7128) < 2 and abs(lon + 74.0060) < 2:  # NYC area
            base_aqi += random.uniform(15, 40)
        
        aqi = min(500, max(0, base_aqi))
        
        # Determine category
        if aqi <= 50:
            category = "Good"
        elif aqi <= 100:
            category = "Moderate"
        elif aqi <= 150:
            category = "Unhealthy for Sensitive Groups"
        elif aqi <= 200:
            category = "Unhealthy"
        elif aqi <= 300:
            category = "Very Unhealthy"
        else:
            category = "Hazardous"
        
        pollutants = ["PM2.5", "O3", "NO2", "SO2", "CO"]
        primary_pollutant = random.choice(pollutants)
        
        # Generate station data
        stations = []
        for i in range(random.randint(3, 8)):
            station_aqi = aqi + random.uniform(-20, 20)
            station_aqi = min(500, max(0, station_aqi))
            
            stations.append({
                'aqi': round(station_aqi),
                'primary_pollutant': random.choice(pollutants),
                'distance_km': round(random.uniform(1, 25), 1),
                'timestamp': datetime.now().isoformat()
            })
        
        return {
            'status': 'success',
            'location': f"{lat},{lon}",
            'timestamp': datetime.now().isoformat(),
            'current_summary': {
                'average_aqi': round(aqi * 0.9, 1),
                'maximum_aqi': round(aqi),
                'category': category,
                'primary_pollutant': primary_pollutant,
                'last_updated': datetime.now().isoformat(),
                'station_count': len(stations)
            },
            'stations': stations
        }
    
    def _get_mock_tempo_data(self, lat: float, lon: float, parameters: List[str]) -> Dict[str, Any]:
        """Generate mock TEMPO satellite data"""
        import random
        
        data_points = []
        statistics = {}
        
        for param in parameters:
            # Generate hourly data for the day
            for hour in range(8, 20):  # Daytime hours
                timestamp = datetime.now().replace(hour=hour, minute=0, second=0, microsecond=0)
                
                # Parameter-specific value ranges
                if param == 'NO2':
                    value = random.uniform(1e15, 3e15)
                    units = 'molecules/cm²'
                elif param == 'O3':
                    value = random.uniform(250, 400)
                    units = 'Dobson Units'
                elif param == 'HCHO':
                    value = random.uniform(5e14, 1.5e15)
                    units = 'molecules/cm²'
                elif param == 'SO2':
                    value = random.uniform(5e14, 2e15)
                    units = 'molecules/cm²'
                else:
                    value = random.uniform(1e14, 1e16)
                    units = 'molecules/cm²'
                
                data_points.append({
                    'timestamp': timestamp.isoformat(),
                    'lat': lat,
                    'lon': lon,
                    'parameter': param,
                    'value': value,
                    'units': units,
                    'quality': random.choice(['good', 'good', 'good', 'moderate'])  # Mostly good quality
                })
            
            # Generate statistics
            param_values = [dp['value'] for dp in data_points if dp['parameter'] == param]
            if param_values:
                statistics[param] = {
                    'count': len(param_values),
                    'min': min(param_values),
                    'max': max(param_values),
                    'mean': sum(param_values) / len(param_values),
                    'median': sorted(param_values)[len(param_values) // 2]
                }
        
        return {
            'status': 'success',
            'query': {
                'parameters': parameters,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'location': {'type': 'point', 'lat': lat, 'lon': lon}
            },
            'timestamp': datetime.now().isoformat(),
            'data': data_points,
            'statistics': statistics
        }
    
    def _get_mock_weather_data(self) -> Dict[str, Any]:
        """Generate mock weather data"""
        import random
        
        return {
            'temperature': random.uniform(15, 30),  # Celsius
            'humidity': random.uniform(30, 80),
            'wind_speed': random.uniform(1, 15),
            'wind_direction': random.uniform(0, 360),
            'pressure': random.uniform(1000, 1030),
            'visibility': random.uniform(5, 25),
            'conditions': random.choice(['Clear', 'Partly Cloudy', 'Cloudy', 'Light Rain'])
        }
    
    def _get_mock_forecast_data(self, forecast_hours: int) -> Dict[str, Any]:
        """Generate mock forecast data"""
        import random
        
        forecast_points = []
        base_aqi = random.uniform(40, 100)
        
        for hour in range(forecast_hours):
            timestamp = datetime.now() + timedelta(hours=hour + 1)
            
            # Add some realistic variation
            hour_variation = 20 * np.sin(hour * np.pi / 12)  # Daily pattern
            trend = -0.5 * hour  # Slight improvement over time
            noise = random.uniform(-10, 10)
            
            aqi = max(0, base_aqi + hour_variation + trend + noise)
            
            forecast_points.append({
                'timestamp': timestamp.isoformat(),
                'aqi': round(aqi, 1),
                'primary_pollutant': random.choice(['PM2.5', 'O3', 'NO2']),
                'confidence': random.uniform(0.7, 0.95)
            })
        
        recommendations = [
            "Monitor air quality throughout the day",
            "Consider indoor activities during peak pollution hours",
            "Use air purifiers if available"
        ]
        
        return {
            'status': 'success',
            'forecast': forecast_points,
            'health_recommendations': recommendations
        }
