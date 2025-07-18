# src/evaluate_model.py
import pandas as pd, numpy as np, joblib, os, json
from sklearn.metrics import mean_absolute_error, mean_squared_error
from lightgbm import LGBMRegressor
from datetime import timedelta

DATA_DIR = "data"
MODEL_DIR = "models"
OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Load Data ─────────────────────────────────────────────
df = pd.read_csv(os.path.join(DATA_DIR, "merged.csv"), parse_dates=["date"])
df = df.sort_values(["store_id", "product_id", "date"])

# ── Hold out last 7 days for validation ───────────────────
latest_date = df["date"].max()
val_start   = latest_date - timedelta(days=6)
df_train = df[df["date"] < val_start].copy()
df_val   = df[df["date"] >= val_start].copy()

# ── Load model ─────────────────────────────────────────────
model: LGBMRegressor = joblib.load(os.path.join(MODEL_DIR, "sales_model.pkl"))

# ── Prepare features ───────────────────────────────────────
FEATURES = ["temperature", "rain", "is_holiday", "day_of_week", "month", "lag_1"]

def prepare_features(df):
    df["day_of_week"] = df["date"].dt.weekday
    df["month"] = df["date"].dt.month
    df = df.sort_values(["store_id", "product_id", "date"])
    df["lag_1"] = df.groupby(["store_id", "product_id"])['units_sold'].shift(1)
    df = df.dropna(subset=["lag_1"])  # drop first day rows with no lag
    return df

val_features = prepare_features(df_val)

# ── Predict ────────────────────────────────────────────────
y_true = val_features["units_sold"].values
y_pred = model.predict(val_features[FEATURES])

# ── Metrics ────────────────────────────────────────────────
mae  = mean_absolute_error(y_true, y_pred)
rmse = mean_squared_error(y_true, y_pred) ** 0.5
mape = np.mean(np.abs((y_true - y_pred) / np.clip(y_true, 1, None))) * 100

results = {
    "MAE": round(mae, 2),
    "RMSE": round(rmse, 2),
    "MAPE": round(mape, 2)
}

# ── Save ───────────────────────────────────────────────────
with open(os.path.join(OUTPUT_DIR, "model_metrics.json"), "w") as f:
    json.dump(results, f, indent=2)

print("\n✅ Evaluation complete. Metrics saved → outputs/model_metrics.json")
print(results)
