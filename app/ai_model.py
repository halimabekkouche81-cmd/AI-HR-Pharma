# -*- coding: utf-8 -*-
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np

def train_model(data):
    if not data or len(data) < 2:
        return None, None

    df = pd.DataFrame(data, columns=["date", "quantity"])
    df["date"] = pd.to_datetime(df["date"])
    df["days"] = (df["date"] - df["date"].min()).dt.days
    df["quantity"] = df["quantity"].abs()

    X = df[["days"]]
    y = df["quantity"]

    model = LinearRegression()
    model.fit(X, y)

    return model, df

def predict_future(model, df, days_ahead=7):
    if model is None or df is None:
        return []

    last_day = df["days"].max()
    future_days = np.array([[last_day + i] for i in range(1, days_ahead + 1)])
    predictions = model.predict(future_days)

    return [max(0, round(p, 2)) for p in predictions.tolist()]

def get_trend(model):
    if model is None:
        return "unknown"

    slope = model.coef_[0]

    if slope > 0.1:
        return "📈 increasing"
    elif slope < -0.1:
        return "📉 decreasing"
    else:
        return "➡️ stable"