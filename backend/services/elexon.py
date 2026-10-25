
from datetime import date

import httpx
import pandas as pd


BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"


async def fetch_dataset(
    dataset: str,
    start_date: date,
    end_date: date,
) -> list[dict]:
    """Fetch dataset records for a date range from Elexon."""

    if start_date > end_date:
        raise ValueError("start_date must not be after end_date")

    if dataset not in {"FUELHH", "WINDFOR"}:
        raise ValueError("Unsupported dataset")
        

    url = f"{BASE_URL}/datasets/{dataset}/stream"

    if dataset == "FUELHH":
        params = {
            "settlementDateFrom": start_date.isoformat(),
            "settlementDateTo": end_date.isoformat(),
        }
    else:
        params = {
            "publishDateTimeFrom": f"{start_date.isoformat()}T00:00:00Z",
            "publishDateTimeTo": f"{end_date.isoformat()}T23:59:59Z",
        }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    if not isinstance(data, list):
        raise ValueError(
            f"Unexpected response format from {dataset}"
        )

    return data


async def fetch_wind_actuals(
    start_date: date,
    end_date: date,
) -> pd.DataFrame:
    """Fetch actual generation and keep wind records only."""

    records = await fetch_dataset(
        "FUELHH",
        start_date,
        end_date,
    )

    df = pd.DataFrame(records)

    if df.empty:
        return pd.DataFrame(
            columns=["startTime", "generation"]
        )

    required = {"startTime", "generation", "fuelType"}
    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"FUELHH is missing fields: {sorted(missing)}"
        )

    df = df.loc[
        df["fuelType"].eq("WIND"),
        ["startTime", "generation"],
    ].copy()

    df["startTime"] = pd.to_datetime(
        df["startTime"], utc=True, errors="coerce"
    )
    df["generation"] = pd.to_numeric(
        df["generation"], errors="coerce"
    )

    return (
        df.dropna(subset=["startTime", "generation"])
        .sort_values("startTime")
        .reset_index(drop=True)
    )


async def fetch_wind_forecasts(
    start_date: date,
    end_date: date,
) -> pd.DataFrame:
    """Fetch wind forecasts, preserving publication times."""

    records = await fetch_dataset(
        "WINDFOR",
        start_date,
        end_date,
    )

    df = pd.DataFrame(records)

    if df.empty:
        return pd.DataFrame(
            columns=["startTime", "publishTime", "generation"]
        )

    required = {"startTime", "publishTime", "generation"}
    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"WINDFOR is missing fields: {sorted(missing)}"
        )

    df = df[["startTime", "publishTime", "generation"]].copy()

    for column in ("startTime", "publishTime"):
        df[column] = pd.to_datetime(
            df[column], utc=True, errors="coerce"
        )

    df["generation"] = pd.to_numeric(
        df["generation"], errors="coerce"
    )

    return (
        df.dropna(
            subset=["startTime", "publishTime", "generation"]
        )
        .sort_values(["startTime", "publishTime"])
        .reset_index(drop=True)
    )
