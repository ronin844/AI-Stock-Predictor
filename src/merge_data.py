import pandas as pd
import os

# ---------- paths ----------
DATA_DIR = "data"
sales_fp    = os.path.join(DATA_DIR, "sales.csv")
weather_fp  = os.path.join(DATA_DIR, "weather.csv")
holiday_fp  = os.path.join(DATA_DIR, "holidays.csv")
out_fp      = os.path.join(DATA_DIR, "merged.csv")

# ---------- load ----------
sales   = pd.read_csv(sales_fp , parse_dates=["date"])
weather = pd.read_csv(weather_fp, parse_dates=["date"])
hols    = pd.read_csv(holiday_fp, parse_dates=["date"])

# ensure consistent dtypes
hols["is_holiday"] = 1         # already 1/0 but keeps dtype int
weather["rain"]    = weather["rain"].fillna(0)

# ---------- merge ----------
df = (
    sales
    .merge(weather, on=["date", "store_id"], how="left")
    .merge(hols,      on="date",              how="left")
    .fillna({"is_holiday":0})                # non‑holiday days → 0
)

# ---------- basic date features ----------
df["day_of_week"] = df["date"].dt.dayofweek          # 0=Mon
df["month"]       = df["date"].dt.month

df.to_csv(out_fp, index=False)
print(f"✅ merged.csv saved → {out_fp}")
print(df.head())
