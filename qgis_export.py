import requests
import json
from config import API_URL

def download_geojson(output_file="water_levels.geojson"):
    """Download GeoJSON data from Flask API and save for QGIS."""
    try:
        response = requests.get(f"{API_URL.replace('/api/water-level', '')}/api/export/geojson")
        
        if response.status_code == 200:
            geojson_data = response.json()
            with open(output_file, 'w') as f:
                json.dump(geojson_data, f, indent=2)
            print(f"✅ GeoJSON exported to {output_file}")
            print("📍 Open this file in QGIS: Layer > Add Layer > Add Vector Layer")
        else:
            print(f"❌ Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Export failed: {e}")

if __name__ == "__main__":
    download_geojson()
