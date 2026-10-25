
import pandas as pd

from services.forecast_analysis import (
    create_decision_cutoffs,
    select_forecasts,
    calculate_accuracy,
    aggregate_actuals_hourly
)


def test_forecast_selection_and_accuracy():
    forecasts = pd.DataFrame({
        "startTime": [
            "2026-01-02T10:00:00Z",
            "2026-01-02T10:00:00Z",
            "2026-01-02T10:00:00Z",
        ],
        "publishTime": [
            "2026-01-01T08:00:00Z",
            "2026-01-01T09:00:00Z",
            "2026-01-01T11:00:00Z",
        ],
        "generation": [5000, 5200, 6000],
    })

    actuals = pd.DataFrame({
        "startTime": ["2026-01-02T10:00:00Z"],
        "generation": [5500],
    })

    delivery_times = pd.Series([
        "2026-01-02T10:00:00Z"
    ])

    cutoffs = create_decision_cutoffs(delivery_times)
    selected = select_forecasts(forecasts, cutoffs)

    assert len(selected) == 1
    assert selected.iloc[0]["generation"] == 5200

    comparison, metrics = calculate_accuracy(selected, actuals)

    assert len(comparison) == 1
    assert comparison.iloc[0]["error"] == -300
    assert metrics["sampleCount"] == 1
    assert metrics["mae"] == 300
    assert metrics["rmse"] == 300
    assert metrics["bias"] == -300
    

def test_aggregate_actuals_hourly():
    actuals = pd.DataFrame({
        "startTime": [
            "2026-01-01T10:00:00Z",
            "2026-01-01T10:30:00Z",
            "2026-01-01T11:00:00Z",
        ],
        "generation": [10000, 12000, 14000],
    })

    hourly = aggregate_actuals_hourly(actuals)

    # The 10:00 hour has two readings: (10000 + 12000) / 2.
    assert len(hourly) == 1
    assert hourly.iloc[0]["startTime"] == pd.Timestamp(
        "2026-01-01T10:00:00Z"
    )
    assert hourly.iloc[0]["generation"] == 11000
