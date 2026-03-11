# ZigZag Rotation Tracker — Streamlit App

## Setup (one-time)

```bash
pip install -r requirements.txt
```

## Run

```bash
streamlit run trading_tracker_app.py
```

Opens at: http://localhost:8501

---

## Features

- **Live NSE prices** via yfinance (15-min delayed) — auto-refreshes every 5 min
- **Signal alerts** with adjustable threshold (sidebar slider):
  - 🔴 NEAR SL ZONE — price approaching Short Term SL
  - 🟢 BREAKOUT WATCH — price approaching Short Term TGT
  - 🟡 APPROACHING SL — mild warning zone
- **Signal Score 0–100** — higher = more urgent action needed
- **Add positions** via form (Tab 2) or bulk upload Excel/CSV (Tab 3)
- **Edit / delete** existing positions
- **Summary metrics**: Total Exposure, Live P&L, Risk, Profit Potential, Active Signals

## Data

Positions stored in `positions.csv` in the same folder. Back this up periodically.

## NSE Symbols

Use the NSE ticker symbol without `.NS`, e.g.:
- `CHAMBLFERT` for Chambal Fertilisers
- `DREDGECORP` for Dredging Corporation
- `YESBANK` for Yes Bank
- `MCX` for MCX India
