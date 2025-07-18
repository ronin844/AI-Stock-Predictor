import pandas as pd
import joblib
from datetime import timedelta

sales = pd.read_csv("data/sales.csv", parse_dates=["date"])
weather = pd.read_csv("data/weather.csv", parse_dates=["date"])
holidays = pd.read_csv("data/holidays.csv", parse_dates=["date"])
model = joblib.load("models/demand_rf.pkl")

forecast_days = 7
future_dates = pd.date_range(sales["date"].max() + timedelta(days=1), periods=forecast_days)
print("➡️ Future forecast dates:", future_dates.date.tolist())

combinations = sales[["store_id", "product_id"]].drop_duplicates()
print("➡️ Store–Product combinations:", len(combinations))

predictions = []

for _, row in combinations.iterrows():
    
    store = row["store_id"]
    product = row["product_id"]

    mask = (sales["store_id"] == store) & (sales["product_id"] == product)
    subset = sales[mask]
    if subset.empty:
        print(f"⚠️ No historical sales for {store}|{product}")
        continue

    last_sales = subset.sort_values("date").iloc[-1]["units_sold"]

    for date in future_dates:
        
        w = weather[(weather["date"] == date) & (weather["store_id"] == store)]
        print(date, store, not w.empty)   # should print True for every combo

        if w.empty:
            print(f"⚠️ No weather for {store} on {date.date()}")
            continue
       # print(date, store, not w.empty)   # should print True for every combo

        # everything works: break-out for demo
        print(f"✅ Predicting for {store}|{product} on {date.date()}")

        temp = w.iloc[0]["temperature"]
        rain = w.iloc[0]["rain"]
        is_holiday = int(date in holidays["date"].values)

        X = pd.DataFrame([{
            "temperature": temp, "rain": rain,
            "is_holiday": is_holiday,
            "day_of_week": date.weekday(),
            "month": date.month,
            "lag_1": last_sales
        }])

        y_pred = model.predict(X)[0]

        print(f"  🔢 Predicted: {round(y_pred,2)} (lag_1 was {last_sales})")
        predictions.append({
            "store_id": store, "product_id": product,
            "date": date, "predicted_sales": round(y_pred, 2)
        })

        last_sales = y_pred

print("✅ Done. Total predictions:", len(predictions))
pd.DataFrame(predictions).to_csv("data/predictions.csv", index=False)
