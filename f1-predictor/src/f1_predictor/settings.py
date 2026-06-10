from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
DEMO_DATA_DIR = PACKAGE_DIR / "demo_data"
CACHE_DIR = DATA_DIR / "cache"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
MODEL_DIR = DATA_DIR / "models"
METRICS_DIR = DATA_DIR / "metrics"
DEMO_PROCESSED_DIR = DEMO_DATA_DIR / "processed"
DEMO_MODEL_DIR = DEMO_DATA_DIR / "models"
DEMO_METRICS_DIR = DEMO_DATA_DIR / "metrics"

SCHEDULE_PATH = PROCESSED_DIR / "schedule.parquet"
RACE_RESULTS_PATH = PROCESSED_DIR / "race_results.parquet"
QUALIFYING_RESULTS_PATH = PROCESSED_DIR / "qualifying_results.parquet"
RACES_CLEAN_PATH = PROCESSED_DIR / "races.parquet"
QUALIFYING_CLEAN_PATH = PROCESSED_DIR / "qualifying.parquet"
DRIVERS_PATH = PROCESSED_DIR / "drivers.parquet"
CONSTRUCTORS_PATH = PROCESSED_DIR / "constructors.parquet"
MODELING_TABLE_PATH = PROCESSED_DIR / "modeling_table.parquet"
FEATURES_PATH = PROCESSED_DIR / "features.parquet"
PREDICTIONS_PATH = PROCESSED_DIR / "latest_predictions.parquet"
MODEL_BUNDLE_PATH = MODEL_DIR / "baseline_model.joblib"
METRICS_PATH = METRICS_DIR / "train_metrics.json"
MODEL_METADATA_PATH = MODEL_DIR / "model_metadata.json"
DATASET_METADATA_PATH = PROCESSED_DIR / "dataset_metadata.json"
CALIBRATION_REPORT_PATH = METRICS_DIR / "podium_calibration.csv"
BACKTEST_PREDICTIONS_PATH = METRICS_DIR / "backtest_predictions.parquet"
BACKTEST_METRICS_PATH = METRICS_DIR / "backtest_metrics.csv"

DEMO_SCHEDULE_PATH = DEMO_PROCESSED_DIR / "schedule.parquet"
DEMO_RACES_CLEAN_PATH = DEMO_PROCESSED_DIR / "races.parquet"
DEMO_QUALIFYING_CLEAN_PATH = DEMO_PROCESSED_DIR / "qualifying.parquet"
DEMO_PREDICTIONS_PATH = DEMO_PROCESSED_DIR / "latest_predictions.parquet"
DEMO_MODEL_BUNDLE_PATH = DEMO_MODEL_DIR / "baseline_model.joblib"
DEMO_MODEL_METADATA_PATH = DEMO_MODEL_DIR / "model_metadata.json"
DEMO_DATASET_METADATA_PATH = DEMO_PROCESSED_DIR / "dataset_metadata.json"
DEMO_CALIBRATION_REPORT_PATH = DEMO_METRICS_DIR / "podium_calibration.csv"
DEMO_BACKTEST_METRICS_PATH = DEMO_METRICS_DIR / "backtest_metrics.csv"


def readable_path(primary: Path, fallback: Path) -> Path:
    if os.getenv("F1_PREDICTOR_USE_DEMO_DATA") == "1":
        return fallback
    return primary if primary.exists() else fallback


def ensure_directories() -> None:
    for path in (DATA_DIR, CACHE_DIR, RAW_DIR, PROCESSED_DIR, MODEL_DIR, METRICS_DIR):
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError:
            # Serverless deployments such as Vercel expose the application
            # bundle as read-only. In that mode the API reads packaged demo
            # artifacts from src/f1_predictor/demo_data instead of writing
            # generated pipeline outputs under data/.
            continue
