from datetime import date, timedelta

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from services.cache import AsyncTTLCache
from services.elexon import (
    fetch_wind_actuals,
    fetch_wind_forecasts,
)
from services.forecast_analysis import (
    calculate_accuracy,
    create_decision_cutoffs,
    select_forecasts,
    aggregate_actuals_hourly
)


app = FastAPI(
    title="UK Wind Forecast API",
    description="Wind generation forecasts and accuracy analysis.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

cache = AsyncTTLCache()


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


async def load_analysis(
    decision_start: date,
    decision_end: date,
) -> tuple[pd.DataFrame, dict]:
    if decision_start > decision_end:
        raise HTTPException(
            status_code=400,
            detail="decision_start must not be after decision_end",
        )

    # With a 24-hour cutoff, delivery occurs one day after
    # the decision date. Fetch an extra day to cover the range.
    delivery_start = decision_start + timedelta(days=1)
    delivery_end = decision_end + timedelta(days=1)

    try:
        actuals = await cache.get_or_set(
            f"actuals:{delivery_start}:{delivery_end}",
            lambda: fetch_wind_actuals(
                delivery_start,
                delivery_end,
            ),
        )
        
        actuals = aggregate_actuals_hourly(actuals)

        # Include the previous day for January 1 decisions.
        forecast_start = decision_start - timedelta(days=1)

        forecasts = await cache.get_or_set(
            f"forecasts:{forecast_start}:{decision_end}",
            lambda: fetch_wind_forecasts(
                forecast_start,
                decision_end,
            ),
        )

        if actuals.empty:
            return pd.DataFrame(), {
                "sampleCount": 0,
                "mae": None,
                "rmse": None,
                "bias": None,
            }

        cutoffs = create_decision_cutoffs(actuals["startTime"])

        # Keep delivery intervals whose decision cutoff falls
        # within the requested decision-date range.
        cutoff_dates = cutoffs["decisionCutoff"].dt.date

        cutoffs = cutoffs.loc[
            (cutoff_dates >= decision_start)
            & (cutoff_dates <= decision_end)
        ]

        selected = select_forecasts(forecasts, cutoffs)
        comparison, metrics = calculate_accuracy(
            selected,
            actuals,
        )

        return comparison, metrics

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to load or process Elexon data",
        ) from exc


def to_records(df: pd.DataFrame) -> list[dict]:
    if df.empty:
        return []

    result = df.copy()

    for column in result.select_dtypes(
        include=["datetimetz"]
    ).columns:
        result[column] = result[column].map(
            lambda value: value.isoformat() if pd.notna(value) else None
        )

    return result.astype(object).where(
        pd.notna(result), None
    ).to_dict(orient="records")


@app.get("/api/forecasts")
async def get_forecasts(
    decision_start: date = Query(default=date(2026, 1, 1)),
    decision_end: date = Query(default=date(2026, 1, 31)),
) -> dict:
    comparison, metrics = await load_analysis(
        decision_start,
        decision_end,
    )

    return {
        "decisionStart": decision_start.isoformat(),
        "decisionEnd": decision_end.isoformat(),
        "records": to_records(comparison),
        "sampleCount": metrics["sampleCount"],
    }


@app.get("/api/accuracy")
async def get_accuracy(
    decision_start: date = Query(default=date(2026, 1, 1)),
    decision_end: date = Query(default=date(2026, 1, 31)),
) -> dict:
    comparison, metrics = await load_analysis(
        decision_start,
        decision_end,
    )

    return {
        "decisionStart": decision_start.isoformat(),
        "decisionEnd": decision_end.isoformat(),
        **metrics,
    }
