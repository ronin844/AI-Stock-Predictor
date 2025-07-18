import pandas as pd
import joblib

model = joblib.load("models/demand_rf.pkl")
print("✅ Model loaded")

# Match exactly the same features used in training
sample = pd.DataFrame([{
    "temperature": 30,
    "rain": 0,                # used instead of 'humidity'
    "is_holiday": 0,
    "day_of_week": 2,
    "month": 6,
    "lag_1": 100              # synthetic lagged sales value
}])

prediction = model.predict(sample)
print("📈 Predicted sales:", prediction[0])
