"""
Data ingestion service for CleanSky AI - orchestrates data collection from all sources
"""
import structlog
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
import pandas as pd
from dataclasses import dataclass, field
from enum import Enum
import json

from backend.services.tempo_service import TempoService
from backend.services.weather_service import WeatherService
from backend.services.ground_station_service import GroundStationService
from backend.models.air_quality_model import AirQualityService
from backend.models.database import get_db, DataIngestionLog
from backend.utils.data_processor import DataCache
from config.config import Config

logger = structlog.get_logger()

class DataSource(Enum):
    TEMPO = "tempo"
    GROUND_STATIONS = "ground_stations"
    WEATHER = "weather"
    EPA_AQS = "epa_aqs"
    AIRNOW = "airnow"

class IngestionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"

@dataclass
class IngestionTask:
    """Represents a data ingestion task"""
    source: DataSource
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1  # 1 = highest, 5 = lowest
    scheduled_time: Optional[datetime] = None
    timeout_seconds: int = 300
    retry_count: int = 0
    max_retries: int = 3
    callback: Optional[Callable] = None

@dataclass
class IngestionResult:
    """Result of a data ingestion task"""
    task: IngestionTask
    status: IngestionStatus
    records_processed: int = 0
    records_successful: int = 0
    records_failed: int = 0
    execution_time: float = 0.0
    error_message: Optional[str] = None
    data_summary: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class DataIngestionService:
    """Main data ingestion orchestration service"""
    
    def __init__(self):
        # Initialize data source services
        self.tempo_service = TempoService()
        self.weather_service = WeatherService()
        self.ground_station_service = GroundStationService()
        self.air_quality_service = AirQualityService()
        
        # Cache and storage
        self.cache = DataCache()
        
        # Task management
        self.task_queue = asyncio.PriorityQueue()
        self.running_tasks = {}
        self.completed_tasks = []
        
        # Configuration
        self.config = {
            'max_concurrent_tasks': getattr(Config, 'MAX_CONCURRENT_INGESTION_TASKS', 5),
            'default_timeout': getattr(Config, 'INGESTION_TIMEOUT_SECONDS', 300),
            'batch_size': getattr(Config, 'INGESTION_BATCH_SIZE', 1000),
            'retry_delay': getattr(Config, 'INGESTION_RETRY_DELAY', 60)  # seconds
        }
        
        # Scheduling intervals (in minutes)
        self.ingestion_schedules = {
            DataSource.TEMPO: 60,          # Every hour
            DataSource.GROUND_STATIONS: 15, # Every 15 minutes
            DataSource.WEATHER: 30,        # Every 30 minutes
            DataSource.EPA_AQS: 60,        # Every hour
            DataSource.AIRNOW: 15          # Every 15 minutes
        }
        
        # Statistics
        self.stats = {
            'total_tasks_processed': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'total_records_processed': 0,
            'last_ingestion_time': {}
        }
    
    async def start_ingestion_worker(self):
        """Start the background ingestion worker"""
        logger.info("Starting data ingestion worker")
        
        while True:
            try:
                # Check if we can start new tasks
                if len(self.running_tasks) < self.config['max_concurrent_tasks']:
                    # Get next task from queue (this will block if queue is empty)
                    priority, task_id, task = await asyncio.wait_for(
                        self.task_queue.get(), timeout=1.0
                    )
                    
                    # Start task execution
                    asyncio.create_task(self._execute_task(task_id, task))
                
                await asyncio.sleep(1)  # Brief pause to prevent busy waiting
                
            except asyncio.TimeoutError:
                # No tasks in queue, continue
                continue
            except Exception as e:
                logger.error(f"Ingestion worker error: {str(e)}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def schedule_routine_ingestion(self):
        """Schedule routine data ingestion tasks"""
        logger.info("Starting routine ingestion scheduler")
        
        while True:
            try:
                current_time = datetime.utcnow()
                
                for source, interval_minutes in self.ingestion_schedules.items():
                    last_ingestion = self.stats['last_ingestion_time'].get(source)
                    
                    if (not last_ingestion or 
                        (current_time - last_ingestion).total_seconds() >= interval_minutes * 60):
                        
                        # Create ingestion task
                        task = self._create_routine_task(source, current_time)
                        await self.queue_task(task)
                        
                        # Update last ingestion time
                        self.stats['last_ingestion_time'][source] = current_time
                
                # Sleep for a minute before checking again
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Routine ingestion scheduler error: {str(e)}")
                await asyncio.sleep(60)
    
    async def queue_task(self, task: IngestionTask) -> str:
        """Queue a data ingestion task"""
        task_id = f"{task.source.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Add to priority queue (lower priority number = higher priority)
        await self.task_queue.put((task.priority, task_id, task))
        
        logger.info(f"Queued ingestion task: {task_id}")
        return task_id
    
    async def _execute_task(self, task_id: str, task: IngestionTask) -> IngestionResult:
        """Execute a single ingestion task"""
        start_time = datetime.utcnow()
        self.running_tasks[task_id] = task
        
        result = IngestionResult(
            task=task,
            status=IngestionStatus.RUNNING,
            started_at=start_time
        )
        
        try:
            logger.info(f"Starting ingestion task: {task_id}")
            
            # Execute the appropriate ingestion method
            if task.source == DataSource.TEMPO:
                await self._ingest_tempo_data(task, result)
            elif task.source == DataSource.GROUND_STATIONS:
                await self._ingest_ground_station_data(task, result)
            elif task.source == DataSource.WEATHER:
                await self._ingest_weather_data(task, result)
            elif task.source == DataSource.EPA_AQS:
                await self._ingest_epa_data(task, result)
            elif task.source == DataSource.AIRNOW:
                await self._ingest_airnow_data(task, result)
            else:
                raise ValueError(f"Unknown data source: {task.source}")
            
            # Mark as completed
            result.status = IngestionStatus.COMPLETED if result.records_failed == 0 else IngestionStatus.PARTIAL
            result.completed_at = datetime.utcnow()
            result.execution_time = (result.completed_at - start_time).total_seconds()
            
            logger.info(
                f"Completed ingestion task {task_id}: "
                f"{result.records_successful}/{result.records_processed} records successful"
            )
            
        except Exception as e:
            result.status = IngestionStatus.FAILED
            result.error_message = str(e)
            result.completed_at = datetime.utcnow()
            result.execution_time = (result.completed_at - start_time).total_seconds()
            
            logger.error(f"Ingestion task {task_id} failed: {str(e)}")
            
            # Check if we should retry
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                logger.info(f"Scheduling retry {task.retry_count} for task {task_id}")
                
                # Schedule retry with delay
                retry_task = task
                retry_task.scheduled_time = datetime.utcnow() + timedelta(
                    seconds=self.config['retry_delay'] * task.retry_count
                )
                await self.queue_task(retry_task)
        
        finally:
            # Clean up
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
            
            self.completed_tasks.append(result)
            self._update_stats(result)
            
            # Log to database
            await self._log_ingestion_result(result)
            
            # Call callback if provided
            if task.callback:
                try:
                    await task.callback(result)
                except Exception as e:
                    logger.error(f"Task callback error: {str(e)}")
        
        return result
    
    async def _ingest_tempo_data(self, task: IngestionTask, result: IngestionResult):
        """Ingest TEMPO satellite data"""
        parameters = task.parameters
        
        # Get parameters
        date = parameters.get('date', datetime.utcnow().strftime('%Y-%m-%d'))
        parameters_list = parameters.get('parameters', ['NO2', 'O3'])
        location = parameters.get('location', {
            'type': 'bbox',
            'west': -125.0, 'south': 25.0, 'east': -66.0, 'north': 49.0
        })
        
        # Fetch TEMPO data
        tempo_data = self.tempo_service.get_data(
            parameters=parameters_list,
            date=date,
            location=location
        )
        
        result.records_processed = len(tempo_data)
        
        # Process and store data
        successful_count = 0
        for data_point in tempo_data:
            try:
                # Store in database or cache
                await self._store_tempo_data(data_point)
                successful_count += 1
            except Exception as e:
                logger.warning(f"Failed to store TEMPO data point: {str(e)}")
                result.records_failed += 1
        
        result.records_successful = successful_count
        result.data_summary = {
            'parameters': parameters_list,
            'date': date,
            'location_type': location.get('type'),
            'unique_parameters': list(set(dp.get('parameter') for dp in tempo_data))
        }
    
    async def _ingest_ground_station_data(self, task: IngestionTask, result: IngestionResult):
        """Ingest ground station data"""
        parameters = task.parameters
        
        # Get multiple locations or use default coverage area
        locations = parameters.get('locations', [
            {'lat': 34.0522, 'lon': -118.2437, 'radius': 50},  # LA
            {'lat': 40.7128, 'lon': -74.0060, 'radius': 50},   # NYC
            {'lat': 41.8781, 'lon': -87.6298, 'radius': 50}    # Chicago
        ])
        
        all_station_data = []
        
        for location in locations:
            try:
                station_data = self.ground_station_service.get_air_quality_data(
                    location=f"{location['lat']},{location['lon']}",
                    radius=location.get('radius', 25),
                    start_date=parameters.get('start_date'),
                    end_date=parameters.get('end_date')
                )
                all_station_data.extend(station_data)
            except Exception as e:
                logger.warning(f"Failed to get ground station data for location {location}: {str(e)}")
        
        result.records_processed = len(all_station_data)
        
        # Store data
        successful_count = 0
        for station_data in all_station_data:
            try:
                await self._store_ground_station_data(station_data)
                successful_count += 1
            except Exception as e:
                logger.warning(f"Failed to store ground station data: {str(e)}")
                result.records_failed += 1
        
        result.records_successful = successful_count
        result.data_summary = {
            'locations_processed': len(locations),
            'unique_stations': len(set(sd.get('station_id') for sd in all_station_data if sd.get('station_id')))
        }
    
    async def _ingest_weather_data(self, task: IngestionTask, result: IngestionResult):
        """Ingest weather data"""
        parameters = task.parameters
        
        locations = parameters.get('locations', [
            {'lat': 39.8283, 'lon': -98.5795}  # Center of US
        ])
        
        all_weather_data = []
        
        for location in locations:
            try:
                # Get current weather
                current_weather = self.weather_service.get_current_weather(
                    location['lat'], location['lon']
                )
                
                if current_weather:
                    all_weather_data.append({
                        'type': 'current',
                        'data': current_weather,
                        'location': location
                    })
                
                # Get forecast if requested
                if parameters.get('include_forecast', True):
                    forecast_data = self.weather_service.get_forecast(
                        location['lat'], location['lon']
                    )
                    
                    if forecast_data:
                        all_weather_data.append({
                            'type': 'forecast',
                            'data': forecast_data,
                            'location': location
                        })
                        
            except Exception as e:
                logger.warning(f"Failed to get weather data for location {location}: {str(e)}")
        
        result.records_processed = len(all_weather_data)
        
        # Store weather data
        successful_count = 0
        for weather_data in all_weather_data:
            try:
                await self._store_weather_data(weather_data)
                successful_count += 1
            except Exception as e:
                logger.warning(f"Failed to store weather data: {str(e)}")
                result.records_failed += 1
        
        result.records_successful = successful_count
        result.data_summary = {
            'locations_processed': len(locations),
            'data_types': list(set(wd.get('type') for wd in all_weather_data))
        }
    
    async def _ingest_epa_data(self, task: IngestionTask, result: IngestionResult):
        """Ingest EPA AQS data"""
        # Placeholder for EPA-specific ingestion logic
        # This would be similar to ground station ingestion but with EPA-specific parameters
        await self._ingest_ground_station_data(task, result)
    
    async def _ingest_airnow_data(self, task: IngestionTask, result: IngestionResult):
        """Ingest AirNow data"""
        # Placeholder for AirNow-specific ingestion logic
        await self._ingest_ground_station_data(task, result)
    
    async def _store_tempo_data(self, data_point: Dict[str, Any]):
        """Store TEMPO data point"""
        # Store in cache for immediate use
        cache_key = f"tempo_{data_point.get('parameter')}_{data_point.get('lat')}_{data_point.get('lon')}"
        self.cache.set(cache_key, data_point, expire=3600)
        
        # In production, would also store in database
        logger.debug(f"Stored TEMPO data point: {data_point.get('parameter')} at {data_point.get('lat')}, {data_point.get('lon')}")
    
    async def _store_ground_station_data(self, station_data: Dict[str, Any]):
        """Store ground station data"""
        # Store in cache
        cache_key = f"station_{station_data.get('station_id')}_{datetime.utcnow().strftime('%Y%m%d%H')}"
        self.cache.set(cache_key, station_data, expire=1800)
        
        # In production, would store in database using AirQualityService
        logger.debug(f"Stored ground station data: {station_data.get('station_id')}")
    
    async def _store_weather_data(self, weather_data: Dict[str, Any]):
        """Store weather data"""
        location = weather_data.get('location', {})
        cache_key = f"weather_{location.get('lat')}_{location.get('lon')}_{weather_data.get('type')}"
        self.cache.set(cache_key, weather_data, expire=1800)
        
        logger.debug(f"Stored weather data: {weather_data.get('type')} for {location}")
    
    def _create_routine_task(self, source: DataSource, current_time: datetime) -> IngestionTask:
        """Create a routine ingestion task for a data source"""
        
        # Define standard parameters for each source
        if source == DataSource.TEMPO:
            parameters = {
                'date': current_time.strftime('%Y-%m-%d'),
                'parameters': ['NO2', 'O3', 'HCHO', 'SO2'],
                'location': {
                    'type': 'bbox',
                    'west': -125.0, 'south': 25.0, 'east': -66.0, 'north': 49.0
                }
            }
        elif source == DataSource.GROUND_STATIONS:
            parameters = {
                'locations': [
                    {'lat': 34.0522, 'lon': -118.2437, 'radius': 50},  # LA
                    {'lat': 40.7128, 'lon': -74.0060, 'radius': 50},   # NYC
                    {'lat': 41.8781, 'lon': -87.6298, 'radius': 50},   # Chicago
                    {'lat': 29.7604, 'lon': -95.3698, 'radius': 50},   # Houston
                    {'lat': 33.4484, 'lon': -112.0740, 'radius': 50}   # Phoenix
                ]
            }
        elif source == DataSource.WEATHER:
            parameters = {
                'locations': [
                    {'lat': 39.8283, 'lon': -98.5795}  # Center of US
                ],
                'include_forecast': True
            }
        else:
            parameters = {}
        
        return IngestionTask(
            source=source,
            parameters=parameters,
            priority=2,  # Routine tasks have normal priority
            scheduled_time=current_time
        )
    
    def _update_stats(self, result: IngestionResult):
        """Update ingestion statistics"""
        self.stats['total_tasks_processed'] += 1
        
        if result.status == IngestionStatus.COMPLETED:
            self.stats['successful_tasks'] += 1
        else:
            self.stats['failed_tasks'] += 1
        
        self.stats['total_records_processed'] += result.records_processed
    
    async def _log_ingestion_result(self, result: IngestionResult):
        """Log ingestion result to database"""
        try:
            db = next(get_db())
            
            log_entry = DataIngestionLog(
                data_source=result.task.source.value,
                operation_type='ingestion',
                status='success' if result.status == IngestionStatus.COMPLETED else 'error',
                records_processed=result.records_processed,
                records_success=result.records_successful,
                records_error=result.records_failed,
                processing_time_seconds=result.execution_time,
                error_message=result.error_message,
                error_details=result.data_summary,
                started_at=result.started_at,
                completed_at=result.completed_at
            )
            
            db.add(log_entry)
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to log ingestion result: {str(e)}")
        finally:
            db.close()
    
    def get_ingestion_status(self) -> Dict[str, Any]:
        """Get current ingestion status"""
        return {
            'running_tasks': len(self.running_tasks),
            'queued_tasks': self.task_queue.qsize(),
            'statistics': self.stats.copy(),
            'last_ingestion_times': {
                source.value: timestamp.isoformat() if timestamp else None
                for source, timestamp in self.stats['last_ingestion_time'].items()
            },
            'configuration': self.config
        }
    
    def get_recent_results(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent ingestion results"""
        recent_results = sorted(
            self.completed_tasks,
            key=lambda x: x.completed_at or datetime.min,
            reverse=True
        )[:limit]
        
        return [
            {
                'task_id': f"{result.task.source.value}_{result.started_at.strftime('%Y%m%d_%H%M%S') if result.started_at else 'unknown'}",
                'source': result.task.source.value,
                'status': result.status.value,
                'records_processed': result.records_processed,
                'records_successful': result.records_successful,
                'records_failed': result.records_failed,
                'execution_time': result.execution_time,
                'error_message': result.error_message,
                'started_at': result.started_at.isoformat() if result.started_at else None,
                'completed_at': result.completed_at.isoformat() if result.completed_at else None
            }
            for result in recent_results
        ]
    
    async def trigger_manual_ingestion(
        self,
        source: DataSource,
        parameters: Optional[Dict[str, Any]] = None,
        priority: int = 1
    ) -> str:
        """Trigger manual data ingestion"""
        task = IngestionTask(
            source=source,
            parameters=parameters or {},
            priority=priority,
            scheduled_time=datetime.utcnow()
        )
        
        task_id = await self.queue_task(task)
        logger.info(f"Manual ingestion triggered: {task_id}")
        
        return task_id
