import pandas as pd, numpy as np, joblib, os
from lightgbm import LGBMRegressor
from sklearn.model_selection import train_test_split

DATA_DIR  = "data"
MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

df = pd.read_csv(os.path.join(DATA_DIR, "merged.csv"), parse_dates=["date"])

# ---------- lag feature (yesterday’s sales) ----------
df = df.sort_values(["store_id", "product_id", "date"])
df["lag_1"] = df.groupby(["store_id", "product_id"])["units_sold"].shift(1)
df = df.dropna(subset=["lag_1"])

# ---------- feature/target split ----------
features = ["temperature", "rain", "is_holiday", "day_of_week", "month", "lag_1"]
X = df[features]
y = df["units_sold"]

# ---------- train/test split ----------
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# ---------- train model ----------
model = LGBMRegressor(n_estimators=300, learning_rate=0.05, random_state=42)
model.fit(X_train, y_train)

print("Train R²:", round(model.score(X_train, y_train), 3))
print("Test  R²:", round(model.score(X_test, y_test), 3))

# ---------- save model ----------
joblib.dump(model, os.path.join(MODEL_DIR, "sales_model.pkl"))
print("✅ model saved → models/sales_model.pkl")
