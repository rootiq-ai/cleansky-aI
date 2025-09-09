"""
Notifications API routes for CleanSky AI
"""
from flask import request, current_app
from flask_restful import Resource
import structlog
from datetime import datetime

from backend.services.ml_service import MLService
from backend.utils.validators import validate_email, validate_phone

logger = structlog.get_logger()

class NotificationAPI(Resource):
    """Notification management API endpoints"""
    
    def __init__(self):
        pass
    
    def get(self, user_id=None):
        """Get notification history or settings"""
        try:
            if user_id:
                # Get notifications for specific user
                notification_type = request.args.get('type', 'all')  # all, alerts, updates
                limit = request.args.get('limit', 50, type=int)
                
                # Mock notification history for demo
                notifications = self._get_mock_notifications(user_id, notification_type, limit)
                
                return {
                    'status': 'success',
                    'user_id': user_id,
                    'notifications': notifications,
                    'total_count': len(notifications)
                }
            else:
                # Get notification system status
                return {
                    'status': 'success',
                    'system_status': {
                        'email_service': 'active',
                        'sms_service': 'active',
                        'push_service': 'active',
                        'last_check': datetime.utcnow().isoformat()
                    },
                    'notification_types': [
                        'air_quality_alert',
                        'forecast_update',
                        'system_maintenance',
                        'weekly_summary'
                    ]
                }
                
        except Exception as e:
            logger.error(f"Error fetching notifications: {str(e)}")
            return {'error': 'Failed to fetch notifications'}, 500
    
    def post(self):
        """Send a new notification"""
        try:
            data = request.get_json()
            if not data:
                return {'error': 'No data provided'}, 400
            
            # Extract notification details
            user_id = data.get('user_id')
            message = data.get('message')
            notification_type = data.get('type', 'alert')
            channels = data.get('channels', ['email'])
            priority = data.get('priority', 'normal')  # low, normal, high, urgent
            recipient_info = data.get('recipient', {})
            
            # Validate required fields
            if not message:
                return {'error': 'Message is required'}, 400
            
            if not channels:
                return {'error': 'At least one notification channel is required'}, 400
            
            # Validate channels and recipient info
            validation_errors = self._validate_notification_request(channels, recipient_info)
            if validation_errors:
                return {'error': 'Validation failed', 'details': validation_errors}, 400
            
            logger.info(f"Sending notification via channels: {channels}")
            
            # Send notification through each channel
            delivery_results = {}
            
            for channel in channels:
                try:
                    if channel == 'email':
                        result = self._send_email_notification(
                            recipient_info.get('email'),
                            message,
                            notification_type,
                            priority
                        )
                    elif channel == 'sms':
                        result = self._send_sms_notification(
                            recipient_info.get('phone'),
                            message,
                            notification_type
                        )
                    elif channel == 'push':
                        result = self._send_push_notification(
                            recipient_info.get('device_token', user_id),
                            message,
                            notification_type
                        )
                    else:
                        result = {'success': False, 'error': f'Unknown channel: {channel}'}
                    
                    delivery_results[channel] = result
                    
                except Exception as e:
                    logger.error(f"Failed to send {channel} notification: {str(e)}")
                    delivery_results[channel] = {
                        'success': False,
                        'error': str(e)
                    }
            
            # Determine overall success
            successful_channels = [ch for ch, result in delivery_results.items() if result.get('success')]
            overall_success = len(successful_channels) > 0
            
            # Log notification attempt
            notification_record = {
                'id': f"notif_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{user_id or 'anonymous'}",
                'user_id': user_id,
                'message': message,
                'type': notification_type,
                'channels': channels,
                'successful_channels': successful_channels,
                'priority': priority,
                'timestamp': datetime.utcnow().isoformat(),
                'delivery_results': delivery_results
            }
            
            return {
                'status': 'success' if overall_success else 'partial_failure',
                'notification_id': notification_record['id'],
                'successful_channels': successful_channels,
                'failed_channels': [ch for ch in channels if ch not in successful_channels],
                'delivery_results': delivery_results,
                'timestamp': notification_record['timestamp']
            }
            
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            return {'error': 'Failed to send notification'}, 500
    
    def put(self, user_id):
        """Update notification preferences for a user"""
        try:
            data = request.get_json()
            if not data:
                return {'error': 'No data provided'}, 400
            
            # Extract preference updates
            preferences = data.get('preferences', {})
            
            # Mock preference update for demo
            updated_preferences = {
                'user_id': user_id,
                'email_alerts': preferences.get('email_alerts', True),
                'sms_alerts': preferences.get('sms_alerts', False),
                'push_alerts': preferences.get('push_alerts', True),
                'alert_threshold': preferences.get('alert_threshold', 100),
                'quiet_hours': preferences.get('quiet_hours', {'start': '22:00', 'end': '08:00'}),
                'notification_frequency': preferences.get('notification_frequency', 'immediate'),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Updated notification preferences for user {user_id}")
            
            return {
                'status': 'success',
                'user_id': user_id,
                'preferences': updated_preferences
            }
            
        except Exception as e:
            logger.error(f"Error updating notification preferences: {str(e)}")
            return {'error': 'Failed to update preferences'}, 500
    
    def delete(self, user_id):
        """Delete notification or unsubscribe user"""
        try:
            notification_id = request.args.get('notification_id')
            
            if notification_id:
                # Delete specific notification
                logger.info(f"Deleting notification {notification_id} for user {user_id}")
                return {
                    'status': 'success',
                    'message': f'Notification {notification_id} deleted'
                }
            else:
                # Unsubscribe user from all notifications
                logger.info(f"Unsubscribing user {user_id} from all notifications")
                return {
                    'status': 'success',
                    'message': f'User {user_id} unsubscribed from all notifications'
                }
                
        except Exception as e:
            logger.error(f"Error deleting notification: {str(e)}")
            return {'error': 'Failed to delete notification'}, 500
    
    def _validate_notification_request(self, channels, recipient_info):
        """Validate notification request"""
        errors = []
        
        for channel in channels:
            if channel == 'email':
                email = recipient_info.get('email')
                if not email:
                    errors.append("Email address required for email notifications")
                elif not validate_email(email):
                    errors.append("Invalid email address")
            
            elif channel == 'sms':
                phone = recipient_info.get('phone')
                if not phone:
                    errors.append("Phone number required for SMS notifications")
                elif not validate_phone(phone):
                    errors.append("Invalid phone number")
            
            elif channel == 'push':
                device_token = recipient_info.get('device_token')
                if not device_token:
                    errors.append("Device token required for push notifications")
        
        return errors
    
    def _send_email_notification(self, email, message, notification_type, priority):
        """Send email notification (mock implementation)"""
        # In production, integrate with SendGrid, AWS SES, etc.
        logger.info(f"Sending email notification to {email}")
        
        return {
            'success': True,
            'message_id': f"email_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            'delivery_time': datetime.utcnow().isoformat()
        }
    
    def _send_sms_notification(self, phone, message, notification_type):
        """Send SMS notification (mock implementation)"""
        # In production, integrate with Twilio, AWS SNS, etc.
        logger.info(f"Sending SMS notification to {phone}")
        
        return {
            'success': True,
            'message_id': f"sms_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            'delivery_time': datetime.utcnow().isoformat()
        }
    
    def _send_push_notification(self, device_token, message, notification_type):
        """Send push notification (mock implementation)"""
        # In production, integrate with FCM, APNs, etc.
        logger.info(f"Sending push notification to device {device_token}")
        
        return {
            'success': True,
            'message_id': f"push_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            'delivery_time': datetime.utcnow().isoformat()
        }
    
    def _get_mock_notifications(self, user_id, notification_type, limit):
        """Generate mock notification history"""
        import random
        
        notifications = []
        for i in range(min(limit, 20)):  # Limit to 20 for demo
            timestamp = datetime.utcnow() - timedelta(hours=random.randint(1, 168))  # Last week
            
            notification = {
                'id': f"notif_{timestamp.strftime('%Y%m%d_%H%M%S')}_{i}",
                'type': random.choice(['air_quality_alert', 'forecast_update', 'weekly_summary']),
                'message': random.choice([
                    "Air quality alert: AQI exceeded 150 in your area",
                    "Daily air quality forecast update available",
                    "Weekly air quality summary: Moderate conditions expected",
                    "Poor air quality expected tomorrow - consider indoor activities"
                ]),
                'priority': random.choice(['normal', 'high', 'urgent']),
                'channels': random.choice([['email'], ['sms'], ['email', 'push']]),
                'status': random.choice(['delivered', 'delivered', 'delivered', 'failed']),
                'timestamp': timestamp.isoformat(),
                'read': random.choice([True, False])
            }
            
            if notification_type == 'all' or notification['type'] == notification_type:
                notifications.append(notification)
        
        return sorted(notifications, key=lambda x: x['timestamp'], reverse=True)
