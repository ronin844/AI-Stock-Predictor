import pandas as pd
import numpy as np
import os
import requests
from datetime import datetime

np.random.seed(42)
os.makedirs("data", exist_ok=True)

# 1. Synthetic Sales Data  (now with LOW‑DEMAND pockets)
stores   = [f"store_{i}"   for i in range(1, 6)]
products = [f"product_{j}" for j in range(1, 7)]
dates    = pd.date_range(start="2024-01-01", end="2024-06-30")

sales_rows = []
low_demand_combos = {                       # 👈  these will sell ~70 % less
    ("store_3", "product_2"),
    ("store_4", "product_3"),
    ("store_5", "product_1"),
}

for date in dates:
    for store in stores:
        for product in products:
            base   = np.random.randint(10, 50)
            fluct  = np.random.normal(0, 5)
            units  = max(0, int(base + fluct))

            # ↓ shrink units_sold for chosen low‑demand combos
            if (store, product) in low_demand_combos:
                units = max(1, int(units * 0.3))       # 70 % reduction

            sales_rows.append([date.strftime("%Y-%m-%d"),
                               store, product, units])

sales_df = pd.DataFrame(
    sales_rows, columns=["date", "store_id", "product_id", "units_sold"]
)
sales_df.to_csv("data/sales.csv", index=False)
print("✅ sales.csv saved with mixed demand levels")

# 2. Holidays via Calendarific API


CALENDARIFIC_API_KEY = "1P5wWw9Z78TPuBg11jAmPo4wcZ2WOBis"  # <-- REPLACE THIS

params = {
    "api_key": CALENDARIFIC_API_KEY,
    "country": "IN",
    "year": 2024,
    "type": "national"
}
try:
    response = requests.get("https://calendarific.com/api/v2/holidays", params=params)
    response.raise_for_status()
    holidays = response.json()["response"]["holidays"]
    
    holidays_df = pd.DataFrame({
        "date": [h["date"]["iso"] for h in holidays],
        "is_holiday": 1
    })
    holidays_df.to_csv("data/holidays.csv", index=False)
    print("✅ holidays.csv saved via Calendarific")
except Exception as e:
    print("❌ Holiday API failed:", e)
    holidays_df = pd.DataFrame(columns=["date", "is_holiday"])
    holidays_df.to_csv("data/holidays.csv", index=False)
    print("✅ Empty holidays.csv fallback saved")
# ------------------------------------------------
# 3. WEATHER  (API + full per‑store coverage)
# ------------------------------------------------
API_KEY  = "d22afca047869596edf316503c4241a6"
CITY     = "Bhopal"

resp = requests.get(
    "https://api.openweathermap.org/data/2.5/forecast",
    params={"q": CITY, "appid": API_KEY, "units": "metric"}
)
resp.raise_for_status()
fc = resp.json()["list"]

weather_rows = []

def add_rows(date_str, temp, rain):
    """add one weather row for *every* store for a given date"""
    for store in stores:
        weather_rows.append([date_str, store, round(temp, 1), rain])

# ❶ OpenWeather forecast → average per day → replicate per store
daily_fc = {}
for e in fc:
    d = datetime.fromtimestamp(e["dt"]).strftime("%Y-%m-%d")
    t = e["main"]["temp"]
    r = e.get("rain", {}).get("3h", 0) or 0
    daily_fc.setdefault(d, []).append((t, r))

for d, vals in daily_fc.items():
    temps, rains = zip(*vals)
    add_rows(d, np.mean(temps), np.mean(rains))

# ❷ Synthetic historical weather (you already did this, but per store)
past_dates = [d for d in dates if d < datetime.now()]
for dt in past_dates:
    temp = np.random.normal(25, 5)
    rain = np.random.choice([0, 1], p=[0.8, 0.2])
    add_rows(dt.strftime("%Y-%m-%d"), temp, rain)

# ❸ NEW: synthetic rows for 01–07 Jul 2024 (the forecast gap)
gap_start = pd.to_datetime(sales_df["date"].max()) # 2024‑06‑30
gap_future = pd.date_range(gap_start + pd.Timedelta(days=1), periods=7)
for dt in gap_future:
    temp = np.random.normal(30, 3)
    rain = np.random.choice([0, 1], p=[0.7, 0.3])
    add_rows(dt.strftime("%Y-%m-%d"), temp, rain)

weather_df = pd.DataFrame(
    weather_rows, columns=["date", "store_id", "temperature", "rain"]
)
weather_df.to_csv("data/weather.csv", index=False)
print("✅ weather.csv saved with complete per‑store coverage")
