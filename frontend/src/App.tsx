import { useEffect, useState } from "react";

import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";

import {
  Activity,
  AlertTriangle,
  CalendarDays,
  RefreshCw,
  Wind,
} from "lucide-react";

type AccuracyMetrics = {
  decisionStart: string;
  decisionEnd: string;
  sampleCount: number;
  mae: number | null;
  rmse: number | null;
  bias: number | null;
};

type ForecastRecord = {
  startTime: string;
  forecastPublishTime: string;
  forecastGeneration: number;
  actualGeneration: number;
  error: number;
};

type ForecastResponse = {
  decisionStart: string;
  decisionEnd: string;
  records: ForecastRecord[];
  sampleCount: number;
};

const API_URL = "http://127.0.0.1:8000";

function formatNumber(value: number | null): string {
  if (value === null) return "—";

  return new Intl.NumberFormat("en-GB", {
    maximumFractionDigits: 1,
  }).format(value);
}

function App() {
  const [metrics, setMetrics] = useState<AccuracyMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDeliveryDate, setSelectedDeliveryDate] = useState("");
  const [records, setRecords] = useState<ForecastRecord[]>([]);
  const [chartLoading, setChartLoading] = useState(true);

  async function loadMetrics() {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/api/accuracy`);

      if (!response.ok) {
        throw new Error("Unable to load forecast accuracy.");
      }

      const data: AccuracyMetrics = await response.json();
      setMetrics(data);
    } catch {
      setError(
        "Could not connect to the backend. Check that FastAPI is running.",
      );
    } finally {
      setLoading(false);
    }
  }

  async function loadForecasts() {
    setChartLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/forecasts`);

      if (!response.ok) {
        throw new Error("Unable to load forecast records.");
      }

      const data: ForecastResponse = await response.json();

      const sortedRecords = [...data.records].sort(
        (a, b) =>
          new Date(a.startTime).getTime() - new Date(b.startTime).getTime(),
      );

      setRecords(sortedRecords);
    } catch {
      setError("Could not load forecast comparison data.");
    } finally {
      setChartLoading(false);
    }
  }

  useEffect(() => {
    void loadMetrics();
    void loadForecasts();
  }, []);

  const cards = [
    {
      label: "MEAN ABSOLUTE ERROR",
      value: metrics?.mae ?? null,
      unit: "MW",
      description: "Average absolute forecast error",
    },
    {
      label: "ROOT MEAN SQUARED ERROR",
      value: metrics?.rmse ?? null,
      unit: "MW",
      description: "Penalises larger forecast errors",
    },
    {
      label: "FORECAST BIAS",
      value: metrics?.bias ?? null,
      unit: "MW",
      description:
        metrics && metrics.bias !== null
          ? metrics.bias > 0
            ? "Wind generation was over-forecast on average"
            : metrics.bias < 0
              ? "Wind generation was under-forecast on average"
              : "No average forecast bias"
          : "Average forecast minus actual",
    },
    {
      label: "VALID HOURLY INTERVALS",
      value: metrics?.sampleCount ?? null,
      unit: "",
      description: "Matched forecast and actual records",
    },
  ];

  const filteredRecords = records.filter((record) => {
    if (!selectedDeliveryDate) return true;

    const ukDate = new Intl.DateTimeFormat("en-CA", {
      timeZone: "Europe/London",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    }).format(new Date(record.startTime));

    return ukDate === selectedDeliveryDate;
  });

  return (
    <main className="min-h-screen bg-[#f5f7f5] text-[#18251f]">
      <div className="mx-auto max-w-[1440px] px-5 sm:px-8 lg:px-12">
        <header className="flex min-h-[82px] items-center justify-between border-b border-[#dce3dc]">
          <div className="flex items-center gap-3">
            <div className="grid size-11 place-items-center bg-[#214e3a] text-white">
              <Wind size={22} />
            </div>

            <div>
              <p className="text-sm font-bold tracking-[1.2px]">
                WIND / INSIGHT
              </p>
              <p className="mt-1 text-[10px] tracking-[1.5px] text-[#77847b]">
                UK POWER ANALYTICS
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-[11px] tracking-wider text-[#506458]">
            <span className="size-2 rounded-full bg-[#438760]" />
            ELEXON DATA
          </div>
        </header>

        <section className="flex flex-col justify-between gap-5 py-10 sm:flex-row sm:items-end">
          <div>
            <p className="text-[10px] font-bold tracking-[1.8px] text-[#51715f]">
              ENERGY PROCUREMENT / ANALYTICS
            </p>

            <h1 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
              Wind generation intelligence
            </h1>

            <p className="mt-3 text-sm text-[#758078]">
              Forecast performance for January 2026 purchase decisions.
            </p>
          </div>

          <button
            type="button"
            onClick={() => void loadMetrics()}
            disabled={loading}
            className="inline-flex items-center justify-center gap-2 border border-[#cfd8d0] bg-white px-4 py-3 text-sm text-[#214e3a] transition hover:bg-[#edf3ee] disabled:cursor-wait disabled:opacity-60"
          >
            <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
            Refresh
          </button>
        </section>

        <section className="flex flex-col gap-3 border border-[#dce3dc] bg-white p-4 sm:flex-row sm:items-center sm:gap-6">
          <div className="flex items-center gap-2 text-[10px] font-bold tracking-wider text-[#506458]">
            <CalendarDays size={18} />
            DECISION PERIOD
          </div>

          <p className="text-sm font-semibold">01 Jan 2026 — 31 Jan 2026</p>

          <div className="flex items-center gap-2 text-xs text-[#68766c] sm:ml-auto">
            <span className="size-2 rounded-full bg-[#438760]" />
            Historical analysis
          </div>
        </section>

        {error && (
          <div
            role="alert"
            className="mt-5 flex flex-wrap items-center gap-3 border border-[#e7c8c1] bg-[#fff5f2] p-4 text-sm text-[#8d3527]"
          >
            <AlertTriangle size={18} />
            <span className="flex-1">{error}</span>
            <button
              type="button"
              onClick={() => void loadMetrics()}
              className="underline"
            >
              Retry
            </button>
          </div>
        )}

        <section className="my-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {cards.map((card) => (
            <article
              key={card.label}
              className="min-w-0 border border-[#dce3dc] bg-white p-5"
            >
              <div className="flex items-center justify-between gap-2">
                <p className="text-[10px] font-bold tracking-wide text-[#68766c]">
                  {card.label}
                </p>
                <Activity size={18} className="shrink-0 text-[#65816f]" />
              </div>

              <div className="mt-6 flex flex-wrap items-baseline gap-2">
                <p className="break-words text-3xl font-semibold tracking-tight">
                  {loading ? "..." : formatNumber(card.value)}
                </p>
                {card.unit && (
                  <span className="text-xs text-[#718076]">{card.unit}</span>
                )}
              </div>

              <p className="mt-3 text-xs leading-5 text-[#758078]">
                {card.description}
              </p>
            </article>
          ))}
        </section>

        <section className="border border-[#dce3dc] bg-white p-5 sm:p-6">
          <div className="mt-6 flex flex-wrap items-end justify-between gap-4 border-y border-[#e5eae5] py-4">
            <div className="flex flex-col gap-2">
              <label
                htmlFor="delivery-date"
                className="text-xs font-semibold text-[#506458]"
              >
                DELIVERY DATE
              </label>

              <input
                id="delivery-date"
                type="date"
                min="2026-01-01"
                max="2026-02-01"
                value={selectedDeliveryDate}
                onChange={(event) =>
                  setSelectedDeliveryDate(event.target.value)
                }
                className="border border-[#cfd8d0] bg-white px-3 py-2 text-sm outline-none focus:border-[#527d65]"
              />
            </div>

            <div className="flex items-center gap-3">
              <span className="text-xs text-[#758078]">
                {filteredRecords.length} hourly intervals
              </span>

              <button
                type="button"
                onClick={() => setSelectedDeliveryDate("")}
                disabled={!selectedDeliveryDate}
                className="border border-[#cfd8d0] px-3 py-2 text-xs text-[#214e3a] hover:bg-[#edf3ee] disabled:cursor-not-allowed disabled:opacity-40"
              >
                Show all dates
              </button>
            </div>
          </div>

          <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
            <div>
              <h2 className="text-lg font-semibold">Forecast performance</h2>
              <p className="mt-2 text-sm text-[#758078]">
                Compare predicted wind generation with actual output.
              </p>
            </div>

            <span className="w-fit bg-[#edf3ee] px-3 py-2 text-[10px] tracking-wider text-[#315c43]">
              HOURLY RESOLUTION
            </span>
          </div>

          <div className="mt-6 h-[360px] w-full">
            {chartLoading ? (
              <div className="flex h-full items-center justify-center text-sm text-[#758078]">
                Loading forecast data...
              </div>
            ) : filteredRecords.length === 0 ? (
              <div className="flex h-full items-center justify-center text-sm text-[#758078]">
                No forecast comparison data available.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={filteredRecords}
                  margin={{ top: 12, right: 16, left: 8, bottom: 8 }}
                >
                  <CartesianGrid stroke="#e5eae5" strokeDasharray="3 3" />

                  <XAxis
                    dataKey="startTime"
                    tickFormatter={(value: string) =>
                      new Date(value).toLocaleDateString("en-GB", {
                        day: "2-digit",
                        month: "short",
                        timeZone: "Europe/London",
                      })
                    }
                    minTickGap={32}
                    tick={{ fontSize: 11, fill: "#758078" }}
                  />

                  <YAxis
                    width={75}
                    tick={{ fontSize: 11, fill: "#758078" }}
                    tickFormatter={(value: number) =>
                      `${(value / 1000).toFixed(0)}k`
                    }
                    label={{
                      value: "Generation (MW)",
                      angle: -90,
                      position: "insideLeft",
                      style: { fill: "#758078", fontSize: 11 },
                    }}
                  />

                  <Tooltip
                    labelFormatter={(value) =>
                      new Date(String(value)).toLocaleString("en-GB", {
                        dateStyle: "medium",
                        timeStyle: "short",
                        timeZone: "Europe/London",
                      })
                    }
                    formatter={(value, name) => [
                      `${Number(value).toLocaleString("en-GB", {
                        maximumFractionDigits: 1,
                      })} MW`,
                      name === "forecastGeneration" ? "Forecast" : "Actual",
                    ]}
                  />

                  <Legend
                    formatter={(value) =>
                      value === "forecastGeneration" ? "Forecast" : "Actual"
                    }
                  />

                  <Line
                    type="monotone"
                    dataKey="forecastGeneration"
                    name="forecastGeneration"
                    stroke="#527d65"
                    strokeWidth={2}
                    dot={false}
                    connectNulls={false}
                  />

                  <Line
                    type="monotone"
                    dataKey="actualGeneration"
                    name="actualGeneration"
                    stroke="#d28a51"
                    strokeWidth={2}
                    dot={false}
                    connectNulls={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </section>

        <section className="mt-6 border border-[#dce3dc] bg-white">
          <div className="flex flex-col justify-between gap-3 border-b border-[#e5eae5] p-5 sm:flex-row sm:items-center">
            <div>
              <h2 className="text-lg font-semibold">Hourly generation data</h2>
              <p className="mt-1 text-sm text-[#758078]">
                Forecast values compared with actual wind generation.
              </p>
            </div>

            <span className="text-xs text-[#758078]">
              {filteredRecords.length} records
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full min-w-[680px] text-left text-sm">
              <thead className="bg-[#f5f7f5] text-[11px] uppercase tracking-wide text-[#68766c]">
                <tr>
                  <th className="px-5 py-3 font-semibold">
                    Delivery time (UK)
                  </th>
                  <th className="px-5 py-3 text-right font-semibold">
                    Forecast (MW)
                  </th>
                  <th className="px-5 py-3 text-right font-semibold">
                    Actual (MW)
                  </th>
                  <th className="px-5 py-3 text-right font-semibold">
                    Error (MW)
                  </th>
                </tr>
              </thead>

              <tbody className="divide-y divide-[#edf0ed]">
                {filteredRecords.map((record) => (
                  <tr
                    key={record.startTime}
                    className="transition hover:bg-[#f8faf8]"
                  >
                    <td className="whitespace-nowrap px-5 py-3 text-[#34483b]">
                      {new Date(record.startTime).toLocaleString("en-GB", {
                        day: "2-digit",
                        month: "short",
                        year: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                        timeZone: "Europe/London",
                      })}
                    </td>

                    <td className="px-5 py-3 text-right tabular-nums">
                      {formatNumber(record.forecastGeneration)}
                    </td>

                    <td className="px-5 py-3 text-right tabular-nums">
                      {formatNumber(record.actualGeneration)}
                    </td>

                    <td
                      className={`px-5 py-3 text-right font-medium tabular-nums ${
                        record.error > 0
                          ? "text-[#a65d2e]"
                          : record.error < 0
                            ? "text-[#376d51]"
                            : "text-[#68766c]"
                      }`}
                    >
                      {record.error > 0 ? "+" : ""}
                      {formatNumber(record.error)}
                    </td>
                  </tr>
                ))}

                {filteredRecords.length === 0 && (
                  <tr>
                    <td
                      colSpan={4}
                      className="px-5 py-12 text-center text-[#758078]"
                    >
                      No matching generation records found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        <footer className="flex flex-col justify-between gap-3 py-6 text-[9px] tracking-wider text-[#7c877e] sm:flex-row">
          <span>DATA SOURCE: ELEXON FUELHH / WINDFOR</span>
          <span>PROTOTYPE CUTOFF: DELIVERY TIME - 24 HOURS</span>
        </footer>
      </div>
    </main>
  );
}

export default App;
