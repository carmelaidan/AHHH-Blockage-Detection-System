from db_utils import export_to_geojson
import json

print("Testing GeoJSON export...")

geojson_data = export_to_geojson(limit=100)

if geojson_data:
    print("✅ GeoJSON data returned!")
    if isinstance(geojson_data, dict):
        print(f"Type: dict with {len(geojson_data.get('features', []))} features")
        print(json.dumps(geojson_data, indent=2)[:500])
    else:
        print(f"Type: {type(geojson_data)}")
        print(str(geojson_data)[:500])
else:
    print("❌ GeoJSON returned None")
