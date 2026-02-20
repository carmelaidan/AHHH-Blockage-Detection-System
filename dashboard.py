import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import folium
from streamlit_folium import st_folium
from config import API_URL
from datetime import datetime, timedelta

st.set_page_config(page_title="Live Water-Stage Monitor Dashboard", page_icon="🌊", layout="wide")
st.title("🌊 Live Water-Stage Monitor")
st.subheader("Real-Time Water Level Monitoring System")

# Configuration
ALERT_THRESHOLD = 50  # cm - trigger warning
DANGER_THRESHOLD = 70  # cm - trigger alert

def fetch_data():
    """Fetch sensor data from Flask API."""
    try:
        response = requests.get(API_URL, timeout=5)
        return response.json().get("data", []) if response.status_code == 200 else []
    except requests.exceptions.RequestException:
        st.error("❌ Cannot connect to backend API. Is Flask running?")
        return []

def get_status_color(level):
    """Return status and color based on water level."""
    if level >= DANGER_THRESHOLD:
        return "🔴 DANGER", "red"
    elif level >= ALERT_THRESHOLD:
        return "🟠 WARNING", "orange"
    else:
        return "🟢 NORMAL", "green"

def get_marker_color(level):
    """Return Folium marker color based on water level."""
    if level >= DANGER_THRESHOLD:
        return "red"
    elif level >= ALERT_THRESHOLD:
        return "orange"
    else:
        return "green"

def create_sensor_map(df):
    """Create an interactive Folium map with sensor locations."""
    if df.empty or df[['latitude', 'longitude']].isnull().all().any():
        st.warning("No geospatial data available. Sensors need latitude/longitude.")
        return None
    
    # Filter rows with valid coordinates
    df_map = df.dropna(subset=['latitude', 'longitude'])
    
    if df_map.empty:
        return None
    
    # Calculate center of map
    center_lat = df_map['latitude'].mean()
    center_lon = df_map['longitude'].mean()
    
    # Create map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=12,
        tiles="OpenStreetMap"
    )
    
    # Add sensor markers
    for idx, row in df_map.iterrows():
        status_text, _ = get_status_color(row['water_level_cm'])
        marker_color = get_marker_color(row['water_level_cm'])
        
        # Create popup with sensor information
        popup_text = f"""
        <b>{row['sensor_id']}</b><br>
        Water Level: <b>{row['water_level_cm']} cm</b><br>
        Status: {status_text}<br>
        Time: {row['recorded_at']}<br>
        Lat: {row['latitude']:.4f}<br>
        Lon: {row['longitude']:.4f}
        """
        
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=folium.Popup(popup_text, max_width=250),
            tooltip=f"{row['sensor_id']}: {row['water_level_cm']} cm",
            icon=folium.Icon(color=marker_color, icon="tint", prefix="fa")
        ).add_to(m)
    
    # Add a circle marker for each recent reading (last 5)
    df_recent = df_map.nlargest(5, 'recorded_at')
    for idx, row in df_recent.iterrows():
        radius = row['water_level_cm'] / 10  # Scale radius by water level
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=radius,
            popup=f"{row['sensor_id']}: {row['water_level_cm']} cm",
            color=get_marker_color(row['water_level_cm']),
            fill=True,
            fillColor=get_marker_color(row['water_level_cm']),
            fillOpacity=0.4,
            weight=2
        ).add_to(m)
    
    return m

# Fetch fresh data
raw_data = fetch_data()

if raw_data:
    df = pd.DataFrame(raw_data)
    df['recorded_at'] = pd.to_datetime(df['recorded_at'])
    df = df.sort_values('recorded_at')
    
    latest = df.iloc[-1]
    status_text, status_color = get_status_color(latest['water_level_cm'])
    
    # --- TOP METRICS ROW ---
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Latest Reading",
            value=f"{latest['water_level_cm']} cm",
            delta=status_text,
            delta_color="off"
        )
    
    with col2:
        avg_level = df['water_level_cm'].mean()
        st.metric(
            label="Average Level",
            value=f"{avg_level:.1f} cm",
            delta=f"{latest['water_level_cm'] - avg_level:.1f} cm"
        )
    
    with col3:
        max_level = df['water_level_cm'].max()
        st.metric(
            label="Peak Level",
            value=f"{max_level:.1f} cm"
        )
    
    with col4:
        min_level = df['water_level_cm'].min()
        st.metric(
            label="Minimum Level",
            value=f"{min_level:.1f} cm"
        )
    
    st.markdown("---")
    
    # --- ALERT SYSTEM ---
    if latest['water_level_cm'] >= DANGER_THRESHOLD:
        st.error(f"⚠️ **DANGER ALERT!** Water level is at {latest['water_level_cm']} cm. Immediate action required!")
    elif latest['water_level_cm'] >= ALERT_THRESHOLD:
        st.warning(f"⚠️ **WARNING!** Water level is rising. Current: {latest['water_level_cm']} cm")
    
    st.markdown("---")
    
    # --- INTERACTIVE MAP ---
    st.subheader("🗺️ Sensor Location Map")
    sensor_map = create_sensor_map(df)
    if sensor_map:
        st_folium(sensor_map, width=1400, height=500)
    else:
        st.info("Map not available. Add latitude/longitude to sensor data.")
    
    st.markdown("---")
    
    # --- CHARTS ROW ---
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Water Level Trend")
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=df['recorded_at'],
            y=df['water_level_cm'],
            mode='lines+markers',
            name='Water Level',
            line=dict(color='#0066cc', width=2),
            fill='tozeroy',
            hovertemplate='<b>%{x}</b><br>Level: %{y:.1f} cm<extra></extra>'
        ))
        fig_trend.add_hline(y=ALERT_THRESHOLD, line_dash="dash", line_color="orange", 
                           annotation_text="Warning", annotation_position="right")
        fig_trend.add_hline(y=DANGER_THRESHOLD, line_dash="dash", line_color="red",
                           annotation_text="Danger", annotation_position="right")
        fig_trend.update_layout(hovermode='x unified', height=400)
        st.plotly_chart(fig_trend, use_container_width=True)
    
    with col2:
        st.subheader("📊 Distribution by Sensor")
        sensor_stats = df.groupby('sensor_id')['water_level_cm'].agg(['mean', 'count']).reset_index()
        fig_bar = px.bar(
            sensor_stats,
            x='sensor_id',
            y='mean',
            color='mean',
            color_continuous_scale='RdYlGn_r',
            labels={'mean': 'Avg Level (cm)', 'sensor_id': 'Sensor ID'},
            hover_data={'count': True}
        )
        fig_bar.update_layout(height=400)
        st.plotly_chart(fig_bar, use_container_width=True)
    
    st.markdown("---")
    
    # --- STATISTICS SECTION ---
    st.subheader("📋 Detailed Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Readings", len(df))
    
    with col2:
        time_span = (df['recorded_at'].max() - df['recorded_at'].min()).total_seconds() / 3600
        st.metric("Duration", f"{time_span:.1f} hours" if time_span > 0 else "< 1 hour")
    
    with col3:
        sensors = df['sensor_id'].nunique()
        st.metric("Active Sensors", sensors)
    
    st.markdown("---")
    
    # --- DATA TABLE ---
    st.subheader("🗂️ Recent Readings")
    display_df = df[['recorded_at', 'sensor_id', 'water_level_cm', 'latitude', 'longitude']].copy()
    display_df['recorded_at'] = display_df['recorded_at'].dt.strftime('%Y-%m-%d %H:%M:%S')
    display_df = display_df.sort_values('recorded_at', ascending=False)
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # --- EXPORT SECTION ---
    st.markdown("---")
    st.subheader("💾 Export Data")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"water_levels_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with col2:
        try:
            api_base = API_URL.rsplit('/api/', 1)[0]  # Get base URL without endpoint
            geojson_url = f"{api_base}/api/export/geojson"
            response = requests.get(geojson_url, timeout=5)
            
            if response.status_code == 200:
                geojson_data = response.text
                st.download_button(
                    label="📍 Download GeoJSON",
                    data=geojson_data,
                    file_name=f"water_levels_{datetime.now().strftime('%Y%m%d_%H%M%S')}.geojson",
                    mime="application/json"
                )
            else:
                st.warning(f"GeoJSON unavailable (API returned {response.status_code})")
        except Exception as e:
            st.warning(f"GeoJSON export error: {str(e)[:50]}")
    
    with col3:
        st.info("💡 Tip: Import GeoJSON into QGIS for spatial analysis")
    
    # --- AUTO REFRESH ---
    st.markdown("---")
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()
    
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

else:
    st.warning("⏳ No data available. Waiting for sensor readings...")
    st.info("Steps to start monitoring:")
    st.markdown("""
    1. Run `python setup_db.py` to initialize the database
    2. Run `python app.py` to start the Flask API
    3. Run `python sim_esp32.py` to simulate sensor data
    4. Refresh this dashboard
    """)