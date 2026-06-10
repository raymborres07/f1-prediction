# f1-predictor

Baseline Formula 1 podium and finishing-position predictor built with Python 3.10+, FastF1, scikit-learn, FastAPI, and a lightweight static frontend.

## What It Does

- Downloads historical schedules, race results, and qualifying results with FastF1 caching enabled.
- Builds one feature row per driver per race using only data available before that race starts.
- Trains baseline models for:
  - podium probability
  - expected finish position
- Serves predictions through a FastAPI endpoint.
- Displays next race predictions in a simple web page.

## Project Layout

```text
f1-predictor/
  data/
    cache/        # FastF1 cache
    processed/    # ingested and feature datasets
    models/       # trained model artifacts
  src/f1_predictor/
    ingest/       # FastF1 data collection
    features/     # feature engineering
    models/       # training and inference
    api/          # FastAPI app
    web/          # static frontend
```

## Setup

```powershell
cd f1-predictor
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-pipeline.txt
pip install -e .
```

`requirements.txt` is deploy-focused for FastAPI inference. `requirements-pipeline.txt` adds FastF1 for local ingestion and retraining. FastF1 downloads live timing data and Ergast-compatible schedule/result data. The first run can take a while; later runs reuse `data/cache`.

## Run The Pipeline

```powershell
python -m f1_predictor.ingest.pipeline --start-year 2021 --end-year 2025
python -m f1_predictor.features.pipeline
python -m f1_predictor.models.train
python -m f1_predictor.models.backtest
python -m f1_predictor.models.predict_next
```

Or use the installed command aliases:

```powershell
f1-ingest --start-year 2021 --end-year 2025
f1-ingest-rich --start-year 2023 --end-year 2026 --include-telemetry
f1-features
f1-features-rich
f1-train
f1-backtest
f1-predict-next
f1-serve --reload
```

One-click retrain plus dashboard refresh:

```powershell
f1-demo --start-year 2021 --end-year 2025
```

Add `--backtest` to include walk-forward metrics in the same run.

To train through the most recently completed season, pass the relevant year range to ingestion first.

## Serve Predictions

```powershell
uvicorn f1_predictor.api.main:app --reload
```

Or:

```powershell
f1-serve --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

API endpoints:

- `GET /api/health`
- `GET /api/next-race`
- `GET /api/predictions/next`
- `GET /api/predictions/{year}/{round_number}`
- `GET /api/reports/podium-calibration`
- `GET /api/reports/backtest`

## Deploy To Vercel

This repo includes `vercel.json` and `api/index.py` for Vercel's Python runtime. The app boots from committed lightweight demo artifacts in `src/f1_predictor/demo_data`, so deployment does not run ingestion or training.

Deploy from the `f1-predictor` directory:

```powershell
vercel
```

The production app serves the FastAPI API and mounted static frontend as one product. Local generated artifacts under `data/` are ignored by Git; refresh committed demo artifacts intentionally after retraining.

## Notes

The dataset build writes clean processed tables for `races`, `qualifying`, `drivers`, `constructors`, and `modeling_table`, plus timestamped Parquet copies for reproducibility. The feature pipeline is intentionally leak-aware. For a target race, rolling driver and constructor form only use prior races. Grid position and teammate qualifying deltas use qualifying data for the target race when available; otherwise they fall back to neutral values so upcoming race predictions can still be generated before qualifying.

Training calibrates win, podium, and top-10 classifiers with scikit-learn when enough data is available. Backtesting walks forward race by race and writes `data/metrics/backtest_metrics.csv` with Brier scores and finish MAE.

## Rich Data Pipeline

For deeper modeling, run the normalized FastF1/OpenF1 pipeline:

```powershell
f1-ingest-rich --start-year 2023 --end-year 2026
f1-features-rich
```

Add `--include-telemetry` to aggregate OpenF1 car/location streams. This can be large; use `--max-openf1-sessions 5` for smoke tests.

The rich pipeline writes versioned raw pulls under `data/raw/fastf1` and `data/raw/openf1`, then normalized Parquet tables under `data/processed/rich`:

- `seasons`, `events`, `sessions`
- `drivers`, `constructors`, `grid_entries`
- `qualifying`, `race_results`, `lap_times`
- `stint_summaries`, `tyre_usage`, `pit_stops`
- `weather_conditions`, `session_conditions`
- `telemetry_aggregates`
- `pre_race_features`, `race_sim_inputs`

FastF1 remains the primary source for schedules, results, qualifying, laps, and weather. OpenF1 supplements historical timing, grid, stints, pit, weather, and telemetry data from 2023 onward.
