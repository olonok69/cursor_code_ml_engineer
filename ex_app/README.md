# Streamlit App — Traditional Time Series Forecasting

This Streamlit application showcases classical time series forecasting models and evaluation metrics, grounded in the explanations from `research.md` and `metrics.md`.

## Features

- Upload a CSV or use a synthetic sample series
- Select date and target columns; optional resampling by frequency
- Choose forecast horizon and season length (m)
- Run multiple classical models:
  - Naive, Seasonal Naive, Moving Average
  - Simple Exponential Smoothing (SES)
  - Holt (level + trend)
  - Holt–Winters (ETS)
  - SARIMA (statsmodels)
  - Auto-ARIMA (pmdarima) if available
- Compare metrics: MAE, RMSE, MSE, MAPE, sMAPE, MASE, MDA, RMSE/MAE ratio
- Actual vs forecast chart and residual summaries per model

## Install

Create/activate a Python environment (3.9+ recommended), then install dependencies:

```powershell
pip install -r streamlit_app/requirements.txt
```

If `pmdarima` fails to build on Windows, you can skip it; the app handles its absence gracefully.

## Run

From the repository root:

```powershell
streamlit run streamlit_app/app.py
```

## CSV format

The app expects at least two columns:

- A datetime-like column (select in the sidebar)
- A numeric target column (select in the sidebar)

The index is set to the datetime column. If frequency is set to `auto`, your timestamps should already be regular; otherwise choose a frequency (D/W/M/H) to asfreq-resample.

## Notes

- Metric definitions and caveats are summarized from `metrics.md`.
- Model descriptions (SES/Holt/ETS/ARIMA) align with the discussion in `research.md`.
- For seasonal naive and MASE, ensure `season_length (m)` reflects your data (e.g., 7 for daily with weekly seasonality, 12 for monthly with yearly seasonality).
