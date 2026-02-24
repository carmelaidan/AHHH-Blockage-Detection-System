# A.H.H.H. Blockage Detection System
**IoT & GIS-Based Storm Drain Monitoring**

## Quick Start

```powershell
# 1. Start backend (Terminal 1) - auto-initializes database
python backend.py

# 2. Start frontend (Terminal 2)
streamlit run frontend.py

# 3. Test simulator (Terminal 3)
python simulator.py
```

**Dashboard:** http://localhost:8501

## 4 Core Files
- **backend.py** - Flask API + Database (auto-init)
- **frontend.py** - Streamlit Dashboard
- **hardware.ino** - Arduino UNO R4 Firmware
- **docs.md** - Full Documentation

See `docs.md` for complete guide.