# src/forecast_and_detect.py
import pandas as pd, numpy as np, joblib, os
from datetime import timedelta
from lightgbm import LGBMRegressor   # only for type hints
import subprocess

DATA_DIR   = "data"
MODEL_DIR  = "models"
OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── load -----------------------------------------------------------------
df         = pd.read_csv(os.path.join(DATA_DIR, "merged.csv"),    parse_dates=["date"])
inventory  = pd.read_csv(os.path.join(DATA_DIR, "inventory.csv"))
model: LGBMRegressor = joblib.load(os.path.join(MODEL_DIR, "sales_model.pkl"))

# sort for groupby last()
df = df.sort_values(["store_id", "product_id", "date"])
latest_date  = df["date"].max()
future_dates = [latest_date + timedelta(days=i) for i in range(1, 8)]

# pre‑compute latest weather per store  (temperature & rain)
latest_weather = (
    df.sort_values("date")
      .groupby("store_id")
      .last()[["temperature", "rain"]]
      .reset_index()
)

# pre‑compute lag_1 (last known units sold per store‑product)
last_sales = (
    df.groupby(["store_id", "product_id"])["units_sold"]
      .last()
      .reset_index()
      .rename(columns={"units_sold": "lag_1"})
)

results = []

for single_date in future_dates:
    # start from last snapshot of each store‑product
    temp = last_sales.copy()
    temp["date"]        = single_date
    temp["day_of_week"] = single_date.weekday()
    temp["month"]       = single_date.month
    temp["is_holiday"]  = 0                # extend later if holiday file has future rows

    # merge latest weather
    temp = temp.merge(latest_weather, on="store_id", how="left")

    # make sure all required columns exist
    features = ["temperature", "rain", "is_holiday",
                "day_of_week", "month", "lag_1"]

    # predict
    temp["predicted_units_sold"] = model.predict(temp[features])

    # retain needed cols
    results.append(
        temp[["store_id", "product_id", "date", "predicted_units_sold"]]
    )

    # update lag_1 for next iteration
    last_sales["lag_1"] = temp["predicted_units_sold"].values

# ── combine 7‑day horizon ------------------------------------------------
forecast_df = pd.concat(results, ignore_index=True)
forecast_df.to_csv(os.path.join(OUTPUT_DIR, "forecast_daily.csv"), index=False)

# 7‑day cumulative demand
forecast_sum = (
    forecast_df.groupby(["store_id", "product_id"])["predicted_units_sold"]
    .sum()
    .reset_index()
    .rename(columns={"predicted_units_sold": "predicted_7_day_sales"})
)

# ── merge with inventory snapshot ---------------------------------------
inventory = inventory.rename(columns={"stock_level": "current_inventory"})
merged = forecast_sum.merge(
    inventory[["store_id", "product_id", "current_inventory"]],
    on=["store_id", "product_id"],
    how="left"
)

# flag status
def status(row):
    if row["predicted_7_day_sales"] > row["current_inventory"]:
        return "shortage"
    elif row["predicted_7_day_sales"] < row["current_inventory"]:
        return "surplus"
    else:
        return "balanced"

merged["status"] = merged.apply(status, axis=1)

# save predictions CSV
out_path = os.path.join(OUTPUT_DIR, "predictions.csv")
merged.to_csv(out_path, index=False)
print(f"✅ Forecast saved → {out_path}")

# ── NEW: ALERTS & SUMMARY  ----------------------------------------------
# 1) Alerts: show shortages ordered by severity
alerts = merged[merged["status"] == "shortage"].copy()
alerts["shortage_qty"] = (
    alerts["predicted_7_day_sales"] - alerts["current_inventory"]
).round().astype(int)  # ← convert to integer
alerts = alerts.sort_values("shortage_qty", ascending=False)

alerts_path = os.path.join(OUTPUT_DIR, "alerts.csv")
alerts.to_csv(alerts_path, index=False)
print(f"🚨 Alerts saved → {alerts_path}")


# Save alerts to file for email use
alerts.to_csv(os.path.join(OUTPUT_DIR, "alerts.csv"), index=False)
print("📁 Alerts saved → outputs/alerts.csv")

# Optional: trigger email

subprocess.run(["python", "src/email_alerts.py"])
