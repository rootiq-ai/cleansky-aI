"""
Ground station data service for EPA and AirNow integration
"""
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import structlog

from config.config import Config
from backend.utils.data_processor import DataCache

logger = structlog.get_logger()

class GroundStationService:
    """Service for fetching ground-based air quality monitoring data"""
    
    def __init__(self):
        self.epa_api_key = Config.EPA_API_KEY
        self.epa_base_url = Config.EPA_AQS_URL
        self.airnow_base_url = Config.AIRNOW_API_URL
        self.cache = DataCache()
        
        # Session for API requests
        self.session = requests.Session()
        self.session.timeout = 30
        
        # Parameter codes for EPA AQS API
        self.epa_parameters = {
            'ozone': '44201',
            'so2': '42401', 
            'co': '42101',
            'no2': '42602',
            'pm25': '88101',
            'pm10': '81102'
        }
    
    def get_air_quality_data(
        self,
        location: str,
        radius: int = 25,
        start_date: str = None,
        end_date: str = None
    ) -> List[Dict[str, Any]]:
        """
        Get air quality data from ground monitoring stations
        
        Args:
            location: "lat,lon" string or location name
            radius: Search radius in kilometers
            start_date: Start date in ISO format
            end_date: End date in ISO format
            
        Returns:
            List of air quality measurements from nearby stations
        """
        try:
            # Parse location
            if ',' in location:
                lat, lon = map(float, location.split(','))
            else:
                # For named locations, would need geocoding service
                # Using default coordinates for demo
                lat, lon = 39.8283, -98.5795
            
            # Generate cache key
            cache_key = f"ground_stations_{lat}_{lon}_{radius}_{start_date}_{end_date}"
            
            # Check cache
            cached_data = self.cache.get(cache_key)
            if cached_data:
                logger.info("Returning cached ground station data")
                return cached_data
            
            # Get data from multiple sources
            station_data = []
            
            # Try AirNow API first (real-time data)
            airnow_data = self._get_airnow_data(lat, lon, radius)
            if airnow_data:
                station_data.extend(airnow_data)
            
            # Try EPA AQS API for historical data
            if start_date and end_date:
                epa_data = self._get_epa_aqs_data(lat, lon, radius, start_date, end_date)
                if epa_data:
                    station_data.extend(epa_data)
            
            # If no real data available, generate mock data
            if not station_data:
                logger.warning("No ground station data available, generating mock data")
                station_data = self._generate_mock_station_data(lat, lon, radius)
            
            # Process and validate data
            processed_data = self._process_station_data(station_data)
            
            # Cache results
            self.cache.set(cache_key, processed_data, expire=1800)  # 30 minutes
            
            logger.info(f"Retrieved data from {len(processed_data)} ground stations")
            return processed_data
            
        except Exception as e:
            logger.error(f"Error fetching ground station data: {str(e)}")
            # Return mock data as fallback
            return self._generate_mock_station_data(39.8283, -98.5795, radius)
    
    def get_historical_data(
        self,
        lat: float,
        lon: float,
        days_back: int = 7,
        parameters: List[str] = None
    ) -> pd.DataFrame:
        """
        Get historical air quality data for ML model training
        
        Args:
            lat: Latitude
            lon: Longitude
            days_back: Number of days of historical data
            parameters: List of parameters to fetch
            
        Returns:
            DataFrame with historical air quality data
        """
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)
            
            # Get station data
            station_data = self.get_air_quality_data(
                f"{lat},{lon}",
                radius=50,  # Larger radius for historical data
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat()
            )
            
            # Convert to DataFrame
            if station_data:
                df = pd.DataFrame(station_data)
                
                # Convert timestamp to datetime
                if 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df = df.sort_values('timestamp')
                
                return df
            else:
                # Return mock historical data
                return self._generate_mock_historical_data(lat, lon, days_back)
                
        except Exception as e:
            logger.error(f"Error fetching historical data: {str(e)}")
            return self._generate_mock_historical_data(lat, lon, days_back)
    
    def _get_airnow_data(self, lat: float, lon: float, radius: int) -> List[Dict]:
        """Fetch data from AirNow API"""
        try:
            # AirNow API requires API key and specific format
            if not hasattr(Config, 'AIRNOW_API_KEY') or not Config.AIRNOW_API_KEY:
                return []
            
            params = {
                'format': 'application/json',
                'latitude': lat,
                'longitude': lon,
                'distance': radius,
                'API_KEY': Config.AIRNOW_API_KEY
            }
            
            response = self.session.get(
                f"{self.airnow_base_url}/observation/latLong/current/",
                params=params
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Process AirNow response
            processed_data = []
            for observation in data:
                processed_data.append({
                    'station_id': observation.get('ReportingArea', 'Unknown'),
                    'parameter': observation.get('ParameterName', 'Unknown'),
                    'value': observation.get('AQI', 0),
                    'units': 'AQI',
                    'timestamp': observation.get('DateObserved', datetime.utcnow().isoformat()),
                    'lat': observation.get('Latitude', lat),
                    'lon': observation.get('Longitude', lon),
                    'source': 'AirNow'
                })
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error fetching AirNow data: {str(e)}")
            return []
    
    def _get_epa_aqs_data(
        self, 
        lat: float, 
        lon: float, 
        radius: int, 
        start_date: str, 
        end_date: str
    ) -> List[Dict]:
        """Fetch data from EPA AQS API"""
        try:
            if not self.epa_api_key:
                return []
            
            # EPA AQS API requires specific date format
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            
            start_date_str = start_dt.strftime('%Y%m%d')
            end_date_str = end_dt.strftime('%Y%m%d')
            
            all_data = []
            
            # Fetch data for each parameter
            for param_name, param_code in self.epa_parameters.items():
                try:
                    params = {
                        'email': 'demo@cleansky-ai.org',  # Required by EPA API
                        'key': self.epa_api_key,
                        'param': param_code,
                        'bdate': start_date_str,
                        'edate': end_date_str,
                        'minlat': lat - 0.5,
                        'maxlat': lat + 0.5,
                        'minlon': lon - 0.5,
                        'maxlon': lon + 0.5
                    }
                    
                    response = self.session.get(
                        f"{self.epa_base_url}/dailyData/byBox",
                        params=params
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        for observation in data.get('Data', []):
                            all_data.append({
                                'station_id': observation.get('site_number', 'Unknown'),
                                'parameter': param_name,
                                'value': observation.get('arithmetic_mean', 0),
                                'units': observation.get('units_of_measure', 'Unknown'),
                                'timestamp': observation.get('date_local', datetime.utcnow().isoformat()),
                                'lat': observation.get('latitude', lat),
                                'lon': observation.get('longitude', lon),
                                'source': 'EPA AQS'
                            })
                
                except Exception as param_error:
                    logger.warning(f"Failed to fetch EPA data for {param_name}: {str(param_error)}")
                    continue
            
            return all_data
            
        except Exception as e:
            logger.error(f"Error fetching EPA AQS data: {str(e)}")
            return []
    
    def _process_station_data(self, raw_data: List[Dict]) -> List[Dict]:
        """Process and standardize station data"""
        processed_data = []
        
        for station in raw_data:
            try:
                # Calculate AQI if not provided
                aqi_value = station.get('aqi')
                if not aqi_value and station.get('value') and station.get('parameter'):
                    aqi_value = self._calculate_aqi(
                        station['parameter'], 
                        station['value']
                    )
                
                # Determine primary pollutant
                primary_pollutant = self._determine_primary_pollutant(station)
                
                processed_station = {
                    'station_id': station.get('station_id', 'Unknown'),
                    'aqi': aqi_value or 0,
                    'primary_pollutant': primary_pollutant,
                    'parameters': {
                        station.get('parameter', 'Unknown'): {
                            'value': station.get('value', 0),
                            'units': station.get('units', 'Unknown')
                        }
                    },
                    'location': {
                        'lat': station.get('lat', 0),
                        'lon': station.get('lon', 0)
                    },
                    'timestamp': station.get('timestamp', datetime.utcnow().isoformat()),
                    'data_source': station.get('source', 'Unknown'),
                    'quality_flag': 'good'  # Assume good quality for ground stations
                }
                
                processed_data.append(processed_station)
                
            except Exception as e:
                logger.warning(f"Failed to process station data: {str(e)}")
                continue
        
        return processed_data
    
    def _calculate_aqi(self, parameter: str, concentration: float) -> int:
        """Calculate AQI from pollutant concentration"""
        # Simplified AQI calculation - in production use official EPA formulas
        aqi_breakpoints = {
            'pm25': [(0, 12, 0, 50), (12.1, 35.4, 51, 100), (35.5, 55.4, 101, 150)],
            'pm10': [(0, 54, 0, 50), (55, 154, 51, 100), (155, 254, 101, 150)],
            'ozone': [(0, 0.054, 0, 50), (0.055, 0.070, 51, 100), (0.071, 0.085, 101, 150)],
            'co': [(0, 4.4, 0, 50), (4.5, 9.4, 51, 100), (9.5, 12.4, 101, 150)],
            'so2': [(0, 35, 0, 50), (36, 75, 51, 100), (76, 185, 101, 150)],
            'no2': [(0, 53, 0, 50), (54, 100, 51, 100), (101, 360, 101, 150)]
        }
        
        if parameter.lower() not in aqi_breakpoints:
            return int(min(500, max(0, concentration)))  # Fallback
        
        breakpoints = aqi_breakpoints[parameter.lower()]
        
        for bp_lo, bp_hi, aqi_lo, aqi_hi in breakpoints:
            if bp_lo <= concentration <= bp_hi:
                # Linear interpolation
                aqi = ((aqi_hi - aqi_lo) / (bp_hi - bp_lo)) * (concentration - bp_lo) + aqi_lo
                return int(round(aqi))
        
        # If concentration is higher than all breakpoints, return max AQI
        return 500
    
    def _determine_primary_pollutant(self, station_data: Dict) -> str:
        """Determine the primary pollutant contributing to AQI"""
        # Simplified logic - in production, calculate AQI for each pollutant
        parameter = station_data.get('parameter', 'PM2.5')
        
        # Map parameter names to standard pollutant names
        pollutant_mapping = {
            'pm25': 'PM2.5',
            'pm10': 'PM10',
            'ozone': 'O3',
            'no2': 'NO2',
            'so2': 'SO2',
            'co': 'CO'
        }
        
        return pollutant_mapping.get(parameter.lower(), parameter.upper())
    
    def _generate_mock_station_data(
        self, 
        lat: float, 
        lon: float, 
        radius: int
    ) -> List[Dict]:
        """Generate mock ground station data for development/demo"""
        import random
        
        mock_stations = []
        num_stations = random.randint(3, 8)
        
        pollutants = ['PM2.5', 'O3', 'NO2', 'SO2', 'CO', 'PM10']
        
        for i in range(num_stations):
            # Random location within radius
            lat_offset = random.uniform(-0.2, 0.2)
            lon_offset = random.uniform(-0.3, 0.3)
            
            # Random AQI value
            base_aqi = random.uniform(30, 120)
            
            # Add some location-based variation (higher AQI near cities)
            if abs(lat - 34.0522) < 2 and abs(lon + 118.2437) < 2:  # LA area
                base_aqi += random.uniform(20, 50)
            elif abs(lat - 40.7128) < 2 and abs(lon + 74.0060) < 2:  # NYC area
                base_aqi += random.uniform(15, 40)
            
            aqi = min(500, max(0, int(base_aqi)))
            
            # Select primary pollutant
            primary_pollutant = random.choice(pollutants)
            
            mock_station = {
                'station_id': f"MOCK_{i+1:03d}",
                'aqi': aqi,
                'primary_pollutant': primary_pollutant,
                'value': aqi * random.uniform(0.5, 1.5),  # Simulate concentration
                'units': 'μg/m³' if primary_pollutant in ['PM2.5', 'PM10'] else 'ppb',
                'parameter': primary_pollutant.lower(),
                'lat': lat + lat_offset,
                'lon': lon + lon_offset,
                'timestamp': datetime.utcnow().isoformat(),
                'source': 'Mock Data',
                'distance_km': random.uniform(1, radius)
            }
            
            mock_stations.append(mock_station)
        
        return mock_stations
    
    def _generate_mock_historical_data(
        self, 
        lat: float, 
        lon: float, 
        days_back: int
    ) -> pd.DataFrame:
        """Generate mock historical data for ML training"""
        import random
        
        # Generate hourly data
        dates = pd.date_range(
            start=datetime.utcnow() - timedelta(days=days_back),
            end=datetime.utcnow(),
            freq='H'
        )
        
        data = []
        base_aqi = random.uniform(40, 80)
        
        for timestamp in dates:
            # Add daily and hourly patterns
            hour_of_day = timestamp.hour
            day_of_week = timestamp.weekday()
            
            # Daily pattern (higher during day, rush hours)
            daily_factor = 1.0
            if 6 <= hour_of_day <= 9 or 16 <= hour_of_day <= 19:  # Rush hours
                daily_factor = 1.3
            elif 22 <= hour_of_day or hour_of_day <= 5:  # Night
                daily_factor = 0.7
            
            # Weekly pattern (higher on weekdays)
            weekly_factor = 1.1 if day_of_week < 5 else 0.9
            
            # Random variation
            noise = random.uniform(0.8, 1.2)
            
            aqi = base_aqi * daily_factor * weekly_factor * noise
            aqi = min(500, max(0, aqi))
            
            data.append({
                'timestamp': timestamp,
                'aqi': aqi,
                'pm25': aqi * 0.4 + random.uniform(-5, 5),
                'o3': aqi * 0.6 + random.uniform(-10, 10),
                'no2': aqi * 0.3 + random.uniform(-3, 3),
                'lat': lat,
                'lon': lon
            })
        
        return pd.DataFrame(data)
