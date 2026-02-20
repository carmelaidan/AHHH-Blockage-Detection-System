# 🌊 Hydro-Hazard Helper
**IoT Flood Monitoring System**

## Quick Start

```powershell
# 1. Initialize database
python database.py

# 2. Start backend (Terminal 1)
python backend.py

# 3. Start frontend (Terminal 2)
streamlit run frontend.py

# 4. Test simulator (Terminal 3)
python simulator.py
```

**Dashboard:** http://localhost:8501

## 5 Core Files
- **backend.py** - Flask API + Database
- **frontend.py** - Streamlit Dashboard
- **database.py** - DB Setup
- **hardware.ino** - ESP32 Firmware
- **docs.md** - Full Documentation

See `docs.md` for complete guide.