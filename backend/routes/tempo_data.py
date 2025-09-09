"""
TEMPO satellite data API routes for CleanSky AI
"""
from flask import request, current_app
from flask_restful import Resource
import structlog
from datetime import datetime, timedelta
import json

from backend.services.tempo_service import TempoService
from backend.utils.validators import validate_coordinates, validate_date_range
from backend.utils.data_processor import TempoDataProcessor

logger = structlog.get_logger()

class TempoDataAPI(Resource):
    """TEMPO satellite data API endpoints"""
    
    def __init__(self):
        self.tempo_service = TempoService()
        self.data_processor = TempoDataProcessor()
    
    def get(self, parameter=None):
        """Get TEMPO satellite data"""
        try:
            # Parse query parameters
            lat = request.args.get('lat', type=float)
            lon = request.args.get('lon', type=float)
            bbox = request.args.get('bbox')  # Format: "west,south,east,north"
            date = request.args.get('date')
            resolution = request.args.get('resolution', 'high')  # high, medium, low
            parameters = request.args.getlist('parameter') or [parameter] if parameter else ['NO2']
            
            # Validate inputs
            if lat is not None and lon is not None:
                if not validate_coordinates(lat, lon):
                    return {'error': 'Invalid coordinates'}, 400
            
            if bbox:
                try:
                    west, south, east, north = map(float, bbox.split(','))
                    if not (validate_coordinates(south, west) and validate_coordinates(north, east)):
                        return {'error': 'Invalid bounding box coordinates'}, 400
                except (ValueError, TypeError):
                    return {'error': 'Invalid bounding box format. Use: west,south,east,north'}, 400
            
            # Default to today if no date specified
            if not date:
                date = datetime.utcnow().strftime('%Y-%m-%d')
            
            # Validate available parameters
            available_parameters = ['NO2', 'O3', 'HCHO', 'SO2']
            invalid_params = [p for p in parameters if p not in available_parameters]
            if invalid_params:
                return {
                    'error': f'Invalid parameters: {invalid_params}. Available: {available_parameters}'
                }, 400
            
            logger.info(f"Fetching TEMPO data for parameters: {parameters}, date: {date}")
            
            # Build query based on location type
            if bbox:
                query_location = {
                    'type': 'bbox',
                    'west': west, 'south': south, 'east': east, 'north': north
                }
            elif lat is not None and lon is not None:
                query_location = {
                    'type': 'point',
                    'lat': lat, 'lon': lon
                }
            else:
                # Default to North America bounds
                query_location = {
                    'type': 'bbox',
                    'west': -170.0, 'south': 15.0, 'east': -50.0, 'north': 70.0
                }
            
            # Fetch TEMPO data
            tempo_data = self.tempo_service.get_data(
                parameters=parameters,
                date=date,
                location=query_location,
                resolution=resolution
            )
            
            if not tempo_data:
                return {
                    'error': 'No TEMPO data available for specified parameters and location'
                }, 404
            
            # Process and format data
            processed_data = self.data_processor.process_tempo_data(tempo_data)
            
            # Generate statistics
            statistics = self._generate_statistics(processed_data, parameters)
            
            return {
                'status': 'success',
                'query': {
                    'parameters': parameters,
                    'date': date,
                    'location': query_location,
                    'resolution': resolution
                },
                'timestamp': datetime.utcnow().isoformat(),
                'data': processed_data,
                'statistics': statistics,
                'metadata': {
                    'satellite': 'TEMPO',
                    'data_source': 'NASA Goddard Space Flight Center',
                    'temporal_resolution': 'Hourly',
                    'spatial_resolution': '2.1 km x 4.4 km at nadir',
                    'units': self._get_parameter_units(parameters)
                }
            }
            
        except Exception as e:
            logger.error(f"Error fetching TEMPO data: {str(e)}")
            return {'error': 'Failed to fetch TEMPO data'}, 500
    
    def post(self):
        """Get processed TEMPO data for multiple locations/times"""
        try:
            data = request.get_json()
            if not data:
                return {'error': 'No data provided'}, 400
            
            locations = data.get('locations', [])
            date_range = data.get('date_range', {})
            parameters = data.get('parameters', ['NO2'])
            processing_options = data.get('processing', {})
            
            if not locations:
                return {'error': 'No locations specified'}, 400
            
            # Validate all locations
            for i, loc in enumerate(locations):
                if not validate_coordinates(loc.get('lat'), loc.get('lon')):
                    return {'error': f'Invalid coordinates for location {i+1}'}, 400
            
            logger.info(f"Processing TEMPO data for {len(locations)} locations")
            
            results = []
            for location in locations:
                try:
                    # Get data for each location
                    location_data = self.tempo_service.get_data(
                        parameters=parameters,
                        date=date_range.get('start'),
                        end_date=date_range.get('end'),
                        location={
                            'type': 'point',
                            'lat': location['lat'],
                            'lon': location['lon']
                        }
                    )
                    
                    # Apply processing options
                    processed = self.data_processor.apply_processing(
                        location_data, 
                        processing_options
                    )
                    
                    results.append({
                        'location': location,
                        'data': processed,
                        'status': 'success'
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing location {location}: {str(e)}")
                    results.append({
                        'location': location,
                        'error': str(e),
                        'status': 'error'
                    })
            
            # Generate summary statistics
            summary = self._generate_batch_summary(results, parameters)
            
            return {
                'status': 'success',
                'timestamp': datetime.utcnow().isoformat(),
                'parameters': parameters,
                'locations_processed': len(locations),
                'results': results,
                'summary': summary
            }
            
        except Exception as e:
            logger.error(f"Error processing batch TEMPO request: {str(e)}")
            return {'error': 'Failed to process batch request'}, 500
    
    def _generate_statistics(self, data, parameters):
        """Generate statistics for TEMPO data"""
        statistics = {}
        
        for param in parameters:
            param_data = [
                point.get(param.lower()) for point in data 
                if point.get(param.lower()) is not None
            ]
            
            if param_data:
                statistics[param] = {
                    'count': len(param_data),
                    'min': min(param_data),
                    'max': max(param_data),
                    'mean': sum(param_data) / len(param_data),
                    'median': sorted(param_data)[len(param_data) // 2]
                }
            else:
                statistics[param] = {
                    'count': 0,
                    'message': 'No valid data points'
                }
        
        return statistics
    
    def _generate_batch_summary(self, results, parameters):
        """Generate summary for batch processing"""
        successful = sum(1 for r in results if r['status'] == 'success')
        failed = len(results) - successful
        
        # Aggregate data from successful results
        all_data = []
        for result in results:
            if result['status'] == 'success':
                all_data.extend(result['data'])
        
        summary = {
            'locations': {
                'total': len(results),
                'successful': successful,
                'failed': failed
            },
            'data_points': len(all_data)
        }
        
        if all_data:
            summary['statistics'] = self._generate_statistics(all_data, parameters)
        
        return summary
    
    def _get_parameter_units(self, parameters):
        """Get units for TEMPO parameters"""
        units = {
            'NO2': 'molecules/cm²',
            'O3': 'Dobson Units',
            'HCHO': 'molecules/cm²',
            'SO2': 'molecules/cm²'
        }
        
        return {param: units.get(param, 'Unknown') for param in parameters}
