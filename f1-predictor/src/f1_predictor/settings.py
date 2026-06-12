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
FASTF1_RAW_DIR = RAW_DIR / "fastf1"
OPENF1_RAW_DIR = RAW_DIR / "openf1"
RICH_PROCESSED_DIR = PROCESSED_DIR / "rich"
SIMULATIONS_DIR = RICH_PROCESSED_DIR / "simulations"
DEMO_PROCESSED_DIR = DEMO_DATA_DIR / "processed"
DEMO_RICH_PROCESSED_DIR = DEMO_PROCESSED_DIR / "rich"
DEMO_SIMULATIONS_DIR = DEMO_RICH_PROCESSED_DIR / "simulations"
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

SEASONS_TABLE_PATH = RICH_PROCESSED_DIR / "seasons.parquet"
EVENTS_TABLE_PATH = RICH_PROCESSED_DIR / "events.parquet"
SESSIONS_TABLE_PATH = RICH_PROCESSED_DIR / "sessions.parquet"
RICH_DRIVERS_TABLE_PATH = RICH_PROCESSED_DIR / "drivers.parquet"
RICH_CONSTRUCTORS_TABLE_PATH = RICH_PROCESSED_DIR / "constructors.parquet"
GRID_ENTRIES_TABLE_PATH = RICH_PROCESSED_DIR / "grid_entries.parquet"
RICH_QUALIFYING_TABLE_PATH = RICH_PROCESSED_DIR / "qualifying.parquet"
RICH_RACE_RESULTS_TABLE_PATH = RICH_PROCESSED_DIR / "race_results.parquet"
LAP_TIMES_TABLE_PATH = RICH_PROCESSED_DIR / "lap_times.parquet"
STINT_SUMMARIES_TABLE_PATH = RICH_PROCESSED_DIR / "stint_summaries.parquet"
TYRE_USAGE_TABLE_PATH = RICH_PROCESSED_DIR / "tyre_usage.parquet"
PIT_STOPS_TABLE_PATH = RICH_PROCESSED_DIR / "pit_stops.parquet"
WEATHER_CONDITIONS_TABLE_PATH = RICH_PROCESSED_DIR / "weather_conditions.parquet"
SESSION_CONDITIONS_TABLE_PATH = RICH_PROCESSED_DIR / "session_conditions.parquet"
TELEMETRY_AGGREGATES_TABLE_PATH = RICH_PROCESSED_DIR / "telemetry_aggregates.parquet"
PRE_RACE_FEATURES_TABLE_PATH = RICH_PROCESSED_DIR / "pre_race_features.parquet"
RACE_SIM_INPUTS_TABLE_PATH = RICH_PROCESSED_DIR / "race_sim_inputs.parquet"
PRACTICE_FEATURES_TABLE_PATH = RICH_PROCESSED_DIR / "practice_features.parquet"
UPGRADE_NEWS_TABLE_PATH = RICH_PROCESSED_DIR / "upgrade_news.parquet"
UPGRADE_FEATURES_TABLE_PATH = RICH_PROCESSED_DIR / "upgrade_features.parquet"
SIMULATION_SUMMARY_PATH = SIMULATIONS_DIR / "simulation_summary.parquet"
SIMULATION_DISTRIBUTIONS_PATH = SIMULATIONS_DIR / "finish_distributions.parquet"
SIMULATION_METADATA_PATH = SIMULATIONS_DIR / "simulation_metadata.json"
RICH_DATASET_METADATA_PATH = RICH_PROCESSED_DIR / "dataset_metadata.json"

DEMO_SCHEDULE_PATH = DEMO_PROCESSED_DIR / "schedule.parquet"
DEMO_RACES_CLEAN_PATH = DEMO_PROCESSED_DIR / "races.parquet"
DEMO_QUALIFYING_CLEAN_PATH = DEMO_PROCESSED_DIR / "qualifying.parquet"
DEMO_PREDICTIONS_PATH = DEMO_PROCESSED_DIR / "latest_predictions.parquet"
DEMO_MODEL_BUNDLE_PATH = DEMO_MODEL_DIR / "baseline_model.joblib"
DEMO_MODEL_METADATA_PATH = DEMO_MODEL_DIR / "model_metadata.json"
DEMO_DATASET_METADATA_PATH = DEMO_PROCESSED_DIR / "dataset_metadata.json"
DEMO_CALIBRATION_REPORT_PATH = DEMO_METRICS_DIR / "podium_calibration.csv"
DEMO_BACKTEST_METRICS_PATH = DEMO_METRICS_DIR / "backtest_metrics.csv"
DEMO_TRAIN_METRICS_PATH = DEMO_METRICS_DIR / "train_metrics.json"
DEMO_SIMULATION_SUMMARY_PATH = DEMO_SIMULATIONS_DIR / "simulation_summary.parquet"
DEMO_SIMULATION_DISTRIBUTIONS_PATH = DEMO_SIMULATIONS_DIR / "finish_distributions.parquet"
DEMO_SIMULATION_METADATA_PATH = DEMO_SIMULATIONS_DIR / "simulation_metadata.json"
DEMO_EVENTS_TABLE_PATH = DEMO_RICH_PROCESSED_DIR / "events.parquet"
DEMO_PRE_RACE_FEATURES_TABLE_PATH = DEMO_RICH_PROCESSED_DIR / "pre_race_features.parquet"
DEMO_LAP_TIMES_TABLE_PATH = DEMO_RICH_PROCESSED_DIR / "lap_times.parquet"
DEMO_STINT_SUMMARIES_TABLE_PATH = DEMO_RICH_PROCESSED_DIR / "stint_summaries.parquet"
DEMO_TYRE_USAGE_TABLE_PATH = DEMO_RICH_PROCESSED_DIR / "tyre_usage.parquet"
DEMO_SESSION_CONDITIONS_TABLE_PATH = DEMO_RICH_PROCESSED_DIR / "session_conditions.parquet"


def readable_path(primary: Path, fallback: Path) -> Path:
    if os.getenv("F1_PREDICTOR_USE_DEMO_DATA") == "1":
        return fallback
    return primary if primary.exists() else fallback


def ensure_directories() -> None:
    for path in (
        DATA_DIR,
        CACHE_DIR,
        RAW_DIR,
        FASTF1_RAW_DIR,
        OPENF1_RAW_DIR,
        PROCESSED_DIR,
        RICH_PROCESSED_DIR,
        SIMULATIONS_DIR,
        MODEL_DIR,
        METRICS_DIR,
    ):
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError:
            # Serverless deployments such as Vercel expose the application
            # bundle as read-only. In that mode the API reads packaged demo
            # artifacts from src/f1_predictor/demo_data instead of writing
            # generated pipeline outputs under data/.
            continue
