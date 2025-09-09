"""
Weather service for CleanSky AI
"""
import requests
import structlog
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

from config.config import Config
from backend.utils.data_processor import DataCache

logger = structlog.get_logger()

class WeatherService:
    """Service for fetching weather data from external APIs"""
    
    def __init__(self):
        self.api_key = Config.OPENWEATHER_API_KEY
        self.base_url = Config.WEATHER_API_URL
        self.cache = DataCache()
        
        # Session for persistent connections
        self.session = requests.Session()
        self.session.timeout = 30
    
    def get_current_weather(
        self, 
        lat: float, 
        lon: float, 
        units: str = 'metric'
    ) -> Optional[Dict[str, Any]]:
        """
        Get current weather conditions for a location
        
        Args:
            lat: Latitude
            lon: Longitude  
            units: Temperature units ('metric', 'imperial', 'standard')
            
        Returns:
            Dict with current weather data
        """
        try:
            # Generate cache key
            cache_key = f"current_weather_{lat}_{lon}_{units}"
            
            # Check cache first (15 minute TTL for weather data)
            cached_data = self.cache.get(cache_key)
            if cached_data:
                logger.info("Returning cached weather data")
                return cached_data
            
            # Build API request
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': units
            }
            
            if not self.api_key:
                # Return mock data if no API key configured
                logger.warning("No OpenWeather API key configured, returning mock data")
                return self._get_mock_current_weather(lat, lon, units)
            
            response = self.session.get(
                f"{self.base_url}/weather",
                params=params
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Process and format the response
            processed_data = self._process_current_weather(data, units)
            
            # Cache the results
            self.cache.set(cache_key, processed_data, expire=900)  # 15 minutes
            
            logger.info(f"Fetched current weather for {lat}, {lon}")
            return processed_data
            
        except requests.RequestException as e:
            logger.error(f"Error fetching current weather: {str(e)}")
            # Return mock data as fallback
            return self._get_mock_current_weather(lat, lon, units)
        
        except Exception as e:
            logger.error(f"Unexpected error in get_current_weather: {str(e)}")
            return None
    
    def get_forecast(
        self, 
        lat: float, 
        lon: float, 
        units: str = 'metric',
        days: int = 5
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get weather forecast for a location
        
        Args:
            lat: Latitude
            lon: Longitude
            units: Temperature units
            days: Number of forecast days (1-5)
            
        Returns:
            List of forecast data points
        """
        try:
            cache_key = f"forecast_{lat}_{lon}_{units}_{days}"
            
            # Check cache first
            cached_data = self.cache.get(cache_key)
            if cached_data:
                logger.info("Returning cached forecast data")
                return cached_data
            
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': units,
                'cnt': min(days * 8, 40)  # 3-hour intervals, max 5 days
            }
            
            if not self.api_key:
                logger.warning("No OpenWeather API key configured, returning mock forecast")
                return self._get_mock_forecast(lat, lon, units, days)
            
            response = self.session.get(
                f"{self.base_url}/forecast",
                params=params
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Process forecast data
            forecast_data = self._process_forecast_data(data, units, days)
            
            # Cache results
            self.cache.set(cache_key, forecast_data, expire=1800)  # 30 minutes
            
            logger.info(f"Fetched {days}-day forecast for {lat}, {lon}")
            return forecast_data
            
        except requests.RequestException as e:
            logger.error(f"Error fetching forecast: {str(e)}")
            return self._get_mock_forecast(lat, lon, units, days)
            
        except Exception as e:
            logger.error(f"Unexpected error in get_forecast: {str(e)}")
            return None
    
    def get_air_pollution(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        Get air pollution data from OpenWeather API
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dict with air pollution data
        """
        try:
            cache_key = f"air_pollution_{lat}_{lon}"
            
            cached_data = self.cache.get(cache_key)
            if cached_data:
                return cached_data
            
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key
            }
            
            if not self.api_key:
                return None
            
            response = self.session.get(
                f"{self.base_url}/air_pollution",
                params=params
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Process air pollution data
            processed_data = self._process_air_pollution_data(data)
            
            # Cache results
            self.cache.set(cache_key, processed_data, expire=1800)  # 30 minutes
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error fetching air pollution data: {str(e)}")
            return None
    
    def _process_current_weather(self, data: Dict, units: str) -> Dict[str, Any]:
        """Process raw weather API response"""
        temp_unit = '°C' if units == 'metric' else '°F' if units == 'imperial' else 'K'
        speed_unit = 'm/s' if units == 'metric' else 'mph' if units == 'imperial' else 'm/s'
        
        return {
            'temperature': data['main']['temp'],
            'temperature_unit': temp_unit,
            'feels_like': data['main']['feels_like'],
            'humidity': data['main']['humidity'],
            'pressure': data['main']['pressure'],
            'visibility': data.get('visibility', 0) / 1000,  # Convert to km
            'wind_speed': data.get('wind', {}).get('speed', 0),
            'wind_speed_unit': speed_unit,
            'wind_direction': data.get('wind', {}).get('deg', 0),
            'wind_gust': data.get('wind', {}).get('gust'),
            'cloudiness': data['clouds']['all'],
            'conditions': data['weather'][0]['main'],
            'description': data['weather'][0]['description'],
            'icon': data['weather'][0]['icon'],
            'sunrise': datetime.fromtimestamp(data['sys']['sunrise']).isoformat(),
            'sunset': datetime.fromtimestamp(data['sys']['sunset']).isoformat(),
            'location': {
                'name': data.get('name', 'Unknown'),
                'country': data['sys']['country'],
                'lat': data['coord']['lat'],
                'lon': data['coord']['lon']
            },
            'timestamp': datetime.fromtimestamp(data['dt']).isoformat(),
            'data_source': 'OpenWeather'
        }
    
    def _process_forecast_data(self, data: Dict, units: str, days: int) -> List[Dict[str, Any]]:
        """Process forecast API response"""
        temp_unit = '°C' if units == 'metric' else '°F' if units == 'imperial' else 'K'
        speed_unit = 'm/s' if units == 'metric' else 'mph' if units == 'imperial' else 'm/s'
        
        forecast_list = []
        
        for item in data['list'][:days * 8]:  # 3-hour intervals
            forecast_point = {
                'timestamp': datetime.fromtimestamp(item['dt']).isoformat(),
                'temperature': item['main']['temp'],
                'temperature_unit': temp_unit,
                'feels_like': item['main']['feels_like'],
                'humidity': item['main']['humidity'],
                'pressure': item['main']['pressure'],
                'wind_speed': item.get('wind', {}).get('speed', 0),
                'wind_speed_unit': speed_unit,
                'wind_direction': item.get('wind', {}).get('deg', 0),
                'cloudiness': item['clouds']['all'],
                'conditions': item['weather'][0]['main'],
                'description': item['weather'][0]['description'],
                'icon': item['weather'][0]['icon'],
                'precipitation_probability': item.get('pop', 0) * 100,
                'rain_3h': item.get('rain', {}).get('3h', 0),
                'snow_3h': item.get('snow', {}).get('3h', 0)
            }
            forecast_list.append(forecast_point)
        
        return forecast_list
    
    def _process_air_pollution_data(self, data: Dict) -> Dict[str, Any]:
        """Process air pollution API response"""
        if not data.get('list'):
            return {}
        
        pollution_data = data['list'][0]  # Current pollution data
        components = pollution_data.get('components', {})
        
        return {
            'aqi': pollution_data['main']['aqi'],
            'components': {
                'co': components.get('co', 0),  # Carbon monoxide (μg/m³)
                'no': components.get('no', 0),   # Nitric oxide (μg/m³)
                'no2': components.get('no2', 0), # Nitrogen dioxide (μg/m³)
                'o3': components.get('o3', 0),   # Ozone (μg/m³)
                'so2': components.get('so2', 0), # Sulfur dioxide (μg/m³)
                'pm2_5': components.get('pm2_5', 0), # PM2.5 (μg/m³)
                'pm10': components.get('pm10', 0),   # PM10 (μg/m³)
                'nh3': components.get('nh3', 0)      # Ammonia (μg/m³)
            },
            'timestamp': datetime.fromtimestamp(pollution_data['dt']).isoformat(),
            'data_source': 'OpenWeather'
        }
    
    def _get_mock_current_weather(self, lat: float, lon: float, units: str) -> Dict[str, Any]:
        """Generate mock current weather data"""
        import random
        
        temp_unit = '°C' if units == 'metric' else '°F' if units == 'imperial' else 'K'
        
        # Base temperature depending on units
        if units == 'metric':
            base_temp = random.uniform(15, 30)
        elif units == 'imperial':
            base_temp = random.uniform(60, 85)
        else:  # standard (Kelvin)
            base_temp = random.uniform(288, 303)
        
        conditions = ['Clear', 'Partly Cloudy', 'Cloudy', 'Light Rain', 'Rain', 'Thunderstorm']
        
        return {
            'temperature': round(base_temp, 1),
            'temperature_unit': temp_unit,
            'feels_like': round(base_temp + random.uniform(-3, 5), 1),
            'humidity': random.randint(30, 80),
            'pressure': random.randint(1000, 1030),
            'visibility': round(random.uniform(5, 25), 1),
            'wind_speed': round(random.uniform(0, 15), 1),
            'wind_speed_unit': 'm/s' if units == 'metric' else 'mph',
            'wind_direction': random.randint(0, 359),
            'wind_gust': round(random.uniform(0, 20), 1) if random.random() > 0.7 else None,
            'cloudiness': random.randint(0, 100),
            'conditions': random.choice(conditions),
            'description': random.choice(['clear sky', 'few clouds', 'broken clouds', 'light rain']),
            'icon': '01d',
            'sunrise': '06:30:00',
            'sunset': '19:45:00',
            'location': {
                'name': 'Demo Location',
                'country': 'US',
                'lat': lat,
                'lon': lon
            },
            'timestamp': datetime.utcnow().isoformat(),
            'data_source': 'Mock Data'
        }
    
    def _get_mock_forecast(self, lat: float, lon: float, units: str, days: int) -> List[Dict[str, Any]]:
        """Generate mock forecast data"""
        import random
        
        forecast = []
        current_time = datetime.utcnow()
        
        temp_unit = '°C' if units == 'metric' else '°F' if units == 'imperial' else 'K'
        
        for hour in range(days * 24):  # Hourly forecast
            timestamp = current_time + timedelta(hours=hour)
            
            # Base temperature with daily and hourly variation
            if units == 'metric':
                base_temp = 20 + 10 * random.sin(hour * 3.14159 / 12) + random.uniform(-5, 5)
            elif units == 'imperial':  
                base_temp = 68 + 18 * random.sin(hour * 3.14159 / 12) + random.uniform(-9, 9)
            else:
                base_temp = 293 + 10 * random.sin(hour * 3.14159 / 12) + random.uniform(-5, 5)
            
            forecast_point = {
                'timestamp': timestamp.isoformat(),
                'temperature': round(base_temp, 1),
                'temperature_unit': temp_unit,
                'feels_like': round(base_temp + random.uniform(-2, 3), 1),
                'humidity': random.randint(40, 85),
                'pressure': random.randint(1005, 1025),
                'wind_speed': round(random.uniform(2, 12), 1),
                'wind_speed_unit': 'm/s' if units == 'metric' else 'mph',
                'wind_direction': random.randint(0, 359),
                'cloudiness': random.randint(10, 90),
                'conditions': random.choice(['Clear', 'Partly Cloudy', 'Cloudy', 'Light Rain']),
                'description': 'Mock forecast data',
                'icon': '02d',
                'precipitation_probability': random.randint(0, 30),
                'rain_3h': random.uniform(0, 2) if random.random() > 0.8 else 0,
                'snow_3h': 0
            }
            forecast.append(forecast_point)
        
        return forecast
