# Smoke Test Checklist

Run from the project root after setup:

```powershell
f1-demo --start-year 2021 --end-year 2025 --backtest
f1-serve --reload
```

Acceptance checks:

- Data build finishes and `data/cache` contains FastF1 cache files.
- Processed Parquet files exist:
  - `data/processed/races.parquet`
  - `data/processed/qualifying.parquet`
  - `data/processed/drivers.parquet`
  - `data/processed/constructors.parquet`
  - `data/processed/modeling_table.parquet`
- Dataset metadata exists at `data/processed/dataset_metadata.json`.
- Training writes calibrated model artifacts:
  - `data/models/baseline_model.joblib`
  - `data/models/model_metadata.json`
  - `data/metrics/train_metrics.json`
- Calibration report exists at `data/metrics/podium_calibration.csv`.
- Backtest writes:
  - `data/metrics/backtest_metrics.csv`
  - `data/metrics/backtest_predictions.parquet`
- Backtest metrics include race-by-race `podium_brier`, `win_brier`, `top10_brier`, and `finish_mae`.
- `f1-predict-next` writes `data/processed/latest_predictions.parquet`.
- `GET /api/health` returns `ok: true` with model, dataset, and calibration artifacts present.
- `GET /api/predictions/next` returns race metadata, model metadata, prediction mode, and prediction rows.
- Homepage at `http://127.0.0.1:8000` renders next-race predictions without broken API calls.
