# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split

def prepare_data(raw_data):
    """
    تحويل بيانات StockMovement إلى Time Series يومية
    raw_data: list of (created_at, quantity)
    """
    df = pd.DataFrame(raw_data, columns=["date", "quantity"])
    df["date"] = pd.to_datetime(df["date"])
    df["quantity"] = df["quantity"].abs()

    # Daily Aggregation
    df = df.groupby(df["date"].dt.date)["quantity"].sum().reset_index()
    df.columns = ["date", "sales"]
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    return df

def evaluate_linear_regression(df):
    """
    تقييم Linear Regression مع Train/Test Split
    """
    df["days"] = (df["date"] - df["date"].min()).dt.days

    X = df[["days"]].values
    y = df["sales"].values

    # Train/Test Split (80/20)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False
    )

    model = LinearRegression()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    mae = round(mean_absolute_error(y_test, y_pred), 4)
    rmse = round(np.sqrt(mean_squared_error(y_test, y_pred)), 4)

    # Forecast next 7 days
    last_day = df["days"].max()
    future_days = np.array([[last_day + i] for i in range(1, 8)])
    forecast = model.predict(future_days).tolist()
    forecast = [max(0, round(f, 2)) for f in forecast]

    return {
        "model": "Linear Regression",
        "mae": mae,
        "rmse": rmse,
        "train_size": len(X_train),
        "test_size": len(X_test),
        "forecast_7_days": forecast,
        "y_test": y_test.tolist(),
        "y_pred": y_pred.tolist()
    }

def evaluate_prophet(df):
    """
    تقييم Prophet مع Train/Test Split
    """
    try:
        from prophet import Prophet

        prophet_df = df[["date", "sales"]].copy()
        prophet_df.columns = ["ds", "y"]

        # Train/Test Split (80/20)
        split_idx = int(len(prophet_df) * 0.8)
        train = prophet_df.iloc[:split_idx]
        test = prophet_df.iloc[split_idx:]

        model = Prophet(
            daily_seasonality=False,
            weekly_seasonality=True,
            yearly_seasonality=False
        )
        model.fit(train)

        # Predict on test
        forecast = model.predict(test[["ds"]])
        y_pred = forecast["yhat"].values
        y_test = test["y"].values

        mae = round(mean_absolute_error(y_test, y_pred), 4)
        rmse = round(np.sqrt(mean_squared_error(y_test, y_pred)), 4)

        # Forecast next 7 days
        future = model.make_future_dataframe(periods=7)
        future_forecast = model.predict(future)
        next_7 = future_forecast.tail(7)["yhat"].tolist()
        next_7 = [max(0, round(f, 2)) for f in next_7]

        return {
            "model": "Prophet",
            "mae": mae,
            "rmse": rmse,
            "train_size": len(train),
            "test_size": len(test),
            "forecast_7_days": next_7,
            "y_test": y_test.tolist(),
            "y_pred": y_pred.tolist()
        }

    except Exception as e:
        return {
            "model": "Prophet",
            "error": str(e),
            "mae": None,
            "rmse": None
        }

def compare_models(df):
    """
    مقارنة النموذجين مع جميع المعطيات
    """
    lr_results = evaluate_linear_regression(df)
    prophet_results = evaluate_prophet(df)

    comparison = {
        "data_points": len(df),
        "date_range": {
            "start": str(df["date"].min().date()),
            "end": str(df["date"].max().date())
        },
        "models": [
            {
                "model": "Linear Regression",
                "mae": lr_results["mae"],
                "rmse": lr_results["rmse"],
                "train_size": lr_results["train_size"],
                "test_size": lr_results["test_size"],
                "forecast_7_days": lr_results["forecast_7_days"],
                "interpretation": "Simple trend detection"
            },
            {
                "model": "Prophet",
                "mae": prophet_results.get("mae"),
                "rmse": prophet_results.get("rmse"),
                "train_size": prophet_results.get("train_size"),
                "test_size": prophet_results.get("test_size"),
                "forecast_7_days": prophet_results.get("forecast_7_days"),
                "interpretation": "Handles seasonality and trends"
            }
        ],
        "winner": "Prophet" if (
            prophet_results.get("mae") and
            lr_results["mae"] and
            prophet_results["mae"] < lr_results["mae"]
        ) else "Linear Regression",
        "lr_details": lr_results,
        "prophet_details": prophet_results
    }

    return comparison