"""
Reusable widgets and UI components for CleanSky AI
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any

def setup_page_config(
    page_title: str = "CleanSky AI",
    page_icon: str = "🌤️",
    layout: str = "wide"
):
    """Setup consistent page configuration"""
    st.set_page_config(
        page_title=page_title,
        page_icon=page_icon,
        layout=layout,
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'https://github.com/cleansky-ai/help',
            'Report a bug': 'https://github.com/cleansky-ai/issues',
            'About': """
            # CleanSky AI
            
            **NASA TEMPO Air Quality Monitoring System**
            
            Powered by NASA's Tropospheric Emissions: Monitoring of Pollution (TEMPO) 
            mission for real-time air quality monitoring across North America.
            """
        }
    )

def create_metric_card(
    title: str,
    value: str,
    delta: Optional[str] = None,
    delta_color: str = "normal",
    help_text: Optional[str] = None,
    icon: Optional[str] = None
):
    """Create a styled metric card"""
    with st.container():
        if icon:
            col1, col2 = st.columns([1, 4])
            with col1:
                st.markdown(f"<div style='font-size: 2em; text-align: center;'>{icon}</div>", 
                          unsafe_allow_html=True)
            with col2:
                st.metric(
                    label=title,
                    value=value,
                    delta=delta,
                    delta_color=delta_color,
                    help=help_text
                )
        else:
            st.metric(
                label=title,
                value=value,
                delta=delta,
                delta_color=delta_color,
                help=help_text
            )

def create_status_indicator(
    status: str,
    message: str = "",
    details: Optional[str] = None
):
    """Create a status indicator with color coding"""
    status_config = {
        'online': {'color': 'green', 'icon': '🟢', 'text': 'Online'},
        'offline': {'color': 'red', 'icon': '🔴', 'text': 'Offline'},
        'warning': {'color': 'orange', 'icon': '🟡', 'text': 'Warning'},
        'maintenance': {'color': 'blue', 'icon': '🔵', 'text': 'Maintenance'},
        'error': {'color': 'red', 'icon': '❌', 'text': 'Error'}
    }
    
    config = status_config.get(status.lower(), status_config['offline'])
    
    st.markdown(f"""
    <div style="
        display: flex;
        align-items: center;
        padding: 10px;
        border-left: 4px solid {config['color']};
        background-color: rgba(128,128,128,0.1);
        border-radius: 5px;
        margin: 5px 0;
    ">
        <span style="font-size: 1.2em; margin-right: 10px;">{config['icon']}</span>
        <div>
            <strong>{config['text']}</strong>
            {f": {message}" if message else ""}
            {f"<br><small>{details}</small>" if details else ""}
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_aqi_badge(aqi: float, size: str = "normal"):
    """Create an AQI badge with appropriate color"""
    if aqi <= 50:
        color = "#00E400"
        category = "Good"
    elif aqi <= 100:
        color = "#FFFF00"
        category = "Moderate"
    elif aqi <= 150:
        color = "#FF7E00"
        category = "Unhealthy for Sensitive"
    elif aqi <= 200:
        color = "#FF0000"
        category = "Unhealthy"
    elif aqi <= 300:
        color = "#8F3F97"
        category = "Very Unhealthy"
    else:
        color = "#7E0023"
        category = "Hazardous"
    
    font_size = "1.2em" if size == "normal" else "0.9em" if size == "small" else "1.5em"
    padding = "8px 12px" if size == "normal" else "4px 8px" if size == "small" else "12px 16px"
    
    st.markdown(f"""
    <div style="
        background-color: {color};
        color: {'white' if category in ['Unhealthy', 'Very Unhealthy', 'Hazardous'] else 'black'};
        padding: {padding};
        border-radius: 20px;
        text-align: center;
        font-weight: bold;
        font-size: {font_size};
        display: inline-block;
        margin: 2px;
    ">
        AQI {aqi:.0f} - {category}
    </div>
    """, unsafe_allow_html=True)

def create_location_selector(
    default_lat: float = 39.8283,
    default_lon: float = -98.5795,
    key: str = "location"
):
    """Create a location input widget"""
    st.markdown("#### 📍 Location Selection")
    
    # Location input method
    location_method = st.radio(
        "Select location method:",
        ["Use Coordinates", "Search by City", "Use Current Location"],
        key=f"{key}_method"
    )
    
    if location_method == "Use Coordinates":
        col1, col2 = st.columns(2)
        with col1:
            lat = st.number_input(
                "Latitude",
                value=default_lat,
                min_value=-90.0,
                max_value=90.0,
                step=0.0001,
                format="%.4f",
                key=f"{key}_lat"
            )
        with col2:
            lon = st.number_input(
                "Longitude", 
                value=default_lon,
                min_value=-180.0,
                max_value=180.0,
                step=0.0001,
                format="%.4f",
                key=f"{key}_lon"
            )
        return lat, lon
    
    elif location_method == "Search by City":
        # City search with predefined options
        cities = {
            "New York, NY": (40.7128, -74.0060),
            "Los Angeles, CA": (34.0522, -118.2437),
            "Chicago, IL": (41.8781, -87.6298),
            "Houston, TX": (29.7604, -95.3698),
            "Phoenix, AZ": (33.4484, -112.0740),
            "Philadelphia, PA": (39.9526, -75.1652),
            "San Antonio, TX": (29.4241, -98.4936),
            "San Diego, CA": (32.7157, -117.1611),
            "Dallas, TX": (32.7767, -96.7970),
            "Denver, CO": (39.7392, -104.9903)
        }
        
        selected_city = st.selectbox(
            "Select a city:",
            list(cities.keys()),
            key=f"{key}_city"
        )
        
        return cities[selected_city]
    
    else:  # Use Current Location
        st.info("🌍 Using browser geolocation (if available)")
        # For now, return default coordinates
        # In a real implementation, you would use JavaScript to get user location
        return default_lat, default_lon

def create_parameter_selector(
    available_parameters: List[str] = None,
    default_selected: List[str] = None,
    key: str = "parameters"
):
    """Create a parameter selection widget"""
    if available_parameters is None:
        available_parameters = ["PM2.5", "PM10", "O3", "NO2", "SO2", "CO"]
    
    if default_selected is None:
        default_selected = ["PM2.5", "O3", "NO2"]
    
    st.markdown("#### 🧪 Parameters to Monitor")
    
    # Parameter descriptions
    parameter_help = {
        "PM2.5": "Fine particulate matter (≤2.5 μm)",
        "PM10": "Coarse particulate matter (≤10 μm)", 
        "O3": "Ground-level ozone",
        "NO2": "Nitrogen dioxide",
        "SO2": "Sulfur dioxide",
        "CO": "Carbon monoxide",
        "HCHO": "Formaldehyde"
    }
    
    selected_parameters = []
    
    # Create checkboxes in columns
    cols = st.columns(3)
    for i, param in enumerate(available_parameters):
        with cols[i % 3]:
            if st.checkbox(
                param,
                value=param in default_selected,
                help=parameter_help.get(param, f"Monitor {param} levels"),
                key=f"{key}_{param}"
            ):
                selected_parameters.append(param)
    
    return selected_parameters

def create_time_range_selector(
    key: str = "time_range",
    include_custom: bool = True
):
    """Create a time range selection widget"""
    st.markdown("#### ⏰ Time Range")
    
    range_options = [
        "Last Hour",
        "Last 6 Hours", 
        "Last 24 Hours",
        "Last 3 Days",
        "Last Week",
        "Last Month"
    ]
    
    if include_custom:
        range_options.append("Custom Range")
    
    selected_range = st.selectbox(
        "Select time range:",
        range_options,
        index=2,  # Default to "Last 24 Hours"
        key=f"{key}_select"
    )
    
    if selected_range == "Custom Range" and include_custom:
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", key=f"{key}_start_date")
            start_time = st.time_input("Start Time", key=f"{key}_start_time")
        with col2:
            end_date = st.date_input("End Date", key=f"{key}_end_date")
            end_time = st.time_input("End Time", key=f"{key}_end_time")
        
        # Combine date and time
        from datetime import datetime, timedelta
        start_datetime = datetime.combine(start_date, start_time)
        end_datetime = datetime.combine(end_date, end_time)
        
        return "custom", start_datetime, end_datetime
    
    return selected_range, None, None

def create_notification_preferences(key: str = "notifications"):
    """Create notification preferences widget"""
    st.markdown("#### 🔔 Notification Preferences")
    
    # Enable notifications
    enable_notifications = st.checkbox(
        "Enable Notifications",
        value=True,
        key=f"{key}_enabled"
    )
    
    if enable_notifications:
        # Notification channels
        st.markdown("**Delivery Channels:**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            email_alerts = st.checkbox("Email", value=True, key=f"{key}_email")
        with col2:
            sms_alerts = st.checkbox("SMS", value=False, key=f"{key}_sms")
        with col3:
            push_alerts = st.checkbox("Push", value=True, key=f"{key}_push")
        
        # Alert thresholds
        st.markdown("**Alert Thresholds:**")
        threshold = st.select_slider(
            "AQI Threshold",
            options=[50, 75, 100, 125, 150, 175, 200],
            value=100,
            help="Receive alerts when AQI exceeds this value",
            key=f"{key}_threshold"
        )
        
        # Frequency
        frequency = st.selectbox(
            "Notification Frequency",
            ["Immediate", "Hourly Summary", "Daily Summary"],
            key=f"{key}_frequency"
        )
        
        return {
            'enabled': enable_notifications,
            'channels': {
                'email': email_alerts,
                'sms': sms_alerts,
                'push': push_alerts
            },
            'threshold': threshold,
            'frequency': frequency
        }
    
    return {'enabled': False}

def create_data_export_widget(
    data: pd.DataFrame,
    filename_prefix: str = "cleansky_data",
    key: str = "export"
):
    """Create data export widget"""
    st.markdown("#### 💾 Export Data")
    
    if data.empty:
        st.warning("No data available for export")
        return
    
    # Export format selection
    export_format = st.selectbox(
        "Export Format",
        ["CSV", "JSON", "Excel"],
        key=f"{key}_format"
    )
    
    # Date range for filename
    current_time = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"{filename_prefix}_{current_time}"
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**Rows:** {len(data)}")
        st.markdown(f"**Columns:** {len(data.columns)}")
    
    with col2:
        if export_format == "CSV":
            csv_data = data.to_csv(index=False)
            st.download_button(
                label="📊 Download CSV",
                data=csv_data,
                file_name=f"{filename}.csv",
                mime="text/csv",
                key=f"{key}_download"
            )
        
        elif export_format == "JSON":
            json_data = data.to_json(orient='records', indent=2)
            st.download_button(
                label="📋 Download JSON",
                data=json_data,
                file_name=f"{filename}.json",
                mime="application/json",
                key=f"{key}_download"
            )
        
        elif export_format == "Excel":
            # For Excel export, we'd need openpyxl
            st.info("Excel export requires additional setup")

def create_loading_spinner(message: str = "Loading..."):
    """Create a loading spinner with message"""
    return st.spinner(message)

def create_info_tooltip(text: str, tooltip: str):
    """Create text with hover tooltip"""
    st.markdown(f"""
    <div title="{tooltip}" style="
        display: inline-block;
        border-bottom: 1px dotted #999;
        cursor: help;
    ">
        {text}
    </div>
    """, unsafe_allow_html=True)

def create_progress_bar(
    value: float,
    max_value: float = 100,
    label: str = "",
    color: str = "blue"
):
    """Create a styled progress bar"""
    percentage = min(100, max(0, (value / max_value) * 100))
    
    color_map = {
        'blue': '#1f77b4',
        'green': '#2ecc71',
        'red': '#e74c3c',
        'orange': '#f39c12',
        'purple': '#9b59b6'
    }
    
    bar_color = color_map.get(color, color)
    
    st.markdown(f"""
    <div style="margin: 10px 0;">
        <div style="font-weight: bold; margin-bottom: 5px;">{label}</div>
        <div style="
            width: 100%;
            height: 20px;
            background-color: #f0f0f0;
            border-radius: 10px;
            overflow: hidden;
        ">
            <div style="
                width: {percentage}%;
                height: 100%;
                background-color: {bar_color};
                border-radius: 10px;
                transition: width 0.3s ease;
            "></div>
        </div>
        <div style="text-align: right; font-size: 0.9em; color: #666; margin-top: 2px;">
            {value:.1f} / {max_value}
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_alert_box(
    message: str,
    alert_type: str = "info",
    dismissible: bool = False,
    key: str = None
):
    """Create a styled alert box"""
    alert_configs = {
        'info': {'color': '#d1ecf1', 'border': '#bee5eb', 'text': '#0c5460', 'icon': 'ℹ️'},
        'success': {'color': '#d4edda', 'border': '#c3e6cb', 'text': '#155724', 'icon': '✅'},
        'warning': {'color': '#fff3cd', 'border': '#ffeeba', 'text': '#856404', 'icon': '⚠️'},
        'error': {'color': '#f8d7da', 'border': '#f5c6cb', 'text': '#721c24', 'icon': '❌'}
    }
    
    config = alert_configs.get(alert_type, alert_configs['info'])
    
    if dismissible and key:
        if st.session_state.get(f"alert_dismissed_{key}", False):
            return
        
        dismiss_key = f"alert_dismiss_{key}"
    else:
        dismiss_key = None
    
    alert_html = f"""
    <div style="
        background-color: {config['color']};
        border: 1px solid {config['border']};
        color: {config['text']};
        padding: 12px 20px;
        border-radius: 8px;
        margin: 10px 0;
        display: flex;
        align-items: center;
    ">
        <span style="font-size: 1.2em; margin-right: 10px;">{config['icon']}</span>
        <div style="flex: 1;">{message}</div>
    </div>
    """
    
    st.markdown(alert_html, unsafe_allow_html=True)
    
    if dismissible and key:
        if st.button("✕", key=dismiss_key, help="Dismiss"):
            st.session_state[f"alert_dismissed_{key}"] = True
            st.rerun()

def create_collapsible_section(title: str, content_func, expanded: bool = False, key: str = None):
    """Create a collapsible section"""
    with st.expander(title, expanded=expanded):
        content_func()

def create_tabs_widget(tab_data: Dict[str, callable], key: str = "tabs"):
    """Create a tabs widget with content functions"""
    tab_names = list(tab_data.keys())
    
    tabs = st.tabs(tab_names)
    
    for i, (tab_name, content_func) in enumerate(tab_data.items()):
        with tabs[i]:
            content_func()

def create_sidebar_filters(
    show_location: bool = True,
    show_parameters: bool = True, 
    show_time_range: bool = True,
    show_notifications: bool = False
):
    """Create standardized sidebar filters"""
    with st.sidebar:
        st.markdown("### 🎛️ Filters & Settings")
        
        filters = {}
        
        if show_location:
            st.markdown("---")
            lat, lon = create_location_selector()
            filters['location'] = (lat, lon)
        
        if show_parameters:
            st.markdown("---")
            parameters = create_parameter_selector()
            filters['parameters'] = parameters
        
        if show_time_range:
            st.markdown("---")
            time_range, start_time, end_time = create_time_range_selector()
            filters['time_range'] = {
                'range': time_range,
                'start': start_time,
                'end': end_time
            }
        
        if show_notifications:
            st.markdown("---")
            notifications = create_notification_preferences()
            filters['notifications'] = notifications
        
        return filters
