"""
FRONTEND - Streamlit Dashboard
Displays real-time water level data with maps, charts, and alerts
"""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import folium
from streamlit_folium import st_folium
from config import API_URL
from datetime import datetime

st.set_page_config(page_title="Live Water-Stage Monitor", page_icon="🌊", layout="wide")
st.title("🌊 Live Water-Stage Monitor")
st.subheader("Real-Time Water Level Monitoring System")

# Basin Capacity: 18.7 inches = 47.5 cm
# Percentage-based Thresholds
BASIN_HEIGHT_CM = 47.5
WARN_PCT = 0.25   # 25% = 4.67 inches
ALERT_PCT = 0.50  # 50% = 9.35 inches
DANGER_PCT = 0.75 # 75% = 14.02 inches

WARN_THRESHOLD = BASIN_HEIGHT_CM * WARN_PCT
ALERT_THRESHOLD = BASIN_HEIGHT_CM * ALERT_PCT
DANGER_THRESHOLD = BASIN_HEIGHT_CM * DANGER_PCT

def fetch_data():
    """Fetch sensor data from Flask API."""
    try:
        response = requests.get(API_URL, timeout=5)
        return response.json().get("data", []) if response.status_code == 200 else []
    except requests.exceptions.RequestException:
        st.error("❌ Cannot connect to backend API. Is Flask running?")
        return []

def get_status_color(level):
    """Return status and color based on basin capacity percentage."""
    capacity = (level / BASIN_HEIGHT_CM) * 100
    if level >= DANGER_THRESHOLD:
        return f"🔴 DANGER ({capacity:.1f}%)", "red"
    elif level >= ALERT_THRESHOLD:
        return f"🟠 ALERT ({capacity:.1f}%)", "orange"
    elif level >= WARN_THRESHOLD:
        return f"🟡 WARNING ({capacity:.1f}%)", "gold"
    else:
        return f"🟢 NORMAL ({capacity:.1f}%)", "green"

def get_marker_color(level):
    """Return Folium marker color based on basin capacity percentage."""
    if level >= DANGER_THRESHOLD:
        return "red"
    elif level >= ALERT_THRESHOLD:
        return "orange"
    elif level >= WARN_THRESHOLD:
        return "yellow"
    else:
        return "green"

def create_sensor_map(df):
    """Create an interactive Folium map with sensor locations."""
    if df.empty or df[['latitude', 'longitude']].isnull().all().any():
        st.warning("No geospatial data available.")
        return None
    
    df_map = df.dropna(subset=['latitude', 'longitude'])
    if df_map.empty:
        return None
    
    center_lat = df_map['latitude'].mean()
    center_lon = df_map['longitude'].mean()
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=12, tiles="OpenStreetMap")
    
    for idx, row in df_map.iterrows():
        status_text, _ = get_status_color(row['water_level_cm'])
        marker_color = get_marker_color(row['water_level_cm'])
        
        popup_text = f"""
        <b>{row['sensor_id']}</b><br>
        Level: <b>{row['water_level_cm']} cm</b><br>
        Status: {status_text}<br>
        Time: {row['recorded_at']}
        """
        
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=folium.Popup(popup_text, max_width=250),
            tooltip=f"{row['sensor_id']}: {row['water_level_cm']} cm",
            icon=folium.Icon(color=marker_color, icon="tint", prefix="fa")
        ).add_to(m)
    
    return m

raw_data = fetch_data()

if raw_data:
    df = pd.DataFrame(raw_data)
    df['recorded_at'] = pd.to_datetime(df['recorded_at'])
    df = df.sort_values('recorded_at')
    
    latest = df.iloc[-1]
    status_text, status_color = get_status_color(latest['water_level_cm'])
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Latest Reading", f"{latest['water_level_cm']} cm", status_text, delta_color="off")
    with col2:
        avg_level = df['water_level_cm'].mean()
        st.metric("Average", f"{avg_level:.1f} cm", f"{latest['water_level_cm'] - avg_level:.1f} cm")
    with col3:
        st.metric("Peak", f"{df['water_level_cm'].max():.1f} cm")
    with col4:
        st.metric("Minimum", f"{df['water_level_cm'].min():.1f} cm")
    
    st.markdown("---")
    
    # Alerts with Capacity Percentage
    capacity = (latest['water_level_cm'] / BASIN_HEIGHT_CM) * 100
    if latest['water_level_cm'] >= DANGER_THRESHOLD:
        st.error(f"🔴 DANGER! Basin at {capacity:.1f}% capacity ({latest['water_level_cm']:.1f} cm)")
    elif latest['water_level_cm'] >= ALERT_THRESHOLD:
        st.warning(f"🟠 ALERT! Basin at {capacity:.1f}% capacity ({latest['water_level_cm']:.1f} cm)")
    elif latest['water_level_cm'] >= WARN_THRESHOLD:
        st.warning(f"🟡 WARNING! Basin at {capacity:.1f}% capacity ({latest['water_level_cm']:.1f} cm)")
    
    st.markdown("---")
    
    # Map
    st.subheader("🗺️ Sensor Location Map")
    sensor_map = create_sensor_map(df)
    if sensor_map:
        st_folium(sensor_map, width=1400, height=500)
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Water Level Trend")
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(x=df['recorded_at'], y=df['water_level_cm'], mode='lines+markers',
                                      name='Level', line=dict(color='#0066cc', width=2), fill='tozeroy'))
        fig_trend.add_hline(y=WARN_THRESHOLD, line_dash="dash", line_color="yellow", annotation_text="Warning (25%)")
        fig_trend.add_hline(y=ALERT_THRESHOLD, line_dash="dash", line_color="orange", annotation_text="Alert (50%)")
        fig_trend.add_hline(y=DANGER_THRESHOLD, line_dash="dash", line_color="red", annotation_text="Danger (75%)")
        fig_trend.update_layout(height=400)
        st.plotly_chart(fig_trend, use_container_width=True)
    
    with col2:
        st.subheader("📊 By Sensor")
        sensor_stats = df.groupby('sensor_id')['water_level_cm'].mean().reset_index()
        fig_bar = px.bar(sensor_stats, x='sensor_id', y='water_level_cm', color='water_level_cm',
                        color_continuous_scale='RdYlGn_r')
        fig_bar.update_layout(height=400)
        st.plotly_chart(fig_bar, use_container_width=True)
    
    st.markdown("---")
    
    # Statistics
    st.subheader("📋 Statistics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Readings", len(df))
    col2.metric("Active Sensors", df['sensor_id'].nunique())
    col3.metric("Duration", f"{(df['recorded_at'].max() - df['recorded_at'].min()).total_seconds() / 3600:.1f}h")
    
    st.markdown("---")
    
    # Data Table
    st.subheader("🗂️ Recent Readings")
    display_df = df[['recorded_at', 'sensor_id', 'water_level_cm']].copy()
    display_df['recorded_at'] = display_df['recorded_at'].dt.strftime('%Y-%m-%d %H:%M:%S')
    st.dataframe(display_df.sort_values('recorded_at', ascending=False), use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Export
    st.subheader("💾 Export Data")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        csv = df.to_csv(index=False)
        st.download_button("📥 Download CSV", csv,
                          file_name=f"water_levels_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                          mime="text/csv")
    
    with col2:
        try:
            api_base = API_URL.rsplit('/api/', 1)[0]
            response = requests.get(f"{api_base}/api/export/geojson", timeout=5)
            if response.status_code == 200:
                st.download_button("📍 Download GeoJSON", response.text,
                                  file_name=f"water_levels_{datetime.now().strftime('%Y%m%d_%H%M%S')}.geojson",
                                  mime="application/json")
        except:
            st.info("GeoJSON unavailable")
    
    with col3:
        st.info("💡 Import GeoJSON into QGIS for spatial analysis")
    
    st.markdown("---")
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()
    
    st.caption(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

else:
    st.warning("⏳ No data available")
    st.markdown("1. Run `python database.py`\n2. Run `python backend.py`\n3. Run `python frontend.py`\n4. Run `python simulator.py`")
