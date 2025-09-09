"""
CleanSky AI Frontend Components Package

This package contains reusable UI components for the CleanSky AI application.
"""

from .widgets import (
    setup_page_config,
    create_metric_card,
    create_status_indicator,
    create_aqi_badge,
    create_location_selector,
    create_parameter_selector,
    create_time_range_selector,
    create_notification_preferences,
    create_data_export_widget,
    create_loading_spinner,
    create_info_tooltip,
    create_progress_bar,
    create_alert_box,
    create_sidebar_filters
)

from .charts import (
    create_aqi_gauge,
    create_time_series_chart,
    create_pollutant_comparison,
    create_wind_rose,
    create_heatmap,
    create_forecast_chart,
    create_correlation_matrix,
    create_multi_parameter_chart
)

from .maps import (
    create_base_map,
    add_air_quality_stations,
    add_tempo_overlay,
    add_heatmap_layer,
    add_wind_overlay,
    add_map_legend,
    add_layer_control,
    add_fullscreen_control,
    create_choropleth_map,
    export_map,
    get_map_bounds,
    fit_map_to_bounds
)

from .alerts import (
    create_alert_banner,
    create_notification_center,
    create_notification_card,
    create_alert_subscription_form,
    create_alert_history_chart,
    create_alert_summary_cards,
    create_test_alert_interface,
    show_alert_troubleshooting,
    create_alert_analytics_dashboard,
    create_emergency_alert_interface,
    create_alert_preferences_widget,
    show_recent_alerts_widget,
    create_alert_sound_settings,
    create_mobile_alert_settings
)

__all__ = [
    # Widget components
    'setup_page_config',
    'create_metric_card',
    'create_status_indicator', 
    'create_aqi_badge',
    'create_location_selector',
    'create_parameter_selector',
    'create_time_range_selector',
    'create_notification_preferences',
    'create_data_export_widget',
    'create_loading_spinner',
    'create_info_tooltip',
    'create_progress_bar',
    'create_alert_box',
    'create_sidebar_filters',
    
    # Chart components
    'create_aqi_gauge',
    'create_time_series_chart',
    'create_pollutant_comparison',
    'create_wind_rose',
    'create_heatmap',
    'create_forecast_chart',
    'create_correlation_matrix',
    'create_multi_parameter_chart',
    
    # Map components
    'create_base_map',
    'add_air_quality_stations',
    'add_tempo_overlay',
    'add_heatmap_layer',
    'add_wind_overlay',
    'add_map_legend',
    'add_layer_control',
    'add_fullscreen_control',
    'create_choropleth_map',
    'export_map',
    'get_map_bounds',
    'fit_map_to_bounds',
    
    # Alert components
    'create_alert_banner',
    'create_notification_center',
    'create_notification_card',
    'create_alert_subscription_form',
    'create_alert_history_chart',
    'create_alert_summary_cards',
    'create_test_alert_interface',
    'show_alert_troubleshooting',
    'create_alert_analytics_dashboard',
    'create_emergency_alert_interface',
    'create_alert_preferences_widget',
    'show_recent_alerts_widget',
    'create_alert_sound_settings',
    'create_mobile_alert_settings'
]
