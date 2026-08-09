from __future__ import annotations

from typing import Dict

import numpy as np
try:
    from sklearn.metrics import mean_absolute_error, mean_squared_error  # type: ignore
    HAS_SKLEARN = True
except Exception:
    HAS_SKLEARN = False

    def mean_absolute_error(y_true, y_pred):  # type: ignore
        y_true = np.asarray(y_true)
        y_pred = np.asarray(y_pred)
        return float(np.mean(np.abs(y_true - y_pred)))

    def mean_squared_error(y_true, y_pred):  # type: ignore
        y_true = np.asarray(y_true)
        y_pred = np.asarray(y_pred)
        return float(np.mean((y_true - y_pred) ** 2))


def _safe_mape(actual: np.ndarray, predicted: np.ndarray) -> float:
    actual = np.asarray(actual)
    predicted = np.asarray(predicted)
    mask = actual != 0
    if not np.any(mask):
        return np.nan
    return float(np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100.0)


def _smape(actual: np.ndarray, predicted: np.ndarray) -> float:
    actual = np.asarray(actual)
    predicted = np.asarray(predicted)
    denom = (np.abs(actual) + np.abs(predicted))
    mask = denom != 0
    if not np.any(mask):
        return np.nan
    return float(np.mean(2.0 * np.abs(predicted[mask] - actual[mask]) / denom[mask]) * 100.0)


def _mase(actual: np.ndarray, predicted: np.ndarray, seasonal_period: int = 1, insample: np.ndarray | None = None) -> float:
    actual = np.asarray(actual)
    predicted = np.asarray(predicted)
    mae = mean_absolute_error(actual, predicted)
    baseline_series = np.asarray(insample) if insample is not None else actual
    if len(baseline_series) <= seasonal_period:
        return np.nan
    naive_errors = np.abs(baseline_series[seasonal_period:] - baseline_series[:-seasonal_period])
    denom = np.mean(naive_errors) if len(naive_errors) > 0 else np.nan
    if denom == 0 or np.isnan(denom):
        return np.nan
    return float(mae / denom)


def _mda(actual: np.ndarray, predicted: np.ndarray) -> float:
    actual = np.asarray(actual)
    predicted = np.asarray(predicted)
    if len(actual) < 2:
        return np.nan
    actual_direction = np.sign(actual[1:] - actual[:-1])
    pred_direction = np.sign(predicted[1:] - actual[:-1])
    return float(np.mean(actual_direction == pred_direction))


def evaluate_forecast(actual: np.ndarray, predicted: np.ndarray, seasonal_period: int = 1, mase_insample: np.ndarray | None = None) -> Dict[str, float]:
    mae = mean_absolute_error(actual, predicted)
    mse = mean_squared_error(actual, predicted)
    rmse = np.sqrt(mse)

    return {
        "MAE": float(mae),
        "RMSE": float(rmse),
        "MSE": float(mse),
        "MAPE": _safe_mape(actual, predicted),
        "sMAPE": _smape(actual, predicted),
        "MASE": _mase(actual, predicted, seasonal_period=seasonal_period, insample=mase_insample),
        "MDA": _mda(actual, predicted),
        "RMSE/MAE_ratio": float(rmse / mae) if mae > 0 else np.nan,
    }


METRIC_EXPLANATIONS: Dict[str, str] = {
    "MAE": "Mean Absolute Error — average absolute deviation; linear penalty and interpretable in original units.",
    "RMSE": "Root Mean Square Error — penalizes large errors more; same units as data.",
    "MSE": "Mean Square Error — squared units; useful during optimization.",
    "MAPE": "Mean Absolute Percentage Error — scale independent but undefined for zeros; use sMAPE if zeros present.",
    "sMAPE": "Symmetric MAPE — bounded and handles zeros better; commonly used in forecasting competitions.",
    "MASE": "Mean Absolute Scaled Error — compares against seasonal naive baseline; <1 means better than naive.",
    "MDA": "Mean Directional Accuracy — proportion of correctly predicted directions (up/down).",
    "RMSE/MAE_ratio": "Diagnostic: ratio > 1.5 often indicates presence of large errors/outliers.",
}
