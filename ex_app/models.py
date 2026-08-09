from __future__ import annotations

import warnings
warnings.filterwarnings("ignore")

from typing import Dict, Tuple, Optional

import numpy as np
import pandas as pd

# Statsmodels classical models
try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing  
    from statsmodels.tsa.api import SimpleExpSmoothing, Holt 
    from statsmodels.tsa.statespace.sarimax import SARIMAX 
    from statsmodels.tsa.forecasting.stl import STLForecast  
except Exception:
    HAS_STATSMODELS = False

try:
    import pmdarima as pm  # type: ignore
    HAS_PM = True
except Exception:
    HAS_PM = False


def available_models() -> Dict[str, str]:
    models = {
        "Naive": "Forecast equals last observed value",
        "Seasonal Naive": "Forecast repeats value from last season",
        "Moving Average": "Forecast is mean of last k values",
    }
    if HAS_STATSMODELS:
        models.update({
            "Simple Exponential Smoothing": "Level-only exponential smoothing (SES)",
            "Holt": "Level + trend exponential smoothing",
            "Holt-Winters (ETS)": "Exponential smoothing with trend and seasonality",
            "SARIMA (statsmodels)": "Seasonal ARIMA via statsmodels",
            "STL + ARIMA": "STL decomposition with ARIMA on seasonally adjusted series",
        })
    if HAS_PM:
        models["Auto-ARIMA (pmdarima)"] = "Automatic ARIMA order selection"
    return models


def _to_forecast_index(train: pd.Series, horizon: int) -> pd.DatetimeIndex:
    last = train.index[-1]
    try:
        freq = train.index.freq or train.index.inferred_freq
        return pd.date_range(start=last, periods=horizon + 1, freq=freq)[1:]
    except Exception:
        # fallback: keep same index type by stepping one unit (not perfect)
        return pd.date_range(start=last, periods=horizon + 1, freq="D")[1:]


def forecast_with_model(
    name: str,
    y_train: pd.Series,
    horizon: int,
    season_length: int = 1,
    params: Optional[Dict] = None,
) -> Tuple[pd.Series, Dict]:
    name = name.strip()
    idx = _to_forecast_index(y_train, horizon)
    params = params or {}

    if name == "Naive":
        last = y_train.iloc[-1]
        fc = pd.Series(np.repeat(last, horizon), index=idx, name="forecast")
        return fc, {"model": "naive"}

    if name == "Seasonal Naive":
        if len(y_train) < season_length:
            raise ValueError("Not enough data for seasonal naive.")
        hist = y_train.iloc[-season_length:]
        reps = int(np.ceil(horizon / season_length))
        pattern = np.tile(hist.values, reps)[:horizon]
        fc = pd.Series(pattern, index=idx, name="forecast")
        return fc, {"model": "snaive"}

    if name == "Moving Average":
        k = int(params.get("window", max(2, min(12, season_length))))
        if len(y_train) < k:
            k = max(2, len(y_train))
        mean_val = y_train.iloc[-k:].mean()
        fc = pd.Series(np.repeat(mean_val, horizon), index=idx, name="forecast")
        return fc, {"model": "moving_average", "window": k}

    if name == "Simple Exponential Smoothing":
        if not HAS_STATSMODELS:
            raise ImportError("statsmodels is required for SES. Install from requirements.txt")
        alpha = params.get("alpha", None)
        optimized = params.get("optimized", True)
        model = SimpleExpSmoothing(y_train, initialization_method="estimated").fit(
            smoothing_level=alpha, optimized=optimized
        )
        pred = model.forecast(horizon)
        pred.index = idx
        return pred.rename("forecast"), {"alpha": getattr(model.model, "smoothing_level", None), "optimized": optimized}

    if name == "Holt":
        if not HAS_STATSMODELS:
            raise ImportError("statsmodels is required for Holt. Install from requirements.txt")
        alpha = params.get("alpha", None)
        beta = params.get("beta", None)
        damped = params.get("damped_trend", False)
        optimized = params.get("optimized", True)
        model = Holt(y_train, initialization_method="estimated", damped_trend=damped).fit(
            smoothing_level=alpha, smoothing_slope=beta, optimized=optimized
        )
        pred = model.forecast(horizon)
        pred.index = idx
        return pred.rename("forecast"), {
            "alpha": getattr(model.model, "smoothing_level", None),
            "beta": getattr(model.model, "smoothing_slope", None),
            "damped_trend": damped,
            "optimized": optimized,
        }

    if name == "Holt-Winters (ETS)":
        if not HAS_STATSMODELS:
            raise ImportError("statsmodels is required for ETS. Install from requirements.txt")
        trend = params.get("trend", "add")
        seasonal = params.get("seasonal", ("add" if season_length > 1 else None))
        damped = params.get("damped_trend", False)
        use_boxcox = params.get("use_boxcox", False)
        model = ExponentialSmoothing(
            y_train,
            seasonal_periods=season_length if seasonal else None,
            trend=trend,
            seasonal=seasonal,
            initialization_method="estimated",
            damped_trend=damped,
            use_boxcox=use_boxcox,
        ).fit()
        pred = model.forecast(horizon)
        pred.index = idx
        return pred.rename("forecast"), {"trend": trend, "seasonal": seasonal, "damped_trend": damped}

    if name == "SARIMA (statsmodels)":
        if not HAS_STATSMODELS:
            raise ImportError("statsmodels is required for SARIMA. Install from requirements.txt")
        p = int(params.get("p", 1))
        d = int(params.get("d", 1))
        q = int(params.get("q", 1))
        P = int(params.get("P", 1 if season_length > 1 else 0))
        D = int(params.get("D", 1 if season_length > 1 else 0))
        Q = int(params.get("Q", 1 if season_length > 1 else 0))
        m = int(params.get("m", max(1, season_length)))
        order = (p, d, q)
        sorder = (P, D, Q, m) if m > 1 else (0, 0, 0, 0)
        model = SARIMAX(y_train, order=order, seasonal_order=sorder, enforce_stationarity=False, enforce_invertibility=False)
        fit = model.fit(disp=False)
        pred = fit.forecast(steps=horizon)
        pred.index = idx
        return pred.rename("forecast"), {"order": order, "seasonal_order": sorder}

    if name == "Auto-ARIMA (pmdarima)" and HAS_PM:
        autom = pm.auto_arima(
            y_train,
            seasonal=bool(params.get("seasonal", season_length > 1)),
            m=int(params.get("m", max(1, season_length))),
            start_p=int(params.get("start_p", 0)),
            start_q=int(params.get("start_q", 0)),
            max_p=int(params.get("max_p", 5)),
            max_q=int(params.get("max_q", 5)),
            start_P=int(params.get("start_P", 0)),
            start_Q=int(params.get("start_Q", 0)),
            max_P=int(params.get("max_P", 2)),
            max_Q=int(params.get("max_Q", 2)),
            d=None, D=None,
            stepwise=True,
            suppress_warnings=True,
            information_criterion=str(params.get("ic", "aic")),
        )
        pred = autom.predict(n_periods=horizon)
        fc = pd.Series(pred, index=idx, name="forecast")
        return fc, {"order_": getattr(autom, "order", None), "seasonal_order_": getattr(autom, "seasonal_order", None)}

    if name == "STL + ARIMA" and HAS_STATSMODELS:
        # Basic wrapper: STL for decomposition, ARIMA as the forecasting model on remainder
        p = int(params.get("p", 1))
        d = int(params.get("d", 1))
        q = int(params.get("q", 1))
        P = int(params.get("P", 1 if season_length > 1 else 0))
        D = int(params.get("D", 1 if season_length > 1 else 0))
        Q = int(params.get("Q", 1 if season_length > 1 else 0))
        m = int(params.get("m", max(1, season_length)))
        period = int(params.get("period", max(2, season_length)))
        model = STLForecast(y_train, SARIMAX, period=period, model_kwargs={
            "order": (p, d, q),
            "seasonal_order": (P, D, Q, m) if m > 1 else (0, 0, 0, 0),
            "enforce_stationarity": False,
            "enforce_invertibility": False,
        })
        res = model.fit()
        pred = res.forecast(horizon)
        pred.index = idx
        return pred.rename("forecast"), {"period": period}

    raise ValueError(f"Unknown or unsupported model: {name}")


MODEL_EXPLANATIONS: Dict[str, str] = {
    "Naive": "Naive forecast uses the last observed value for all future periods. It is a strong baseline and forms the denominator for MASE.",
    "Seasonal Naive": "Seasonal naive repeats the last observed seasonal pattern m steps ago. Useful when strong, stable seasonality exists.",
    "Moving Average": "Moving Average averages the last k observations and projects that average forward. Smooths noise but cannot extrapolate trends.",
    "Simple Exponential Smoothing": "SES models a level-only process with exponentially decaying weights for older observations.",
    "Holt": "Holt's method extends SES by adding a trend component (level + trend).",
    "Holt-Winters (ETS)": "Holt-Winters (ETS) includes level, trend, and seasonality components; we fit an additive-additive variant here.",
    "SARIMA (statsmodels)": "Seasonal ARIMA captures autoregression, differencing, and moving average terms with seasonal counterparts.",
    "Auto-ARIMA (pmdarima)": "Auto-ARIMA automatically selects ARIMA orders via information criteria (Hyndman–Khandakar approach).",
    "STL + ARIMA": "STL decomposition separates trend/seasonality; ARIMA models the remainder for robust forecasts.",
}
