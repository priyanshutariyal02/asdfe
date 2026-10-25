# Wind Insight - UK Wind Generation Forecast Dashboard

Wind Insight is a web application that helps electricity procurement teams understand wind power forecasts and evaluate how accurate those forecasts are.

Electricity companies need to buy enough electricity to meet customer demand. Since wind generation depends on weather, the amount of electricity produced by wind farms can be different from the forecast.

This application uses historical wind generation data from **Elexon**, the UK's electricity market data provider, to compare forecasted wind generation with actual generation.

The first version focuses on purchase decisions made during January 2026.

### Live Demo

- Frontend: https://frontend-ashen-sigma-55.vercel.app/
- Backend Health Check: https://uk-wind-forecast-api-1qo5.onrender.com/api/health
- API Documentation: https://uk-wind-forecast-api-1qo5.onrender.com/docs

## Features

- **Forecast accuracy:** Measure how close wind generation forecasts are to actual generation.
- **Accuracy metrics:** View Mean Absolute Error (MAE), Root Mean Squared Error (RMSE), and forecast bias.
- **Forecast comparison chart:** Compare forecasted and actual wind generation over time.
- **Date filter:** Select a delivery date to inspect hourly generation data.
- **Hourly data table:** View forecast, actual generation, and forecast error for each hour.
- **Data caching:** Reuse recently fetched data to reduce repeated requests to Elexon.
- **API documentation:** Explore the backend API using FastAPI's interactive documentation.

## Technology Stack

| Area                | Technology                |
| ------------------- | ------------------------- |
| Frontend            | React, TypeScript, Vite   |
| Styling             | Tailwind CSS              |
| Charts              | Recharts                  |
| Icons               | Lucide React              |
| Backend             | Python, FastAPI           |
| Data processing     | Pandas                    |
| Backend testing     | Pytest                    |
| Containerization    | Docker and Docker Compose |
| Frontend deployment | Vercel                    |
| Backend deployment  | Render                    |

## Data Sources

This application uses only national-level wind generation data from Elexon.

### 1. Actual wind generation

Source: [Elexon FUELHH API documentation](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream)

The application filters the dataset to include records where `fuelType` is `WIND`.

Important fields:

- `startTime`: The start time of the generation interval.
- `generation`: The recorded wind generation, measured in MW.

The actual generation dataset provides readings at 30-minute intervals.

### 2. Forecasted wind generation

Source: [Elexon WINDFOR API documentation](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream)

Important fields:

- `startTime`: The delivery interval the forecast refers to.
- `publishTime`: When the forecast was published.
- `generation`: The forecasted wind generation, measured in MW.

The returned forecast data used in this prototype has hourly intervals.

## Analysis Period

The application evaluates purchase decisions made from **1 January to 31 January 2026**, including delivery intervals in February where applicable.

The forecast cutoff used in this prototype is:

`Decision cutoff = Delivery start time - 24 hours`

For each delivery interval, the application selects the latest forecast whose `publishTime` is at or before the cutoff.

**Important:** The 24-hour cutoff is a prototype assumption. It must be verified against the client's actual purchasing process and applicable market deadlines before the results are used for operational decisions.

## How the Application Works

1. The backend requests actual and forecast data from Elexon.
2. The backend caches the fetched data for a configurable period.
3. The forecast analysis applies the selected decision cutoff.
4. Actual generation is converted from 30-minute readings to hourly average power values.
5. Forecasts are matched with actual generation at the same hourly delivery timestamp.
6. The backend calculates forecast accuracy metrics.
7. The frontend displays the results in metric cards, a comparison chart, and a data table.

Only complete hours with two valid half-hour actual readings are retained during hourly aggregation.

## Understanding the Accuracy Metrics

### Mean Absolute Error (MAE)

MAE measures the average absolute difference between forecasted and actual generation.

A lower MAE means that forecasts are closer to actual generation on average.

### Root Mean Squared Error (RMSE)

RMSE measures forecast error while giving more weight to larger errors.

A lower RMSE generally indicates better forecast accuracy.

### Forecast Bias

Forecast bias is calculated as:

`Bias = Average(Forecast - Actual)`

- **Positive bias:** The forecast overestimated wind generation on average.
- **Negative bias:** The forecast underestimated wind generation on average.
- **Zero bias:** There was no average forecast error, although individual errors may still exist.

All three metrics are expressed in MW.

These metrics help procurement teams understand forecast uncertainty. They do not directly calculate the additional electricity that must be purchased because customer demand and other generation sources are outside the scope of this version.

## Project Structure

```text
reint-ai-ass/
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── index.css
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── backend/
│   ├── services/
│   │   ├── cache.py
│   │   ├── elexon.py
│   │   └── forecast_analysis.py
│   ├── main.py
│   ├── requirements.txt
│   └── test_forecast_analysis.py
├── docker-compose.yml
├── .gitignore
└── README.md
```

The structure above shows the main project files. Additional configuration and test files may also be present.

## Getting Started

### Prerequisites

Install the following tools:

- Node.js and npm
- Python 3.9 or a compatible newer version
- Git
- Docker and Docker Compose (for containerized execution)

### 1. Clone the repository

```bash
git clone https://github.com/priyanshutariyal02/asdfe.git
cd reint-ai-ass
```

### 2. Start the backend

Open a terminal:

```bash
cd backend
python -m venv venv
```

Activate the virtual environment.

**macOS or Linux:**

```bash
source venv/bin/activate
```

**Windows:**

```powershell
venv\Scripts\activate
```

**Configure environment variables**

Copy the example environment file:

```bash
cp .env.example .env
```

Open `backend/.env` and configure the frontend URL:

```env
FRONTEND_URL=http://localhost:5173
```

For production, set `FRONTEND_URL` in your backend hosting provider's environment variables to your deployed frontend URL.

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

Start FastAPI:

```bash
uvicorn main:app --reload
```

The backend should now be available at:

- API base: http://127.0.0.1:8000
- Health check: http://127.0.0.1:8000/api/health
- Interactive API documentation: http://127.0.0.1:8000/docs

The health endpoint should return:

```json
{
  "status": "ok"
}
```

### 3. Start the frontend

Open a second terminal:

```bash
cd frontend
npm install
```

**Configure environment variables**

Copy the example environment file:

```bash
cp .env.example .env
```

Open `frontend/.env` and configure the backend API URL:

```env
# Frontend API URL for local development
VITE_API_BASE_URL=http://127.0.0.1:8000
```

For production, set `VITE_API_BASE_URL` in Vercel to your deployed backend URL.

Start the frontend:

```bash
npm run dev
```

Open the local URL shown by Vite, usually [http://localhost:5173](http://localhost:5173).

The backend must be running for the dashboard to load its data.

## API Endpoints

| Method | Endpoint         | Purpose                                               |
| ------ | ---------------- | ----------------------------------------------------- |
| GET    | `/api/health`    | Check whether the backend is running                  |
| GET    | `/api/forecasts` | Get selected forecasts, actual generation, and errors |
| GET    | `/api/accuracy`  | Get forecast accuracy metrics                         |

The forecast and accuracy endpoints use January 2026 decision dates by default.

You can also supply a date range:

```text
/api/accuracy?decision_start=2026-01-01&decision_end=2026-01-31
```

The endpoints return JSON data for the frontend.

## Data Caching

The backend uses an in-memory cache to avoid fetching the same data repeatedly.

The default cache expiration is one hour.

Set the `CACHE_TTL_SECONDS` environment variable to change it:

```bash
CACHE_TTL_SECONDS=1800
```

This example sets the cache expiration to 30 minutes.

Because the cache is stored in memory, its contents are cleared when the backend restarts. Each backend process also maintains its own cache.

## Docker

Docker is intended to make the application easier to run in a consistent environment.

The repository includes a `docker-compose.yml` file for the container setup. Complete and verify the Docker configuration before relying on containerized execution.

Once the configuration is ready, start the application from the project root with:

```bash
docker compose up --build
```

Stop the containers with:

```bash
docker compose down
```

The frontend and backend must be configured with the correct API address for the environment in which they run. In particular, `localhost` inside a container does not refer to another container.

## Deployment

### Frontend — Vercel

The React frontend is intended to be deployed on [Vercel](https://vercel.com/).

Typical deployment steps:

1. Push the project to a Git repository.
2. Import the repository into Vercel.
3. Set the frontend root directory to `frontend`.
4. Configure the build command as `npm run build`.
5. Configure the output directory as `dist`.
6. Set the production API URL to the publicly deployed backend URL.
7. Deploy and verify the application.

The backend must be hosted separately unless a suitable backend deployment architecture is configured.

### Backend

The FastAPI backend can be deployed to a Python-compatible hosting service or a container hosting platform.

Before deployment:

- Configure the production CORS origins.
- Set the cache expiration as needed.
- Use HTTPS for public API access.
- Verify all API endpoints against the production data source.

**Deployment status:** Update this section with the actual deployed URLs after deployment has been completed and verified.

## Running Backend Tests

Activate the backend virtual environment and run:

```bash
cd backend
pytest -v
```

The current test suite covers forecast selection, accuracy calculations, and hourly aggregation.

## Known Limitations

- The application uses only national-level wind generation data from Elexon.
- It does not include electricity demand, wholesale prices, thermal generation, or other energy sources.
- The 24-hour forecast cutoff is an assumption and is not confirmed as the official market deadline.
- Actual generation is aggregated to hourly average power for comparison with hourly forecasts.
- Forecast accuracy results depend on correct timestamp alignment and forecast publication filtering.
- The in-memory cache is not shared across multiple backend instances.
- This is a prototype for analysis and demonstration, not a production electricity procurement system.

## Future Improvements

- Validate the forecast cutoff with the client.
- Add more detailed data-quality and forecast-eligibility checks.
- Add tests for date boundaries, missing readings, and forecast publication times.
- Improve cache management and error reporting.
- Complete Docker configuration and deployment.
- Add pagination or export options for large data tables.
- Improve deployment configuration and production monitoring.

## AI Tool Usage

AI tools, including ChatGPT, were used to assist with project planning, implementation guidance, code development, debugging, and documentation.

All generated code and analysis should be reviewed and tested before the application is used in a production environment.

## License

Made by Priyanshu Tariyal
