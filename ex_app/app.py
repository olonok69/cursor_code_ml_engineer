import warnings
warnings.filterwarnings("ignore")

import io
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import streamlit as st
import os
import sys

# Ensure local imports work both with `python -m` and `streamlit run`
_THIS_DIR = os.path.dirname(__file__)
if _THIS_DIR not in sys.path:
    sys.path.append(_THIS_DIR)

from models import (
    available_models,
    forecast_with_model,
    MODEL_EXPLANATIONS,
)
from metrics_utils import (
    evaluate_forecast,
    METRIC_EXPLANATIONS,
)
from typing import Dict

try:
    # For diagnostics
    import importlib
    smtsa_stattools = importlib.import_module("statsmodels.tsa.stattools")
    smtsa_graphics = importlib.import_module("statsmodels.graphics.tsaplots")
    HAS_SM_DIAG = True
except Exception:
    HAS_SM_DIAG = False


@dataclass
class AppConfig:
    title: str = "Time Series Forecasting — Traditional Models"
    default_test_size: int = 24
    default_season_length: int = 12


CFG = AppConfig()


def _load_csv(upload: Optional[io.BytesIO]) -> Optional[pd.DataFrame]:
    if upload is None:
        return None
    try:
        df = pd.read_csv(upload)
        return df
    except Exception as e:
        st.error(f"Failed to read CSV: {e}")
        return None


def _make_sample_series(n: int = 200, freq: str = "D", seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2020-01-01", periods=n, freq=freq)
    trend = np.linspace(0, 10, n)
    seasonal = 10 * np.sin(2 * np.pi * np.arange(n) / 7)
    noise = rng.normal(0, 2, n)
    y = 50 + trend + seasonal + noise
    return pd.DataFrame({"ds": idx, "y": y})


def sidebar_data_ingest() -> Tuple[pd.Series, int, str]:
    st.sidebar.header("1) Data")
    mode = st.sidebar.radio("Choose data source", ["Upload CSV", "Use sample data"], index=1)

    df: Optional[pd.DataFrame] = None
    if mode == "Upload CSV":
        upload = st.sidebar.file_uploader("Upload CSV file", type=["csv"])
        df = _load_csv(upload)
        if df is not None and len(df) == 0:
            df = None
    else:
        df = _make_sample_series()

    if df is None:
        st.info("Awaiting data... Upload a CSV or use the sample to continue.")
        st.stop()

    # Column selection
    st.sidebar.markdown("— Columns —")
    date_col = st.sidebar.selectbox("Date/time column", options=df.columns.tolist(), index=0)
    value_col = st.sidebar.selectbox("Target value column", options=[c for c in df.columns if c != date_col], index=0)

    # Parse datetime and set index
    try:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=[date_col])
        df = df.sort_values(date_col)
        df = df.set_index(date_col)
    except Exception as e:
        st.error(f"Failed parsing datetime column: {e}")
        st.stop()

    # Frequency
    inferred = pd.infer_freq(df.index)
    freq = st.sidebar.selectbox(
        "Frequency (inferred if None)",
        options=["auto", "D", "W", "M", "Q", "H"],
        index=0,
        help="If 'auto', we will not resample; your index must already be regular.",
    )
    if freq != "auto":
        df = df.asfreq(freq)
        before = len(df)
        df = df.dropna(subset=[value_col])
        removed = before - len(df)
        if removed > 0:
            st.sidebar.warning(f"Removed {removed} rows with missing values after resampling.")

    # Show head
    with st.expander("Preview data", expanded=False):
        st.write(df[[value_col]].head())
        st.caption(f"Inferred frequency: {inferred}")

    series = df[value_col].astype(float)

    # Season length selection
    st.sidebar.markdown("— Seasonality —")
    season_length = st.sidebar.number_input(
        "Season length (m)", min_value=1, max_value=10_000, value=CFG.default_season_length,
        help="Examples: 7 for daily-with-weekly seasonality, 12 for monthly-with-yearly seasonality, 24 for hourly-with-daily"
    )

    return series, int(season_length), freq


def sidebar_experiment_setup(series: pd.Series) -> Tuple[int, List[str]]:
    st.sidebar.header("2) Experiment setup")
    test_size = st.sidebar.number_input(
        "Forecast horizon (test size)", min_value=1, max_value=max(2, len(series)//2), value=min(CFG.default_test_size, max(2, len(series)//2)),
        help="Number of last points held out for evaluation and forecasting",
    )

    model_options = list(available_models().keys())
    preferred_defaults = [
        "Naive",
        "Seasonal Naive",
        "Moving Average",
        "Simple Exponential Smoothing",
        "Holt",
        "Holt-Winters (ETS)",
        "SARIMA (statsmodels)",
        "Auto-ARIMA (pmdarima)",
    ]
    default_models = [m for m in preferred_defaults if m in model_options]
    model_names = st.sidebar.multiselect(
        "Select models",
        options=model_options,
        default=default_models,
    )
    return int(test_size), model_names


def _walk_forward_backtest(
    model_name: str,
    series: pd.Series,
    season_length: int,
    start_ratio: float = 0.6,
    step: int = 1,
    horizon: int = 1,
    params: Optional[Dict] = None,
):
    params = params or {}
    n = len(series)
    start = max(int(n * start_ratio), season_length + 2)
    preds = []
    actuals = []
    for t in range(start, n - horizon + 1, step):
        y_tr = series.iloc[:t]
        y_te = series.iloc[t:t + horizon]
        fc, _ = forecast_with_model(model_name, y_tr, horizon=horizon, season_length=season_length, params=params)
        preds.append(fc.values)
        actuals.append(y_te.values)
    if len(preds) == 0:
        return None, None
    return np.array(actuals), np.array(preds)


def main():
    st.set_page_config(page_title=CFG.title, layout="wide")
    st.title(CFG.title)
    st.caption("Interactive demo of classical time series forecasting models with clear metric explanations.")

    # Data ingest and setup
    y, season_length, _ = sidebar_data_ingest()
    test_size, model_names = sidebar_experiment_setup(y)

    if len(y) < test_size + max(3, season_length):
        st.warning("Not enough data for the chosen settings. Reduce the forecast horizon or season length.")
        st.stop()

    # Train/test split
    y_train = y.iloc[:-test_size]
    y_test = y.iloc[-test_size:]

    st.subheader("Data summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Train length", len(y_train))
    c2.metric("Test length (horizon)", len(y_test))
    c3.metric("Season length m", season_length)
    c4.metric("Start → End", f"{y.index.min().date()} → {y.index.max().date()}")

    # Run selected models
    st.subheader("Model forecasts and metrics")
    all_forecasts: Dict[str, pd.Series] = {}
    rows = []

    for name in model_names:
        with st.expander(f"Configure {name}", expanded=False):
            params: Dict = {}
            if name == "Moving Average":
                params["window"] = st.number_input(f"{name} window k", min_value=2, max_value=max(2, len(y_train)), value=max(2, min(12, season_length)), key=f"{name}_k")
            if name == "Simple Exponential Smoothing":
                use_opt = st.checkbox(f"{name}: optimized", value=True, key=f"{name}_opt")
                alpha = None
                if not use_opt:
                    alpha = st.slider(f"{name}: alpha", 0.01, 0.99, 0.3, 0.01, key=f"{name}_alpha")
                params.update({"optimized": use_opt})
                if alpha is not None:
                    params["alpha"] = alpha
            if name == "Holt":
                use_opt = st.checkbox(f"{name}: optimized", value=True, key=f"{name}_opt")
                damped = st.checkbox(f"{name}: damped trend", value=False, key=f"{name}_damped")
                alpha = beta = None
                if not use_opt:
                    alpha = st.slider(f"{name}: alpha", 0.01, 0.99, 0.3, 0.01, key=f"{name}_alpha")
                    beta = st.slider(f"{name}: beta", 0.01, 0.99, 0.1, 0.01, key=f"{name}_beta")
                params.update({"optimized": use_opt, "damped_trend": damped})
                if alpha is not None:
                    params["alpha"] = alpha
                if beta is not None:
                    params["beta"] = beta
            if name == "Holt-Winters (ETS)":
                trend = st.selectbox(f"{name}: trend", options=["add", "mul", None], index=0, key=f"{name}_trend")
                seasonal = st.selectbox(f"{name}: seasonal", options=["add", "mul", None], index=(0 if season_length > 1 else 2), key=f"{name}_seasonal")
                damped = st.checkbox(f"{name}: damped trend", value=False, key=f"{name}_damped")
                use_boxcox = st.checkbox(f"{name}: Box-Cox", value=False, key=f"{name}_boxcox")
                params.update({"trend": trend, "seasonal": seasonal, "damped_trend": damped, "use_boxcox": use_boxcox})
            if name in ("SARIMA (statsmodels)", "STL + ARIMA"):
                p = st.number_input(f"{name}: p", 0, 5, 1, key=f"{name}_p")
                d = st.number_input(f"{name}: d", 0, 2, 1, key=f"{name}_d")
                q = st.number_input(f"{name}: q", 0, 5, 1, key=f"{name}_q")
                P = st.number_input(f"{name}: P", 0, 2, (1 if season_length > 1 else 0), key=f"{name}_P")
                D = st.number_input(f"{name}: D", 0, 2, (1 if season_length > 1 else 0), key=f"{name}_D")
                Q = st.number_input(f"{name}: Q", 0, 2, (1 if season_length > 1 else 0), key=f"{name}_Q")
                m = st.number_input(f"{name}: m (season length)", 1, 10000, season_length, key=f"{name}_m")
                params.update({"p": p, "d": d, "q": q, "P": P, "D": D, "Q": Q, "m": m})
                if name == "STL + ARIMA":
                    period = st.number_input(f"{name}: STL period", 2, 10000, season_length, key=f"{name}_period")
                    params["period"] = period
            if name == "Auto-ARIMA (pmdarima)":
                seasonal = st.checkbox(f"{name}: seasonal", value=(season_length > 1), key=f"{name}_seasonal")
                m = st.number_input(f"{name}: m", 1, 10000, season_length, key=f"{name}_m")
                ic = st.selectbox(f"{name}: information criterion", options=["aic", "bic", "aicc"], index=0, key=f"{name}_ic")
                params.update({"seasonal": seasonal, "m": m, "ic": ic})

        with st.spinner(f"Fitting {name}..."):
            fc_series, extras = forecast_with_model(name, y_train, horizon=len(y_test), season_length=season_length, params=params)

        all_forecasts[name] = fc_series
        metrics = evaluate_forecast(
            y_test.values,
            fc_series.values,
            seasonal_period=season_length,
            mase_insample=y_train.values,
        )
        rows.append({"Model": name, **metrics})

    if rows:
        results_df = pd.DataFrame(rows).set_index("Model")
        st.dataframe(results_df.style.format({col: "{:.3f}" for col in results_df.columns if results_df[col].dtype != object}), use_container_width=True)

    # Export forecasts
    if all_forecasts:
        export_df = pd.concat(all_forecasts, axis=1)
        export_df.insert(0, "Actual", y.reindex(export_df.index))
        st.download_button(
            label="Download forecasts CSV",
            data=export_df.to_csv(index=True).encode("utf-8"),
            file_name="forecasts.csv",
            mime="text/csv",
        )

    # Metric explanations
    with st.expander("Metric definitions (from metrics.md)"):
        for m_name, m_text in METRIC_EXPLANATIONS.items():
            st.markdown(f"**{m_name}** — {m_text}")

    # Plot
    st.subheader("Actual vs forecast")
    plot_df = pd.DataFrame({"Actual": y})
    for name, fc in all_forecasts.items():
        plot_df[name] = fc
    st.line_chart(plot_df, use_container_width=True)

    # Per-model info and residuals
    st.subheader("Model details")
    for name in model_names:
        with st.expander(name):
            st.markdown(MODEL_EXPLANATIONS.get(name, ""))
            if name in all_forecasts:
                fc = all_forecasts[name]
                residuals = y_test.values - fc.values
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("Residual summary")
                    st.write(pd.Series(residuals).describe())
                with c2:
                    try:
                        import importlib
                        plt = importlib.import_module("matplotlib.pyplot")
                        mdates = importlib.import_module("matplotlib.dates")
                        fig, ax = plt.subplots(figsize=(6, 3))
                        ax.plot(y_test.index, residuals, label="Residuals")
                        ax.axhline(0, color="gray", ls=":")
                        ax.legend(loc="best")
                        # Improve date tick readability
                        locator = mdates.AutoDateLocator(minticks=3, maxticks=7)
                        formatter = mdates.AutoDateFormatter(locator)
                        ax.xaxis.set_major_locator(locator)
                        ax.xaxis.set_major_formatter(formatter)
                        fig.autofmt_xdate(rotation=30)
                        plt.tight_layout()
                        st.pyplot(fig, use_container_width=True)
                    except Exception:
                        st.info("Install matplotlib for residual plots.")

                # Diagnostics: ACF/PACF and Ljung-Box
                if HAS_SM_DIAG:
                    with st.expander(f"Diagnostics — {name}: ACF/PACF and Ljung–Box"):
                        try:
                            import importlib
                            plt = importlib.import_module("matplotlib.pyplot")
                            fig1 = smtsa_graphics.plot_acf(residuals, lags=min(40, len(residuals) - 1))
                            st.pyplot(fig1, use_container_width=True)
                            fig2 = smtsa_graphics.plot_pacf(residuals, lags=min(40, len(residuals) - 1), method="ywm")
                            st.pyplot(fig2, use_container_width=True)
                            lb = smtsa_stattools.acorr_ljungbox(residuals, lags=[min(10, len(residuals) - 1)], return_df=True)
                            st.write(lb)
                        except Exception as e:
                            st.info(f"Diagnostics unavailable: {e}")

    # Walk-forward backtesting
    st.subheader("Walk-forward backtesting and horizon evaluation")
    with st.expander("Configure backtest", expanded=False):
        bt_model = st.selectbox("Model for backtest", options=model_names or list(available_models().keys()))
        start_ratio = st.slider("Start ratio of history", 0.2, 0.9, 0.6, 0.05)
        step = st.number_input("Step (stride)", 1, max(1, len(y)//10), 1)
        horizon_bt = st.number_input("Prediction horizon", 1, min(60, len(y)//3 if len(y) > 3 else 1), min(12, len(y)//3 if len(y) > 3 else 1))
        run_bt = st.button("Run backtest")

    if 'run_bt' in locals() and run_bt:
        with st.spinner("Running backtest..."):
            actual_arr, pred_arr = _walk_forward_backtest(
                bt_model, y, season_length=season_length, start_ratio=start_ratio, step=step, horizon=horizon_bt
            )
        if actual_arr is None:
            st.warning("Backtest could not run with current settings. Adjust start ratio or horizon.")
        else:
            # Overall metrics (flatten)
            overall = evaluate_forecast(actual_arr.flatten(), pred_arr.flatten(), seasonal_period=season_length, mase_insample=y.values)
            st.write("Overall backtest metrics:")
            st.write(pd.Series(overall))

            # Horizon-specific
            results = {}
            for h in range(1, horizon_bt + 1):
                ah = actual_arr[:, h-1]
                ph = pred_arr[:, h-1]
                results[f"h={h}"] = evaluate_forecast(ah, ph, seasonal_period=season_length, mase_insample=y.values)
            st.write("Horizon-specific metrics:")
            st.dataframe(pd.DataFrame(results).T)


if __name__ == "__main__":
    main()
