"""
Alerts and Notifications page for CleanSky AI
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from frontend.utils.api_client import APIClient

st.set_page_config(
    page_title="Alerts & Notifications - CleanSky AI",
    page_icon="🔔",
    layout="wide"
)

def generate_mock_alerts():
    """Generate mock alert history for demonstration"""
    import random
    
    alert_types = ['air_quality_alert', 'forecast_update', 'system_maintenance', 'weekly_summary']
    severities = ['low', 'medium', 'high', 'critical']
    statuses = ['delivered', 'pending', 'failed', 'read']
    
    alerts = []
    for i in range(20):
        timestamp = datetime.now() - timedelta(hours=random.randint(1, 168))  # Last week
        
        alert_type = random.choice(alert_types)
        severity = random.choice(severities)
        
        # Generate realistic messages based on type
        if alert_type == 'air_quality_alert':
            aqi = random.randint(101, 250)
            messages = [
                f"🚨 Air Quality Alert: AQI reached {aqi} in your area",
                f"⚠️ Unhealthy air quality detected - AQI: {aqi}",
                f"🔴 Poor air quality forecast - AQI expected to reach {aqi}"
            ]
        elif alert_type == 'forecast_update':
            messages = [
                "📈 Daily air quality forecast updated",
                "🌤️ Weekend air quality outlook available",
                "📊 Weekly air quality trends published"
            ]
        elif alert_type == 'system_maintenance':
            messages = [
                "🔧 Scheduled maintenance completed",
                "⚙️ System update deployed successfully",
                "🛠️ Data refresh in progress"
            ]
        else:  # weekly_summary
            messages = [
                "📋 Your weekly air quality summary is ready",
                "📊 Air quality trends for your area",
                "📈 Monthly air quality report available"
            ]
        
        alert = {
            'id': f"alert_{i+1:03d}",
            'timestamp': timestamp,
            'type': alert_type,
            'severity': severity,
            'message': random.choice(messages),
            'status': random.choice(statuses),
            'location': f"{random.uniform(30, 50):.4f}°N, {random.uniform(-120, -70):.4f}°W",
            'aqi_value': random.randint(50, 200) if alert_type == 'air_quality_alert' else None,
            'read': random.choice([True, False])
        }
        alerts.append(alert)
    
    return sorted(alerts, key=lambda x: x['timestamp'], reverse=True)

def create_alert_timeline(alerts_data):
    """Create timeline visualization of alerts"""
    
    df = pd.DataFrame(alerts_data)
    df['date'] = pd.to_datetime(df['timestamp']).dt.date
    
    # Count alerts by date and type
    timeline_data = df.groupby(['date', 'type']).size().reset_index(name='count')
    
    fig = px.bar(
        timeline_data,
        x='date',
        y='count',
        color='type',
        title='Alert Activity Over Time',
        labels={'count': 'Number of Alerts', 'date': 'Date'}
    )
    
    fig.update_layout(
        height=300,
        xaxis_title="Date",
        yaxis_title="Number of Alerts"
    )
    
    return fig

def create_severity_distribution(alerts_data):
    """Create pie chart of alert severity distribution"""
    
    df = pd.DataFrame(alerts_data)
    severity_counts = df['severity'].value_counts()
    
    # Define colors for severity levels
    colors = {
        'critical': '#ff0000',
        'high': '#ff6600',
        'medium': '#ffcc00',
        'low': '#00cc00'
    }
    
    fig = go.Figure(data=[go.Pie(
        labels=severity_counts.index,
        values=severity_counts.values,
        hole=.3,
        marker_colors=[colors.get(severity, '#cccccc') for severity in severity_counts.index]
    )])
    
    fig.update_layout(
        title="Alert Severity Distribution",
        height=300
    )
    
    return fig

def main():
    """Main alerts page"""
    
    # Initialize session state
    if 'api_client' not in st.session_state:
        st.session_state.api_client = APIClient()
    
    if 'user_id' not in st.session_state:
        st.session_state.user_id = 12345  # Mock user ID
    
    st.title("🔔 Alerts & Notifications")
    st.markdown("**Manage your air quality alerts and notification preferences**")
    
    # Sidebar - Notification Settings
    with st.sidebar:
        st.markdown("### ⚙️ Notification Settings")
        
        # Alert preferences
        st.markdown("#### 🚨 Alert Preferences")
        
        enable_alerts = st.checkbox("Enable Alerts", value=True)
        
        if enable_alerts:
            # AQI thresholds
            alert_threshold = st.select_slider(
                "Alert Threshold (AQI)",
                options=[50, 75, 100, 125, 150, 175, 200],
                value=100,
                help="Get alerts when AQI exceeds this value"
            )
            
            # Alert types
            st.markdown("**Alert Types:**")
            air_quality_alerts = st.checkbox("Air Quality Alerts", value=True)
            forecast_alerts = st.checkbox("Daily Forecasts", value=True)
            weekly_summary = st.checkbox("Weekly Summary", value=True)
            system_updates = st.checkbox("System Updates", value=False)
        
        # Notification channels
        st.markdown("#### 📱 Delivery Channels")
        
        email_notifications = st.checkbox("Email Notifications", value=True)
        sms_notifications = st.checkbox("SMS Notifications", value=False)
        push_notifications = st.checkbox("Push Notifications", value=True)
        
        if email_notifications:
            email_address = st.text_input("Email Address", value="user@example.com")
        
        if sms_notifications:
            phone_number = st.text_input("Phone Number", value="+1-555-0123")
        
        # Timing preferences
        st.markdown("#### ⏰ Timing Preferences")
        
        quiet_hours = st.checkbox("Enable Quiet Hours", value=True)
        if quiet_hours:
            quiet_start = st.time_input("Quiet Hours Start", value=datetime.strptime("22:00", "%H:%M").time())
            quiet_end = st.time_input("Quiet Hours End", value=datetime.strptime("08:00", "%H:%M").time())
        
        notification_frequency = st.selectbox(
            "Notification Frequency",
            ["Immediate", "Hourly Digest", "Daily Summary"],
            index=0
        )
        
        # Save settings button
        if st.button("💾 Save Settings", type="primary"):
            st.success("✅ Settings saved successfully!")
    
    # Main content area
    tab1, tab2, tab3 = st.tabs(["🔔 Active Alerts", "📊 Alert History", "📋 Alert Analytics"])
    
    with tab1:
        st.markdown("### 🚨 Current Active Alerts")
        
        # Mock active alerts
        active_alerts = [
            {
                'severity': 'high',
                'message': '🚨 Air Quality Alert: AQI reached 145 in your area (Los Angeles)',
                'timestamp': datetime.now() - timedelta(minutes=15),
                'location': '34.0522°N, 118.2437°W',
                'aqi': 145,
                'primary_pollutant': 'O3'
            },
            {
                'severity': 'medium', 
                'message': '⚠️ Air quality forecast shows moderate conditions tomorrow',
                'timestamp': datetime.now() - timedelta(hours=2),
                'location': '34.0522°N, 118.2437°W',
                'aqi': 85,
                'primary_pollutant': 'PM2.5'
            }
        ]
        
        if active_alerts:
            for alert in active_alerts:
                severity_colors = {
                    'critical': '🔴',
                    'high': '🟠', 
                    'medium': '🟡',
                    'low': '🟢'
                }
                
                severity_icon = severity_colors.get(alert['severity'], '⚪')
                
                with st.container():
                    col1, col2, col3 = st.columns([0.1, 0.7, 0.2])
                    
                    with col1:
                        st.markdown(f"## {severity_icon}")
                    
                    with col2:
                        st.markdown(f"**{alert['message']}**")
                        st.caption(f"📍 {alert['location']} • ⏰ {alert['timestamp'].strftime('%H:%M')} • AQI: {alert['aqi']}")
                    
                    with col3:
                        if st.button(f"✅ Acknowledge", key=f"ack_{alert['timestamp']}"):
                            st.success("Alert acknowledged")
                
                st.divider()
        else:
            st.info("🎉 No active alerts at this time. Air quality conditions are within normal ranges.")
    
    with tab2:
        st.markdown("### 📚 Alert History")
        
        # Generate mock alert history
        alerts_history = generate_mock_alerts()
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filter_type = st.selectbox(
                "Filter by Type",
                ["All", "Air Quality Alerts", "Forecast Updates", "System Updates", "Weekly Summaries"]
            )
        
        with col2:
            filter_severity = st.selectbox(
                "Filter by Severity",
                ["All", "Critical", "High", "Medium", "Low"]
            )
        
        with col3:
            time_range = st.selectbox(
                "Time Range",
                ["Last 24 Hours", "Last Week", "Last Month", "All Time"],
                index=1
            )
        
        # Apply filters
        filtered_alerts = alerts_history.copy()
        
        if filter_type != "All":
            type_mapping = {
                "Air Quality Alerts": "air_quality_alert",
                "Forecast Updates": "forecast_update", 
                "System Updates": "system_maintenance",
                "Weekly Summaries": "weekly_summary"
            }
            filtered_alerts = [a for a in filtered_alerts if a['type'] == type_mapping.get(filter_type)]
        
        if filter_severity != "All":
            filtered_alerts = [a for a in filtered_alerts if a['severity'].lower() == filter_severity.lower()]
        
        # Display alerts
        if filtered_alerts:
            for alert in filtered_alerts[:10]:  # Show last 10
                severity_colors = {
                    'critical': '🔴',
                    'high': '🟠',
                    'medium': '🟡', 
                    'low': '🟢'
                }
                
                status_colors = {
                    'delivered': '✅',
                    'pending': '⏳',
                    'failed': '❌',
                    'read': '👀'
                }
                
                severity_icon = severity_colors.get(alert['severity'], '⚪')
                status_icon = status_colors.get(alert['status'], '⚪')
                
                with st.expander(f"{severity_icon} {alert['message'][:60]}... - {alert['timestamp'].strftime('%m/%d %H:%M')}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Full Message:** {alert['message']}")
                        st.write(f"**Type:** {alert['type'].replace('_', ' ').title()}")
                        st.write(f"**Severity:** {alert['severity'].title()}")
                        
                    with col2:
                        st.write(f"**Status:** {status_icon} {alert['status'].title()}")
                        st.write(f"**Location:** {alert['location']}")
                        if alert['aqi_value']:
                            st.write(f"**AQI Value:** {alert['aqi_value']}")
                        
                    if alert['status'] == 'failed':
                        st.error("⚠️ This alert failed to deliver. Check your notification settings.")
        else:
            st.info("No alerts found matching the selected filters.")
    
    with tab3:
        st.markdown("### 📊 Alert Analytics")
        
        alerts_data = generate_mock_alerts()
        
        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        
        total_alerts = len(alerts_data)
        high_priority = len([a for a in alerts_data if a['severity'] in ['high', 'critical']])
        delivery_rate = len([a for a in alerts_data if a['status'] == 'delivered']) / total_alerts * 100
        unread_alerts = len([a for a in alerts_data if not a['read']])
        
        with col1:
            st.metric("Total Alerts", total_alerts)
        
        with col2:
            st.metric("High Priority", high_priority)
        
        with col3:
            st.metric("Delivery Rate", f"{delivery_rate:.1f}%")
        
        with col4:
            st.metric("Unread", unread_alerts)
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            timeline_chart = create_alert_timeline(alerts_data)
            st.plotly_chart(timeline_chart, use_container_width=True)
        
        with col2:
            severity_chart = create_severity_distribution(alerts_data)
            st.plotly_chart(severity_chart, use_container_width=True)
        
        # Alert effectiveness
        st.markdown("### 📈 Alert Effectiveness")
        
        effectiveness_data = {
            'Metric': ['Open Rate', 'Response Rate', 'Action Taken', 'False Positive Rate'],
            'Percentage': [85, 72, 45, 12],
            'Target': [90, 80, 60, 5]
        }
        
        df = pd.DataFrame(effectiveness_data)
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Current',
            x=df['Metric'],
            y=df['Percentage'],
            marker_color='lightblue'
        ))
        
        fig.add_trace(go.Scatter(
            name='Target',
            x=df['Metric'],
            y=df['Target'],
            mode='markers',
            marker=dict(color='red', size=10, symbol='diamond')
        ))
        
        fig.update_layout(
            title='Alert System Performance Metrics',
            yaxis_title='Percentage (%)',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Test notification section
    st.markdown("---")
    st.markdown("### 🧪 Test Notifications")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📧 Test Email Alert"):
            with st.spinner("Sending test email..."):
                # Mock API call
                success = st.session_state.api_client.send_notification(
                    user_id=st.session_state.user_id,
                    message="This is a test email notification from CleanSky AI",
                    notification_type='test',
                    channels=['email']
                )
                if success:
                    st.success("✅ Test email sent successfully!")
                else:
                    st.error("❌ Failed to send test email")
    
    with col2:
        if st.button("📱 Test SMS Alert"):
            with st.spinner("Sending test SMS..."):
                success = st.session_state.api_client.send_notification(
                    user_id=st.session_state.user_id,
                    message="CleanSky AI test SMS: Air quality monitoring active",
                    notification_type='test',
                    channels=['sms']
                )
                if success:
                    st.success("✅ Test SMS sent successfully!")
                else:
                    st.error("❌ Failed to send test SMS")
    
    with col3:
        if st.button("🔔 Test Push Notification"):
            with st.spinner("Sending test push notification..."):
                success = st.session_state.api_client.send_notification(
                    user_id=st.session_state.user_id,
                    message="CleanSky AI: Test push notification",
                    notification_type='test',
                    channels=['push']
                )
                if success:
                    st.success("✅ Test push notification sent!")
                else:
                    st.error("❌ Failed to send test push notification")

if __name__ == "__main__":
    main()
