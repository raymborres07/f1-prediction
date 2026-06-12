from __future__ import annotations

import argparse
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

from f1_predictor.settings import (
    BACKTEST_METRICS_PATH,
    CALIBRATION_REPORT_PATH,
    DEMO_BACKTEST_METRICS_PATH,
    DEMO_CALIBRATION_REPORT_PATH,
    DEMO_DATA_DIR,
    DEMO_EVENTS_TABLE_PATH,
    DEMO_LAP_TIMES_TABLE_PATH,
    DEMO_PREDICTIONS_PATH,
    DEMO_PRE_RACE_FEATURES_TABLE_PATH,
    DEMO_SESSION_CONDITIONS_TABLE_PATH,
    DEMO_SIMULATION_DISTRIBUTIONS_PATH,
    DEMO_SIMULATION_METADATA_PATH,
    DEMO_SIMULATION_SUMMARY_PATH,
    DEMO_STINT_SUMMARIES_TABLE_PATH,
    DEMO_TYRE_USAGE_TABLE_PATH,
    DEMO_TRAIN_METRICS_PATH,
    EVENTS_TABLE_PATH,
    LAP_TIMES_TABLE_PATH,
    METRICS_PATH,
    PREDICTIONS_PATH,
    PRE_RACE_FEATURES_TABLE_PATH,
    SESSION_CONDITIONS_TABLE_PATH,
    SIMULATION_DISTRIBUTIONS_PATH,
    SIMULATION_METADATA_PATH,
    SIMULATION_SUMMARY_PATH,
    STINT_SUMMARIES_TABLE_PATH,
    TYRE_USAGE_TABLE_PATH,
)


REQUIRED_EXPORTS = {
    PREDICTIONS_PATH: DEMO_PREDICTIONS_PATH,
    SIMULATION_SUMMARY_PATH: DEMO_SIMULATION_SUMMARY_PATH,
    SIMULATION_DISTRIBUTIONS_PATH: DEMO_SIMULATION_DISTRIBUTIONS_PATH,
    SIMULATION_METADATA_PATH: DEMO_SIMULATION_METADATA_PATH,
    EVENTS_TABLE_PATH: DEMO_EVENTS_TABLE_PATH,
    PRE_RACE_FEATURES_TABLE_PATH: DEMO_PRE_RACE_FEATURES_TABLE_PATH,
    LAP_TIMES_TABLE_PATH: DEMO_LAP_TIMES_TABLE_PATH,
    STINT_SUMMARIES_TABLE_PATH: DEMO_STINT_SUMMARIES_TABLE_PATH,
    TYRE_USAGE_TABLE_PATH: DEMO_TYRE_USAGE_TABLE_PATH,
    SESSION_CONDITIONS_TABLE_PATH: DEMO_SESSION_CONDITIONS_TABLE_PATH,
}

OPTIONAL_EXPORTS = {
    CALIBRATION_REPORT_PATH: DEMO_CALIBRATION_REPORT_PATH,
    BACKTEST_METRICS_PATH: DEMO_BACKTEST_METRICS_PATH,
    METRICS_PATH: DEMO_TRAIN_METRICS_PATH,
}


def _copy_file(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    print(f"Copied {source} -> {target}")


def _demo_relative(path: Path) -> str:
    return path.relative_to(DEMO_DATA_DIR).as_posix()


def export_demo_artifacts(allow_missing_optional: bool = True) -> dict[str, object]:
    missing = [str(source) for source in REQUIRED_EXPORTS if not source.exists()]
    if missing:
        raise FileNotFoundError(
            "Missing required demo export artifacts. Run prediction and simulation first: "
            + ", ".join(missing)
        )

    copied: list[str] = []
    for source, target in REQUIRED_EXPORTS.items():
        _copy_file(source, target)
        copied.append(_demo_relative(target))

    skipped: list[str] = []
    for source, target in OPTIONAL_EXPORTS.items():
        if source.exists():
            _copy_file(source, target)
            copied.append(_demo_relative(target))
        elif allow_missing_optional:
            skipped.append(str(source))
        else:
            raise FileNotFoundError(f"Missing optional demo export artifact requested as required: {source}")

    manifest = {
        "exported_at_utc": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "copied": copied,
        "skipped_optional": skipped,
        "notes": [
            "These files are packaged with the app for Vercel/demo fallback mode.",
            "The API reads them when F1_PREDICTOR_USE_DEMO_DATA=1 or local generated artifacts are absent.",
        ],
    }
    manifest_path = DEMO_SIMULATION_METADATA_PATH.parent / "demo_export_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote demo export manifest to {manifest_path}")
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Copy generated prediction/simulation artifacts into packaged demo_data.")
    parser.add_argument(
        "--require-metrics",
        action="store_true",
        help="Fail if optional frontend metric files are missing.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    export_demo_artifacts(allow_missing_optional=not args.require_metrics)


if __name__ == "__main__":
    main()
