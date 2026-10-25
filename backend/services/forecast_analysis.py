import pandas as pd


def create_decision_cutoffs(
    delivery_times: pd.Series,
) -> pd.DataFrame:
    """
    Set the decision cutoff to 24 hours before delivery.
    """

    start_times = pd.to_datetime(
        delivery_times, utc=True, errors="raise"
    )

    return pd.DataFrame({
        "startTime": start_times,
        "decisionCutoff": start_times - pd.Timedelta(hours=24),
    })


def select_forecasts(
    forecasts: pd.DataFrame,
    decision_cutoffs: pd.DataFrame,
) -> pd.DataFrame:
    """
    Select the latest forecast published by each interval's
    purchase decision cutoff.

    forecasts columns:
        startTime, publishTime, generation

    decision_cutoffs columns:
        startTime, decisionCutoff
    """

    required_forecast = {
        "startTime",
        "publishTime",
        "generation",
    }
    required_cutoff = {"startTime", "decisionCutoff"}

    if not required_forecast.issubset(forecasts.columns):
        raise ValueError("Forecast data is missing required columns")

    if not required_cutoff.issubset(decision_cutoffs.columns):
        raise ValueError("Decision cutoffs are missing required columns")

    forecast_data = forecasts.copy()
    cutoffs = decision_cutoffs.copy()

    for column in ("startTime", "publishTime"):
        forecast_data[column] = pd.to_datetime(
            forecast_data[column], utc=True, errors="raise"
        )

    for column in ("startTime", "decisionCutoff"):
        cutoffs[column] = pd.to_datetime(
            cutoffs[column], utc=True, errors="raise"
        )

    if cutoffs["startTime"].duplicated().any():
        raise ValueError("Each delivery interval must have one cutoff")

    forecast_data["generation"] = pd.to_numeric(
        forecast_data["generation"], errors="raise"
    )

    candidates = forecast_data.merge(
        cutoffs,
        on="startTime",
        how="inner",
        validate="many_to_one",
    )

    candidates = candidates.loc[
        candidates["publishTime"] <= candidates["decisionCutoff"]
    ]

    selected = (
        candidates.sort_values("publishTime")
        .drop_duplicates(subset=["startTime"], keep="last")
    )

    return selected[
        ["startTime", "publishTime", "generation"]
    ].reset_index(drop=True)



def calculate_accuracy(
    selected_forecasts: pd.DataFrame,
    actuals: pd.DataFrame,
) -> tuple[pd.DataFrame, dict]:
    """Compare selected forecasts with actual generation."""

    forecast_data = selected_forecasts.copy()
    actual_data = actuals.copy()

    # Ensure both datasets use the same timestamp format.
    for df in (forecast_data, actual_data):
        df["startTime"] = pd.to_datetime(
            df["startTime"],
            utc=True,
            errors="raise",
        )

    forecast_data = forecast_data.rename(
        columns={
            "generation": "forecastGeneration",
            "publishTime": "forecastPublishTime",
        }
    )

    actual_data = actual_data.rename(
        columns={"generation": "actualGeneration"}
    )

    comparison = forecast_data.merge(
        actual_data[["startTime", "actualGeneration"]],
        on="startTime",
        how="inner",
        validate="one_to_one",
    )

    comparison["error"] = (
        comparison["forecastGeneration"]
        - comparison["actualGeneration"]
    )
    comparison["absoluteError"] = comparison["error"].abs()
    comparison["squaredError"] = comparison["error"] ** 2

    if comparison.empty:
        metrics = {
            "sampleCount": 0,
            "mae": None,
            "rmse": None,
            "bias": None,
        }
    else:
        metrics = {
            "sampleCount": len(comparison),
            "mae": float(comparison["absoluteError"].mean()),
            "rmse": float(comparison["squaredError"].mean() ** 0.5),
            "bias": float(comparison["error"].mean()),
        }

    return comparison, metrics


def aggregate_actuals_hourly(
    actuals: pd.DataFrame,
) -> pd.DataFrame:
    """
    Convert 30-minute average power readings into hourly
    average power values.

    Only complete hours with two valid half-hour readings
    are included.
    """

    if actuals.empty:
        return pd.DataFrame(
            columns=["startTime", "generation"]
        )

    df = actuals[["startTime", "generation"]].copy()

    df["startTime"] = pd.to_datetime(
        df["startTime"],
        utc=True,
        errors="raise",
    )
    df["generation"] = pd.to_numeric(
        df["generation"],
        errors="raise",
    )

    df["hour"] = df["startTime"].dt.floor("h")

    hourly = (
        df.groupby("hour", as_index=False)
        .agg(
            generation=("generation", "mean"),
            readingCount=("generation", "count"),
        )
    )

    hourly = hourly.loc[
        hourly["readingCount"] == 2
    ]

    return (
        hourly.rename(columns={"hour": "startTime"})
        [["startTime", "generation"]]
        .reset_index(drop=True)
    )
