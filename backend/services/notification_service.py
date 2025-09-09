"""
Notification service for CleanSky AI - handles multi-channel notifications
"""
import structlog
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import asyncio
from dataclasses import dataclass
from enum import Enum

from config.config import Config

logger = structlog.get_logger()

class NotificationChannel(Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"

class NotificationPriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class NotificationMessage:
    """Structure for notification messages"""
    title: str
    message: str
    priority: NotificationPriority
    channels: List[NotificationChannel]
    recipient: Dict[str, str]  # email, phone, device_token, etc.
    data: Optional[Dict[str, Any]] = None
    scheduled_time: Optional[datetime] = None
    expires_at: Optional[datetime] = None

@dataclass
class NotificationResult:
    """Result of notification delivery attempt"""
    channel: NotificationChannel
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    delivered_at: Optional[datetime] = None

class EmailProvider:
    """Email notification provider using SendGrid"""
    
    def __init__(self):
        self.api_key = Config.SENDGRID_API_KEY
        self.from_email = "alerts@cleansky-ai.org"
        
    async def send_email(
        self, 
        to_email: str, 
        subject: str, 
        message: str, 
        priority: NotificationPriority = NotificationPriority.NORMAL
    ) -> NotificationResult:
        """Send email notification"""
        try:
            if not self.api_key:
                logger.warning("SendGrid API key not configured")
                return NotificationResult(
                    channel=NotificationChannel.EMAIL,
                    success=False,
                    error="SendGrid API key not configured"
                )
            
            # For demonstration, we'll simulate email sending
            # In production, use SendGrid Python SDK
            
            logger.info(f"Sending email to {to_email}: {subject}")
            
            # Simulate API call delay
            await asyncio.sleep(0.1)
            
            # Simulate success/failure
            import random
            success = random.random() > 0.05  # 95% success rate
            
            if success:
                message_id = f"sg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"
                return NotificationResult(
                    channel=NotificationChannel.EMAIL,
                    success=True,
                    message_id=message_id,
                    delivered_at=datetime.utcnow()
                )
            else:
                return NotificationResult(
                    channel=NotificationChannel.EMAIL,
                    success=False,
                    error="SendGrid delivery failed"
                )
                
        except Exception as e:
            logger.error(f"Email sending error: {str(e)}")
            return NotificationResult(
                channel=NotificationChannel.EMAIL,
                success=False,
                error=str(e)
            )

class SMSProvider:
    """SMS notification provider using Twilio"""
    
    def __init__(self):
        self.account_sid = Config.TWILIO_ACCOUNT_SID
        self.auth_token = Config.TWILIO_AUTH_TOKEN
        self.from_number = "+1-555-CLEANSKY"
        
    async def send_sms(
        self, 
        to_number: str, 
        message: str, 
        priority: NotificationPriority = NotificationPriority.NORMAL
    ) -> NotificationResult:
        """Send SMS notification"""
        try:
            if not self.account_sid or not self.auth_token:
                logger.warning("Twilio credentials not configured")
                return NotificationResult(
                    channel=NotificationChannel.SMS,
                    success=False,
                    error="Twilio credentials not configured"
                )
            
            logger.info(f"Sending SMS to {to_number}")
            
            # Simulate API call delay
            await asyncio.sleep(0.2)
            
            # Simulate success/failure
            import random
            success = random.random() > 0.02  # 98% success rate
            
            if success:
                message_id = f"tw_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"
                return NotificationResult(
                    channel=NotificationChannel.SMS,
                    success=True,
                    message_id=message_id,
                    delivered_at=datetime.utcnow()
                )
            else:
                return NotificationResult(
                    channel=NotificationChannel.SMS,
                    success=False,
                    error="Twilio delivery failed"
                )
                
        except Exception as e:
            logger.error(f"SMS sending error: {str(e)}")
            return NotificationResult(
                channel=NotificationChannel.SMS,
                success=False,
                error=str(e)
            )

class PushProvider:
    """Push notification provider"""
    
    def __init__(self):
        self.fcm_key = getattr(Config, 'FCM_SERVER_KEY', None)
        
    async def send_push(
        self, 
        device_token: str, 
        title: str, 
        message: str, 
        data: Optional[Dict[str, Any]] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL
    ) -> NotificationResult:
        """Send push notification"""
        try:
            if not self.fcm_key:
                logger.warning("FCM server key not configured")
                return NotificationResult(
                    channel=NotificationChannel.PUSH,
                    success=False,
                    error="FCM server key not configured"
                )
            
            logger.info(f"Sending push notification: {title}")
            
            # Simulate API call delay
            await asyncio.sleep(0.1)
            
            # Simulate success/failure
            import random
            success = random.random() > 0.10  # 90% success rate
            
            if success:
                message_id = f"fcm_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"
                return NotificationResult(
                    channel=NotificationChannel.PUSH,
                    success=True,
                    message_id=message_id,
                    delivered_at=datetime.utcnow()
                )
            else:
                return NotificationResult(
                    channel=NotificationChannel.PUSH,
                    success=False,
                    error="FCM delivery failed"
                )
                
        except Exception as e:
            logger.error(f"Push notification error: {str(e)}")
            return NotificationResult(
                channel=NotificationChannel.PUSH,
                success=False,
                error=str(e)
            )

class WebhookProvider:
    """Webhook notification provider"""
    
    def __init__(self):
        pass
        
    async def send_webhook(
        self, 
        webhook_url: str, 
        payload: Dict[str, Any],
        priority: NotificationPriority = NotificationPriority.NORMAL
    ) -> NotificationResult:
        """Send webhook notification"""
        try:
            import aiohttp
            
            logger.info(f"Sending webhook to {webhook_url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return NotificationResult(
                            channel=NotificationChannel.WEBHOOK,
                            success=True,
                            message_id=f"webhook_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                            delivered_at=datetime.utcnow()
                        )
                    else:
                        return NotificationResult(
                            channel=NotificationChannel.WEBHOOK,
                            success=False,
                            error=f"HTTP {response.status}"
                        )
                        
        except Exception as e:
            logger.error(f"Webhook sending error: {str(e)}")
            return NotificationResult(
                channel=NotificationChannel.WEBHOOK,
                success=False,
                error=str(e)
            )

class NotificationService:
    """Main notification service"""
    
    def __init__(self):
        self.email_provider = EmailProvider()
        self.sms_provider = SMSProvider()
        self.push_provider = PushProvider()
        self.webhook_provider = WebhookProvider()
        
        # Rate limiting and retry configuration
        self.rate_limits = {
            NotificationChannel.EMAIL: 100,  # per hour
            NotificationChannel.SMS: 50,     # per hour
            NotificationChannel.PUSH: 1000,  # per hour
            NotificationChannel.WEBHOOK: 200 # per hour
        }
        
        self.retry_config = {
            'max_attempts': 3,
            'base_delay': 1,  # seconds
            'max_delay': 300  # seconds
        }
        
        # In-memory tracking (in production, use Redis or database)
        self.rate_limit_counters = {}
        self.failed_notifications = []
        
    async def send_notification(
        self, 
        notification: NotificationMessage
    ) -> Dict[NotificationChannel, NotificationResult]:
        """Send notification through specified channels"""
        try:
            results = {}
            
            # Check if notification is expired
            if notification.expires_at and datetime.utcnow() > notification.expires_at:
                logger.warning("Notification expired, skipping delivery")
                for channel in notification.channels:
                    results[channel] = NotificationResult(
                        channel=channel,
                        success=False,
                        error="Notification expired"
                    )
                return results
            
            # Check if notification is scheduled for future
            if notification.scheduled_time and datetime.utcnow() < notification.scheduled_time:
                logger.info(f"Notification scheduled for {notification.scheduled_time}")
                # In production, would queue for later delivery
                for channel in notification.channels:
                    results[channel] = NotificationResult(
                        channel=channel,
                        success=False,
                        error="Notification scheduled for future delivery"
                    )
                return results
            
            # Send through each channel
            tasks = []
            for channel in notification.channels:
                if self._check_rate_limit(channel):
                    task = self._send_through_channel(notification, channel)
                    tasks.append(task)
                else:
                    results[channel] = NotificationResult(
                        channel=channel,
                        success=False,
                        error="Rate limit exceeded"
                    )
            
            # Wait for all deliveries to complete
            if tasks:
                channel_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in channel_results:
                    if isinstance(result, NotificationResult):
                        results[result.channel] = result
                    elif isinstance(result, Exception):
                        logger.error(f"Notification delivery exception: {str(result)}")
            
            # Log delivery summary
            successful_channels = [ch for ch, result in results.items() if result.success]
            failed_channels = [ch for ch, result in results.items() if not result.success]
            
            logger.info(
                f"Notification delivery complete. "
                f"Successful: {[ch.value for ch in successful_channels]}, "
                f"Failed: {[ch.value for ch in failed_channels]}"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Notification service error: {str(e)}")
            # Return failure for all channels
            results = {}
            for channel in notification.channels:
                results[channel] = NotificationResult(
                    channel=channel,
                    success=False,
                    error=str(e)
                )
            return results
    
    async def _send_through_channel(
        self, 
        notification: NotificationMessage, 
        channel: NotificationChannel
    ) -> NotificationResult:
        """Send notification through specific channel with retry logic"""
        for attempt in range(self.retry_config['max_attempts']):
            try:
                if channel == NotificationChannel.EMAIL:
                    result = await self.email_provider.send_email(
                        to_email=notification.recipient.get('email'),
                        subject=notification.title,
                        message=notification.message,
                        priority=notification.priority
                    )
                
                elif channel == NotificationChannel.SMS:
                    result = await self.sms_provider.send_sms(
                        to_number=notification.recipient.get('phone'),
                        message=f"{notification.title}: {notification.message}",
                        priority=notification.priority
                    )
                
                elif channel == NotificationChannel.PUSH:
                    result = await self.push_provider.send_push(
                        device_token=notification.recipient.get('device_token'),
                        title=notification.title,
                        message=notification.message,
                        data=notification.data,
                        priority=notification.priority
                    )
                
                elif channel == NotificationChannel.WEBHOOK:
                    payload = {
                        'title': notification.title,
                        'message': notification.message,
                        'priority': notification.priority.value,
                        'data': notification.data,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    result = await self.webhook_provider.send_webhook(
                        webhook_url=notification.recipient.get('webhook_url'),
                        payload=payload,
                        priority=notification.priority
                    )
                
                else:
                    result = NotificationResult(
                        channel=channel,
                        success=False,
                        error=f"Unsupported channel: {channel.value}"
                    )
                
                # If successful or non-retryable error, return result
                if result.success or not self._is_retryable_error(result.error):
                    self._update_rate_limit_counter(channel)
                    return result
                
                # Calculate delay for next attempt
                if attempt < self.retry_config['max_attempts'] - 1:
                    delay = min(
                        self.retry_config['base_delay'] * (2 ** attempt),
                        self.retry_config['max_delay']
                    )
                    logger.warning(
                        f"Attempt {attempt + 1} failed for {channel.value}, "
                        f"retrying in {delay} seconds: {result.error}"
                    )
                    await asyncio.sleep(delay)
                
            except Exception as e:
                logger.error(f"Channel {channel.value} delivery error: {str(e)}")
                if attempt == self.retry_config['max_attempts'] - 1:
                    return NotificationResult(
                        channel=channel,
                        success=False,
                        error=str(e)
                    )
        
        return NotificationResult(
            channel=channel,
            success=False,
            error="Max retry attempts exceeded"
        )
    
    def _check_rate_limit(self, channel: NotificationChannel) -> bool:
        """Check if channel is within rate limits"""
        current_hour = datetime.utcnow().strftime('%Y%m%d%H')
        key = f"{channel.value}_{current_hour}"
        
        current_count = self.rate_limit_counters.get(key, 0)
        limit = self.rate_limits.get(channel, 100)
        
        return current_count < limit
    
    def _update_rate_limit_counter(self, channel: NotificationChannel):
        """Update rate limit counter"""
        current_hour = datetime.utcnow().strftime('%Y%m%d%H')
        key = f"{channel.value}_{current_hour}"
        
        self.rate_limit_counters[key] = self.rate_limit_counters.get(key, 0) + 1
    
    def _is_retryable_error(self, error: Optional[str]) -> bool:
        """Determine if an error is retryable"""
        if not error:
            return False
        
        retryable_indicators = [
            'timeout', 'connection', 'network', 'temporary', 'rate limit',
            'server error', '5', 'unavailable'
        ]
        
        error_lower = error.lower()
        return any(indicator in error_lower for indicator in retryable_indicators)
    
    def get_delivery_status(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get delivery status for a message (mock implementation)"""
        # In production, would query actual provider APIs
        return {
            'message_id': message_id,
            'status': 'delivered',
            'delivered_at': datetime.utcnow().isoformat(),
            'channel': 'email'  # or actual channel
        }
    
    def get_rate_limit_status(self) -> Dict[str, Dict[str, int]]:
        """Get current rate limit status"""
        current_hour = datetime.utcnow().strftime('%Y%m%d%H')
        status = {}
        
        for channel in NotificationChannel:
            key = f"{channel.value}_{current_hour}"
            current_count = self.rate_limit_counters.get(key, 0)
            limit = self.rate_limits.get(channel, 100)
            
            status[channel.value] = {
                'current_count': current_count,
                'limit': limit,
                'remaining': max(0, limit - current_count)
            }
        
        return status
    
    def create_air_quality_alert(
        self,
        aqi_value: float,
        location: str,
        recipient: Dict[str, str],
        channels: List[str] = None
    ) -> NotificationMessage:
        """Create air quality alert notification"""
        if channels is None:
            channels = ['email', 'push']
        
        # Determine severity based on AQI
        if aqi_value > 300:
            priority = NotificationPriority.CRITICAL
            severity = "HAZARDOUS"
        elif aqi_value > 200:
            priority = NotificationPriority.HIGH
            severity = "VERY UNHEALTHY"
        elif aqi_value > 150:
            priority = NotificationPriority.HIGH
            severity = "UNHEALTHY"
        elif aqi_value > 100:
            priority = NotificationPriority.NORMAL
            severity = "UNHEALTHY FOR SENSITIVE GROUPS"
        else:
            priority = NotificationPriority.NORMAL
            severity = "MODERATE"
        
        title = f"Air Quality Alert: {severity}"
        message = (
            f"Air quality in {location} has reached {aqi_value:.0f} AQI ({severity}). "
            f"Consider limiting outdoor activities and staying indoors if possible."
        )
        
        notification_channels = [
            NotificationChannel(ch) for ch in channels 
            if ch in [c.value for c in NotificationChannel]
        ]
        
        return NotificationMessage(
            title=title,
            message=message,
            priority=priority,
            channels=notification_channels,
            recipient=recipient,
            data={
                'type': 'air_quality_alert',
                'aqi': aqi_value,
                'location': location,
                'severity': severity
            }
        )
    
    def create_forecast_notification(
        self,
        forecast_summary: str,
        location: str,
        recipient: Dict[str, str],
        channels: List[str] = None
    ) -> NotificationMessage:
        """Create forecast notification"""
        if channels is None:
            channels = ['email']
        
        title = f"Daily Air Quality Forecast - {location}"
        message = forecast_summary
        
        notification_channels = [
            NotificationChannel(ch) for ch in channels 
            if ch in [c.value for c in NotificationChannel]
        ]
        
        return NotificationMessage(
            title=title,
            message=message,
            priority=NotificationPriority.NORMAL,
            channels=notification_channels,
            recipient=recipient,
            data={
                'type': 'forecast_update',
                'location': location
            }
        )
    
    async def send_batch_notifications(
        self, 
        notifications: List[NotificationMessage]
    ) -> List[Dict[NotificationChannel, NotificationResult]]:
        """Send multiple notifications concurrently"""
        try:
            tasks = [self.send_notification(notif) for notif in notifications]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle any exceptions
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Batch notification {i} failed: {str(result)}")
                    # Create failure result for all channels
                    failure_result = {}
                    for channel in notifications[i].channels:
                        failure_result[channel] = NotificationResult(
                            channel=channel,
                            success=False,
                            error=str(result)
                        )
                    processed_results.append(failure_result)
                else:
                    processed_results.append(result)
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Batch notification error: {str(e)}")
            return []
