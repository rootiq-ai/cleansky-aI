"""
Alert and notification components for CleanSky AI
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json

def create_alert_banner(
    message: str,
    severity: str = "info",
    dismissible: bool = True,
    auto_dismiss: int = None,
    key: str = None
):
    """
    Create an alert banner at the top of the page
    
    Args:
        message: Alert message
        severity: Alert severity (info, success, warning, error, critical)
        dismissible: Whether user can dismiss the alert
        auto_dismiss: Auto dismiss after N seconds
        key: Unique key for the alert
    """
    # Alert configurations
    alert_configs = {
        'info': {
            'bg_color': '#d1ecf1',
            'border_color': '#b8daff',
            'text_color': '#0c5460',
            'icon': 'ℹ️'
        },
        'success': {
            'bg_color': '#d4edda',
            'border_color': '#c3e6cb',
            'text_color': '#155724',
            'icon': '✅'
        },
        'warning': {
            'bg_color': '#fff3cd',
            'border_color': '#ffeaa7',
            'text_color': '#856404',
            'icon': '⚠️'
        },
        'error': {
            'bg_color': '#f8d7da',
            'border_color': '#f5c6cb',
            'text_color': '#721c24',
            'icon': '❌'
        },
        'critical': {
            'bg_color': '#f8d7da',
            'border_color': '#dc3545',
            'text_color': '#721c24',
            'icon': '🚨'
        }
    }
    
    config = alert_configs.get(severity, alert_configs['info'])
    
    # Check if alert is dismissed
    dismiss_key = f"alert_dismissed_{key}" if key else None
    if dismissible and dismiss_key and st.session_state.get(dismiss_key, False):
        return
    
    # Create alert container
    alert_container = st.container()
    
    with alert_container:
        col1, col2 = st.columns([20, 1] if dismissible else [1])
        
        with col1:
            st.markdown(f"""
            <div style="
                background-color: {config['bg_color']};
                border: 2px solid {config['border_color']};
                border-radius: 8px;
                padding: 15px 20px;
                margin: 10px 0;
                color: {config['text_color']};
                display: flex;
                align-items: center;
                font-weight: 500;
            ">
                <span style="font-size: 1.5em; margin-right: 15px;">{config['icon']}</span>
                <div style="flex: 1;">
                    {message}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        if dismissible:
            with col2:
                if st.button("✕", key=f"dismiss_{key}", help="Dismiss alert"):
                    if dismiss_key:
                        st.session_state[dismiss_key] = True
                        st.rerun()
    
    # Auto dismiss functionality
    if auto_dismiss and key:
        # This would require JavaScript in a real implementation
        pass

def create_notification_center(
    notifications: List[Dict[str, Any]],
    max_display: int = 5,
    show_filters: bool = True
):
    """
    Create a notification center widget
    
    Args:
        notifications: List of notification dictionaries
        max_display: Maximum number of notifications to display
        show_filters: Whether to show filter options
    """
    if not notifications:
        st.info("📭 No notifications at this time")
        return
    
    st.markdown("### 🔔 Notification Center")
    
    # Filters
    if show_filters:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            type_filter = st.selectbox(
                "Filter by Type",
                ["All"] + list(set(n.get('type', 'unknown') for n in notifications)),
                key="notif_type_filter"
            )
        
        with col2:
            severity_filter = st.selectbox(
                "Filter by Severity", 
                ["All"] + list(set(n.get('severity', 'normal') for n in notifications)),
                key="notif_severity_filter"
            )
        
        with col3:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All", "Unread", "Read"],
                key="notif_status_filter"
            )
        
        # Apply filters
        filtered_notifications = notifications.copy()
        
        if type_filter != "All":
            filtered_notifications = [n for n in filtered_notifications if n.get('type') == type_filter]
        
        if severity_filter != "All":
            filtered_notifications = [n for n in filtered_notifications if n.get('severity') == severity_filter]
        
        if status_filter == "Unread":
            filtered_notifications = [n for n in filtered_notifications if not n.get('read', False)]
        elif status_filter == "Read":
            filtered_notifications = [n for n in filtered_notifications if n.get('read', False)]
    else:
        filtered_notifications = notifications
    
    # Display notifications
    display_notifications = filtered_notifications[:max_display]
    
    for i, notification in enumerate(display_notifications):
        create_notification_card(notification, key=f"notif_{i}")
    
    # Show more button
    if len(filtered_notifications) > max_display:
        if st.button(f"Show {len(filtered_notifications) - max_display} more notifications"):
            st.session_state.show_all_notifications = True

def create_notification_card(
    notification: Dict[str, Any],
    key: str = None,
    expandable: bool = True
):
    """
    Create a single notification card
    
    Args:
        notification: Notification data dictionary
        key: Unique key for the notification
        expandable: Whether the notification can be expanded
    """
    # Get notification details
    title = notification.get('title', 'Notification')
    message = notification.get('message', '')
    timestamp = notification.get('timestamp', datetime.now().isoformat())
    severity = notification.get('severity', 'normal')
    read = notification.get('read', False)
    notification_type = notification.get('type', 'info')
    
    # Severity icons and colors
    severity_config = {
        'low': {'icon': '🟢', 'color': '#28a745'},
        'normal': {'icon': '🔵', 'color': '#17a2b8'},
        'high': {'icon': '🟡', 'color': '#ffc107'},
        'critical': {'icon': '🔴', 'color': '#dc3545'}
    }
    
    config = severity_config.get(severity, severity_config['normal'])
    
    # Parse timestamp
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        time_str = dt.strftime('%m/%d %H:%M')
    except:
        time_str = timestamp
    
    # Card style based on read status
    card_style = f"""
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 15px;
    margin: 10px 0;
    background-color: {'#f8f9fa' if read else 'white'};
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    """
    
    if expandable:
        with st.expander(f"{config['icon']} {title} - {time_str}", expanded=not read):
            st.markdown(f"**Type:** {notification_type.title()}")
            st.markdown(f"**Severity:** {severity.title()}")
            st.markdown(f"**Message:** {message}")
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("Mark as Read", key=f"{key}_read", disabled=read):
                    # In real implementation, would call API
                    st.success("Marked as read")
            
            with col2:
                if st.button("Delete", key=f"{key}_delete"):
                    # In real implementation, would call API
                    st.success("Notification deleted")
            
            with col3:
                if st.button("Share", key=f"{key}_share"):
                    st.info("Share functionality not implemented")
    else:
        st.markdown(f"""
        <div style="{card_style}">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 1.2em; margin-right: 10px;">{config['icon']}</span>
                    <div>
                        <strong>{title}</strong>
                        <br>
                        <small style="color: #666;">{time_str}</small>
                    </div>
                </div>
                <div style="color: {config['color']}; font-weight: bold;">
                    {severity.upper()}
                </div>
            </div>
            <div style="margin-top: 10px; color: #555;">
                {message[:100]}{'...' if len(message) > 100 else ''}
            </div>
        </div>
        """, unsafe_allow_html=True)

def create_alert_subscription_form(key: str = "alert_subscription"):
    """Create a form for subscribing to alerts"""
    
    st.markdown("### 🔔 Alert Subscription Settings")
    
    with st.form(key=key):
        # Basic subscription settings
        enable_alerts = st.checkbox("Enable Air Quality Alerts", value=True)
        
        if enable_alerts:
            # Alert thresholds
            st.markdown("**Alert Thresholds:**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                aqi_threshold = st.slider(
                    "AQI Threshold",
                    min_value=25,
                    max_value=300,
                    value=100,
                    step=25,
                    help="Receive alerts when AQI exceeds this value"
                )
            
            with col2:
                forecast_alerts = st.checkbox("Forecast Alerts", value=True, 
                                            help="Get notified about upcoming poor air quality")
            
            # Notification preferences
            st.markdown("**Notification Channels:**")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                email_alerts = st.checkbox("Email Notifications", value=True)
                if email_alerts:
                    email_address = st.text_input("Email Address", 
                                                placeholder="your.email@example.com")
            
            with col2:
                sms_alerts = st.checkbox("SMS Notifications", value=False)
                if sms_alerts:
                    phone_number = st.text_input("Phone Number", 
                                               placeholder="+1-555-123-4567")
            
            with col3:
                push_alerts = st.checkbox("Push Notifications", value=True)
            
            # Timing preferences
            st.markdown("**Timing Preferences:**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                quiet_hours = st.checkbox("Enable Quiet Hours", value=True)
                if quiet_hours:
                    col_a, col_b = st.columns(2)
                    with col_a:
                        quiet_start = st.time_input("Quiet Start", value=datetime.strptime("22:00", "%H:%M").time())
                    with col_b:
                        quiet_end = st.time_input("Quiet End", value=datetime.strptime("08:00", "%H:%M").time())
            
            with col2:
                frequency = st.selectbox(
                    "Alert Frequency",
                    ["Immediate", "Every 15 minutes", "Hourly", "Daily summary"]
                )
            
            # Location settings
            st.markdown("**Location Settings:**")
            
            location_alerts = st.multiselect(
                "Alert Locations",
                ["Current Location", "Home", "Work", "Custom Location"],
                default=["Current Location"]
            )
            
            if "Custom Location" in location_alerts:
                custom_lat = st.number_input("Custom Latitude", value=39.8283)
                custom_lon = st.number_input("Custom Longitude", value=-98.5795)
        
        # Submit button
        submitted = st.form_submit_button("💾 Save Alert Preferences", type="primary")
        
        if submitted:
            # In real implementation, would save to database/API
            st.success("✅ Alert preferences saved successfully!")
            
            # Show summary
            with st.expander("📋 Subscription Summary", expanded=True):
                st.write(f"**Alerts Enabled:** {'Yes' if enable_alerts else 'No'}")
                if enable_alerts:
                    st.write(f"**AQI Threshold:** {aqi_threshold}")
                    st.write(f"**Email Alerts:** {'Yes' if email_alerts else 'No'}")
                    st.write(f"**SMS Alerts:** {'Yes' if sms_alerts else 'No'}")
                    st.write(f"**Push Alerts:** {'Yes' if push_alerts else 'No'}")
                    st.write(f"**Frequency:** {frequency}")
                    st.write(f"**Quiet Hours:** {'Yes' if quiet_hours else 'No'}")

def create_alert_history_chart(alerts_history: List[Dict[str, Any]]):
    """Create a chart showing alert history over time"""
    
    if not alerts_history:
        st.info("No alert history available")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(alerts_history)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date
    
    # Group by date and severity
    daily_counts = df.groupby(['date', 'severity']).size().reset_index(name='count')
    
    # Create stacked bar chart
    fig = px.bar(
        daily_counts,
        x='date',
        y='count',
        color='severity',
        title='Alert History - Last 30 Days',
        color_discrete_map={
            'low': '#28a745',
            'normal': '#17a2b8', 
            'high': '#ffc107',
            'critical': '#dc3545'
        }
    )
    
    fig.update_layout(
        height=400,
        xaxis_title="Date",
        yaxis_title="Number of Alerts",
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def create_alert_summary_cards(
    total_alerts: int,
    unread_alerts: int,
    critical_alerts: int,
    last_alert_time: str = None
):
    """Create summary cards for alert statistics"""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Alerts",
            value=total_alerts,
            help="Total number of alerts received"
        )
    
    with col2:
        st.metric(
            label="Unread Alerts",
            value=unread_alerts,
            delta=f"{unread_alerts} new" if unread_alerts > 0 else None,
            delta_color="inverse" if unread_alerts > 0 else "normal"
        )
    
    with col3:
        st.metric(
            label="Critical Alerts",
            value=critical_alerts,
            delta=f"{critical_alerts} urgent" if critical_alerts > 0 else "All clear",
            delta_color="inverse" if critical_alerts > 0 else "normal"
        )
    
    with col4:
        if last_alert_time:
            try:
                dt = datetime.fromisoformat(last_alert_time.replace('Z', '+00:00'))
                time_ago = datetime.now(dt.tzinfo) - dt
                if time_ago.days > 0:
                    last_alert_str = f"{time_ago.days}d ago"
                elif time_ago.seconds > 3600:
                    last_alert_str = f"{time_ago.seconds//3600}h ago"
                else:
                    last_alert_str = f"{time_ago.seconds//60}m ago"
            except:
                last_alert_str = "Unknown"
        else:
            last_alert_str = "No alerts"
        
        st.metric(
            label="Last Alert",
            value=last_alert_str,
            help="Time since last alert received"
        )

def create_test_alert_interface():
    """Create interface for testing alert system"""
    
    st.markdown("### 🧪 Test Alert System")
    
    with st.form("test_alert_form"):
        st.markdown("Use this interface to test your alert configuration:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            test_type = st.selectbox(
                "Alert Type",
                ["Air Quality Alert", "Forecast Warning", "System Notification", "Test Message"]
            )
            
            test_severity = st.selectbox(
                "Severity Level",
                ["Low", "Normal", "High", "Critical"]
            )
        
        with col2:
            test_channels = st.multiselect(
                "Test Channels",
                ["Email", "SMS", "Push Notification"],
                default=["Email"]
            )
            
            test_message = st.text_area(
                "Custom Message",
                value="This is a test alert from CleanSky AI",
                help="Custom message for the test alert"
            )
        
        # Submit test
        if st.form_submit_button("🚀 Send Test Alert", type="primary"):
            with st.spinner("Sending test alert..."):
                # Simulate API call
                import time
                time.sleep(2)
                
                st.success(f"✅ Test alert sent successfully!")
                
                # Show delivery details
                with st.expander("📋 Delivery Details"):
                    st.write(f"**Type:** {test_type}")
                    st.write(f"**Severity:** {test_severity}")
                    st.write(f"**Channels:** {', '.join(test_channels)}")
                    st.write(f"**Message:** {test_message}")
                    st.write(f"**Sent at:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def show_alert_troubleshooting():
    """Show alert troubleshooting tips"""
    
    with st.expander("🛠️ Alert Troubleshooting"):
        st.markdown("""
        **Not receiving alerts?** Try these troubleshooting steps:
        
        1. **Check your subscription settings**
           - Verify alerts are enabled
           - Check your AQI threshold settings
           - Ensure you have notification channels selected
        
        2. **Verify contact information**
           - Email address is correct and accessible
           - Phone number is valid and can receive SMS
           - Push notifications are enabled in your browser
        
        3. **Check spam/junk folders**
           - CleanSky AI emails might be filtered
           - Add cleansky-ai.org to your trusted senders
        
        4. **Test your configuration**
           - Use the test alert feature above
           - Verify delivery to all selected channels
        
        5. **Contact support**
           - If issues persist, contact our support team
           - Include your user ID and subscription details
        
        **Common Issues:**
        - Quiet hours blocking notifications
        - Invalid email/phone number format
        - Browser blocking push notifications
        - Network connectivity issues
        """)

def create_alert_analytics_dashboard(analytics_data: Dict[str, Any]):
    """Create analytics dashboard for alert performance"""
    
    st.markdown("### 📈 Alert Analytics")
    
    if not analytics_data:
        st.info("No analytics data available")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Delivery Rate", f"{analytics_data.get('delivery_rate', 0):.1f}%")
    
    with col2:
        st.metric("Open Rate", f"{analytics_data.get('open_rate', 0):.1f}%")
    
    with col3:
        st.metric("Response Rate", f"{analytics_data.get('response_rate', 0):.1f}%")
    
    with col4:
        st.metric("False Positive Rate", f"{analytics_data.get('false_positive_rate', 0):.1f}%")
    
    # Channel performance
    if 'channel_performance' in analytics_data:
        st.markdown("#### 📊 Channel Performance")
        
        channel_data = analytics_data['channel_performance']
        
        # Create performance comparison chart
        channels = list(channel_data.keys())
        delivery_rates = [channel_data[ch].get('delivery_rate', 0) for ch in channels]
        open_rates = [channel_data[ch].get('open_rate', 0) for ch in channels]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Delivery Rate',
            x=channels,
            y=delivery_rates,
            marker_color='lightblue'
        ))
        
        fig.add_trace(go.Bar(
            name='Open Rate',
            x=channels,
            y=open_rates,
            marker_color='lightcoral'
        ))
        
        fig.update_layout(
            title='Alert Channel Performance',
            xaxis_title='Channel',
            yaxis_title='Rate (%)',
            barmode='group',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Alert timing analysis
    if 'timing_analysis' in analytics_data:
        st.markdown("#### ⏰ Alert Timing Analysis")
        
        timing_data = analytics_data['timing_analysis']
        
        # Best performing hours
        hours = list(range(24))
        response_rates = [timing_data.get(str(h), {}).get('response_rate', 0) for h in hours]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hours,
            y=response_rates,
            mode='lines+markers',
            name='Response Rate',
            line=dict(color='green', width=2)
        ))
        
        fig.update_layout(
            title='Alert Response Rate by Hour of Day',
            xaxis_title='Hour of Day',
            yaxis_title='Response Rate (%)',
            height=300,
            xaxis=dict(tickmode='linear', dtick=2)
        )
        
        st.plotly_chart(fig, use_container_width=True)

def create_emergency_alert_interface():
    """Create interface for emergency alerts"""
    
    st.markdown("### 🚨 Emergency Alert System")
    
    # Emergency alert types
    emergency_types = {
        "Hazardous Air Quality": {
            "description": "AQI > 300 - Immediate health risk",
            "color": "#dc3545",
            "icon": "🚨"
        },
        "Severe Weather Impact": {
            "description": "Weather conditions affecting air quality",
            "color": "#fd7e14", 
            "icon": "⛈️"
        },
        "System Failure": {
            "description": "Monitoring system malfunction",
            "color": "#6f42c1",
            "icon": "⚠️"
        },
        "Public Health Advisory": {
            "description": "Official health department alert",
            "color": "#e83e8c",
            "icon": "🏥"
        }
    }
    
    for alert_type, config in emergency_types.items():
        with st.container():
            st.markdown(f"""
            <div style="
                border: 2px solid {config['color']};
                border-radius: 10px;
                padding: 15px;
                margin: 10px 0;
                background-color: rgba(255,255,255,0.9);
            ">
                <div style="display: flex; align-items: center; margin-bottom: 10px;">
                    <span style="font-size: 1.5em; margin-right: 10px;">{config['icon']}</span>
                    <h4 style="margin: 0; color: {config['color']};">{alert_type}</h4>
                </div>
                <p style="margin: 5px 0; color: #666;">{config['description']}</p>
                <div style="margin-top: 10px;">
                    <small style="color: #888;">
                        Last triggered: Never | 
                        Active subscribers: 1,234 | 
                        Response rate: 94.2%
                    </small>
                </div>
            </div>
            """, unsafe_allow_html=True)

def create_alert_preferences_widget():
    """Create a compact alert preferences widget for sidebars"""
    
    st.markdown("#### 🔔 Quick Alert Settings")
    
    # Toggle for quick enable/disable
    alerts_enabled = st.toggle("Enable Alerts", value=True, key="quick_alerts_toggle")
    
    if alerts_enabled:
        # Quick threshold setting
        threshold = st.selectbox(
            "Alert Level",
            ["Moderate (50+)", "Unhealthy for Sensitive (100+)", "Unhealthy (150+)", "Very Unhealthy (200+)"],
            index=1,
            key="quick_threshold"
        )
        
        # Quick channel selection
        st.markdown("**Notify via:**")
        col1, col2 = st.columns(2)
        
        with col1:
            email_quick = st.checkbox("📧 Email", value=True, key="quick_email")
        with col2:
            push_quick = st.checkbox("📱 Push", value=True, key="quick_push")
        
        # Status indicator
        if email_quick or push_quick:
            st.success("✅ Alerts configured")
        else:
            st.warning("⚠️ No notification channels selected")
    else:
        st.info("🔕 Alerts disabled")

def show_recent_alerts_widget(recent_alerts: List[Dict[str, Any]], limit: int = 3):
    """Show recent alerts in a compact widget format"""
    
    st.markdown("#### 🕐 Recent Alerts")
    
    if not recent_alerts:
        st.info("No recent alerts")
        return
    
    for alert in recent_alerts[:limit]:
        severity = alert.get('severity', 'normal')
        message = alert.get('message', 'No message')
        timestamp = alert.get('timestamp', '')
        
        # Parse timestamp
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            time_ago = datetime.now(dt.tzinfo) - dt
            
            if time_ago.days > 0:
                time_str = f"{time_ago.days}d ago"
            elif time_ago.seconds > 3600:
                time_str = f"{time_ago.seconds//3600}h ago"
            else:
                time_str = f"{time_ago.seconds//60}m ago"
        except:
            time_str = "Unknown"
        
        # Severity styling
        severity_colors = {
            'low': '#28a745',
            'normal': '#17a2b8',
            'high': '#ffc107', 
            'critical': '#dc3545'
        }
        
        color = severity_colors.get(severity, '#17a2b8')
        
        st.markdown(f"""
        <div style="
            border-left: 4px solid {color};
            padding: 8px 12px;
            margin: 5px 0;
            background-color: #f8f9fa;
            border-radius: 0 5px 5px 0;
        ">
            <div style="font-weight: bold; font-size: 0.9em;">
                {message[:50]}{'...' if len(message) > 50 else ''}
            </div>
            <div style="font-size: 0.8em; color: #666; margin-top: 2px;">
                {severity.title()} • {time_str}
            </div>
        </div>
        """, unsafe_allow_html=True)

def create_alert_map_integration(map_obj, alert_locations: List[Dict[str, Any]]):
    """Add alert markers to a folium map"""
    
    severity_colors = {
        'low': 'green',
        'normal': 'blue',
        'high': 'orange',
        'critical': 'red'
    }
    
    severity_icons = {
        'low': 'info-sign',
        'normal': 'bell',
        'high': 'warning-sign',
        'critical': 'fire'
    }
    
    for alert in alert_locations:
        lat = alert.get('lat', 0)
        lon = alert.get('lon', 0)
        severity = alert.get('severity', 'normal')
        message = alert.get('message', 'Alert')
        timestamp = alert.get('timestamp', '')
        
        # Create popup content
        popup_html = f"""
        <div style="width: 200px; font-family: Arial, sans-serif;">
            <h5 style="margin: 0 0 10px 0; color: {severity_colors.get(severity, 'blue')};">
                🚨 {severity.title()} Alert
            </h5>
            <p style="margin: 5px 0;"><strong>Message:</strong><br>{message}</p>
            <p style="margin: 5px 0;"><strong>Time:</strong><br>{timestamp}</p>
            <p style="margin: 5px 0;"><strong>Location:</strong><br>{lat:.4f}°, {lon:.4f}°</p>
        </div>
        """
        
        # Add marker to map
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=250),
            icon=folium.Icon(
                color=severity_colors.get(severity, 'blue'),
                icon=severity_icons.get(severity, 'bell'),
                prefix='glyphicon'
            ),
            tooltip=f"{severity.title()} Alert"
        ).add_to(map_obj)
    
    return map_obj

def create_alert_sound_settings():
    """Create sound settings for alerts"""
    
    st.markdown("#### 🔊 Sound Settings")
    
    # Enable sound
    sound_enabled = st.checkbox("Enable Alert Sounds", value=True)
    
    if sound_enabled:
        # Sound options
        sound_type = st.selectbox(
            "Alert Sound",
            ["Default Chime", "Urgent Beep", "Gentle Notification", "Custom"],
            help="Choose the sound for alert notifications"
        )
        
        if sound_type == "Custom":
            uploaded_sound = st.file_uploader(
                "Upload Custom Sound",
                type=['mp3', 'wav', 'ogg'],
                help="Upload a custom sound file for alerts"
            )
        
        # Volume control
        volume = st.slider("Volume", 0, 100, 75, help="Alert sound volume")
        
        # Test sound button
        if st.button("🔊 Test Sound"):
            st.info(f"Playing {sound_type.lower()} at {volume}% volume...")
            # In real implementation, would play the sound
    
    # Quiet hours sound override
    quiet_sound_override = st.checkbox(
        "Override sound during quiet hours",
        value=False,
        help="Play sounds even during quiet hours for critical alerts"
    )
    
    return {
        'enabled': sound_enabled,
        'type': sound_type if sound_enabled else None,
        'volume': volume if sound_enabled else 0,
        'quiet_override': quiet_sound_override
    }

def create_mobile_alert_settings():
    """Create mobile-specific alert settings"""
    
    st.markdown("#### 📱 Mobile Settings")
    
    # Push notification settings
    push_enabled = st.checkbox("Push Notifications", value=True)
    
    if push_enabled:
        # Notification priority
        priority = st.selectbox(
            "Notification Priority",
            ["Low", "Normal", "High", "Urgent"],
            index=1,
            help="Higher priority notifications are more likely to be delivered immediately"
        )
        
        # Vibration settings
        vibration = st.checkbox("Vibration", value=True)
        
        # Lock screen display
        lock_screen = st.checkbox("Show on Lock Screen", value=True)
        
        # Badge count
        badge_count = st.checkbox("App Badge Count", value=True)
    
    # Mobile data usage
    st.markdown("**Data Usage:**")
    wifi_only = st.checkbox(
        "Download alert data only on WiFi",
        value=False,
        help="Reduce mobile data usage by downloading detailed alert data only when connected to WiFi"
    )
    
    return {
        'push_enabled': push_enabled,
        'priority': priority if push_enabled else None,
        'vibration': vibration if push_enabled else False,
        'lock_screen': lock_screen if push_enabled else False,
        'badge_count': badge_count if push_enabled else False,
        'wifi_only': wifi_only
    }
