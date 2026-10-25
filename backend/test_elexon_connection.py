
import asyncio
from datetime import date

from services.elexon import (
    fetch_wind_actuals,
    fetch_wind_forecasts,
)


async def main() -> None:
    start = date(2026, 1, 1)
    end = date(2026, 1, 2)

    actuals = await fetch_wind_actuals(start, end)
    forecasts = await fetch_wind_forecasts(start, end)

    print("Actual wind records:", len(actuals))
    print("Forecast records:", len(forecasts))

    print("\nActual sample:")
    print(actuals.head())


    print("\nActual interval differences:")
    print(
        actuals["startTime"]
        .sort_values()
        .drop_duplicates()
        .diff()
        .value_counts()
        .head()
    )

    print("\nForecast interval differences:")
    print(
        forecasts["startTime"]
        .sort_values()
        .drop_duplicates()
        .diff()
        .value_counts()
        .head()
    )


    print("\nForecast sample:")
    print(forecasts.head())


if __name__ == "__main__":
    asyncio.run(main())
