from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime

import numpy as np
import pandas as pd

from f1_predictor.settings import (
    LAP_TIMES_TABLE_PATH,
    PRACTICE_FEATURES_TABLE_PATH,
    RICH_DATASET_METADATA_PATH,
    RICH_PROCESSED_DIR,
    ensure_directories,
)


PRACTICE_SESSIONS = {"FP1", "FP2", "FP3"}
PRACTICE_SESSION_ALIASES = {
    "practice 1": "FP1",
    "practice 2": "FP2",
    "practice 3": "FP3",
    "free practice 1": "FP1",
    "free practice 2": "FP2",
    "free practice 3": "FP3",
    "fp1": "FP1",
    "fp2": "FP2",
    "fp3": "FP3",
}


def _read_laps() -> pd.DataFrame:
    if not LAP_TIMES_TABLE_PATH.exists():
        raise FileNotFoundError("Missing rich lap_times.parquet. Run f1-ingest-rich first.")
    laps = pd.read_parquet(LAP_TIMES_TABLE_PATH)
    if "session_name" not in laps.columns:
        return pd.DataFrame()
    laps = laps.copy()
    laps["session_name"] = laps["session_name"].astype(str).str.lower().map(PRACTICE_SESSION_ALIASES).fillna(laps["session_name"])
    return laps[laps["session_name"].isin(PRACTICE_SESSIONS)].copy()


def _numeric(df: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(df[column], errors="coerce") if column in df.columns else pd.Series(np.nan, index=df.index)


def _numeric_alias(df: pd.DataFrame, *columns: str) -> pd.Series:
    values = pd.Series(np.nan, index=df.index, dtype=float)
    for column in columns:
        if column in df.columns:
            candidate = pd.to_numeric(df[column], errors="coerce")
            values = values.fillna(candidate)
    return values


def _session_driver_features(laps: pd.DataFrame) -> pd.DataFrame:
    if laps.empty:
        return pd.DataFrame()
    rows = []
    for keys, group in laps.groupby(["season", "round", "session_name", "driver_number", "driver_code", "constructor_name"], dropna=False):
        season, round_number, session_name, driver_number, driver_code, constructor_name = keys
        lap_time = _numeric_alias(group, "lap_time_seconds", "lap_duration")
        sector1 = _numeric_alias(group, "sector1_time_seconds", "duration_sector_1")
        sector2 = _numeric_alias(group, "sector2_time_seconds", "duration_sector_2")
        sector3 = _numeric_alias(group, "sector3_time_seconds", "duration_sector_3")
        clean = group[lap_time.notna()].copy()
        clean["lap_time_seconds_numeric"] = lap_time[lap_time.notna()]
        long_runs = clean.groupby("stint_number", dropna=False).filter(lambda stint: len(stint) >= 5)
        rows.append(
            {
                "season": season,
                "round": round_number,
                "session_name": session_name,
                "driver_number": driver_number,
                "driver_code": driver_code,
                "constructor_name": constructor_name,
                "practice_lap_count": int(len(clean)),
                "single_lap_pace": clean["lap_time_seconds_numeric"].quantile(0.15),
                "long_run_pace": long_runs["lap_time_seconds_numeric"].mean(),
                "stint_consistency": clean["lap_time_seconds_numeric"].std(),
                "sector1_best": sector1.min(),
                "sector2_best": sector2.min(),
                "sector3_best": sector3.min(),
                "speed_trap_max": _numeric_alias(group, "SpeedST", "st_speed").max(),
                "speed_i1_max": _numeric_alias(group, "SpeedI1", "i1_speed").max(),
                "speed_i2_max": _numeric_alias(group, "SpeedI2", "i2_speed").max(),
                "published_cutoff": "pre-qualifying",
            }
        )
    return pd.DataFrame(rows)


def _add_relative_features(features: pd.DataFrame) -> pd.DataFrame:
    if features.empty:
        return features
    out = features.copy()
    for column, output in (
        ("single_lap_pace", "teammate_single_lap_delta"),
        ("long_run_pace", "teammate_long_run_delta"),
    ):
        team_best = out.groupby(["season", "round", "session_name", "constructor_name"])[column].transform("min")
        event_best = out.groupby(["season", "round", "session_name"])[column].transform("min")
        out[output] = out[column] - team_best
        out[f"{column}_gap_to_session_best"] = out[column] - event_best
    return out


def build_practice_features() -> pd.DataFrame:
    ensure_directories()
    laps = _read_laps()
    features = _add_relative_features(_session_driver_features(laps))
    if features.empty:
        features = pd.DataFrame(
            columns=[
                "season",
                "round",
                "session_name",
                "driver_number",
                "driver_code",
                "constructor_name",
                "practice_lap_count",
                "single_lap_pace",
                "long_run_pace",
                "stint_consistency",
                "teammate_single_lap_delta",
                "teammate_long_run_delta",
            ]
        )
    RICH_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    features.to_parquet(PRACTICE_FEATURES_TABLE_PATH, index=False)
    metadata = {}
    if RICH_DATASET_METADATA_PATH.exists():
        metadata = json.loads(RICH_DATASET_METADATA_PATH.read_text(encoding="utf-8"))
    metadata["practice_features"] = {
        "built_at_utc": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "rows": int(len(features)),
        "sessions": sorted(PRACTICE_SESSIONS),
        "leakage_guard": "Only FP1/FP2/FP3 rows are used; race and qualifying result columns are excluded.",
    }
    RICH_DATASET_METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Wrote {len(features):,} practice feature rows to {PRACTICE_FEATURES_TABLE_PATH}")
    return features


def parse_args() -> argparse.Namespace:
    return argparse.ArgumentParser(description="Build FP1/FP2/FP3 practice feature table.").parse_args()


def main() -> None:
    parse_args()
    build_practice_features()


if __name__ == "__main__":
    main()
