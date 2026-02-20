import streamlit as st
import requests
import pandas as pd
from config import API_URL  # This will now work perfectly

st.set_page_config(page_title="Hydro-Hazard Dashboard", page_icon="🌊")
st.title("🌊 Automated Hydro-Hazard Helper")

def fetch_data():
    """Fetch data from the centralized API URL."""
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            return response.json().get("data", [])
    except Exception as e:
        st.error(f"❌ Connection Error: {e}")
    return []

# The rest of your dashboard logic continues here...
raw_data = fetch_data()
if raw_data:
    df = pd.DataFrame(raw_data)
    st.dataframe(df)
else:
    st.info("Awaiting data from sensors...")