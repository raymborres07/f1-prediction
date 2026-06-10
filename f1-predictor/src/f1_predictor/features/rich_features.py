from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime

import numpy as np
import pandas as pd

from f1_predictor.settings import (
    EVENTS_TABLE_PATH,
    GRID_ENTRIES_TABLE_PATH,
    LAP_TIMES_TABLE_PATH,
    PIT_STOPS_TABLE_PATH,
    PRE_RACE_FEATURES_TABLE_PATH,
    RACE_SIM_INPUTS_TABLE_PATH,
    RICH_DATASET_METADATA_PATH,
    RICH_PROCESSED_DIR,
    RICH_QUALIFYING_TABLE_PATH,
    RICH_RACE_RESULTS_TABLE_PATH,
    SESSION_CONDITIONS_TABLE_PATH,
    STINT_SUMMARIES_TABLE_PATH,
    TELEMETRY_AGGREGATES_TABLE_PATH,
    TYRE_USAGE_TABLE_PATH,
    ensure_directories,
)


PRE_RACE_FEATURE_COLUMNS = [
    "grid_position",
    "qualifying_position",
    "qualifying_gap_to_pole",
    "driver_last3_avg_finish",
    "driver_last5_avg_finish",
    "driver_last5_points",
    "driver_last5_dnf_rate",
    "constructor_last5_avg_finish",
    "constructor_last5_points",
    "constructor_last5_dnf_rate",
    "circuit_avg_finish",
    "circuit_points_rate",
    "teammate_quali_delta",
    "avg_lap_time_last3",
    "long_run_pace_last3",
    "pit_loss_last3",
    "weather_air_temp",
    "weather_track_temp",
    "weather_rainfall",
    "telemetry_speed_mean",
    "telemetry_throttle_mean",
    "telemetry_brake_mean",
]


def _read(path) -> pd.DataFrame:
    return pd.read_parquet(path) if path.exists() else pd.DataFrame()


def _race_keys(df: pd.DataFrame) -> pd.Series:
    return df[["season", "round"]].apply(tuple, axis=1)


def _prior(df: pd.DataFrame, season: int, round_number: int) -> pd.DataFrame:
    if df.empty:
        return df
    return df[(df["season"] < season) | ((df["season"] == season) & (df["round"] < round_number))]


def _driver_constructor_roster(race_results: pd.DataFrame, qualifying: pd.DataFrame) -> pd.DataFrame:
    race_cols = ["season", "round", "driver_number", "driver_code", "driver_name", "constructor_name"]
    race = race_results[[column for column in race_cols if column in race_results.columns]].copy()
    quali = qualifying[[column for column in race_cols if column in qualifying.columns]].copy()
    roster = pd.concat([race, quali], ignore_index=True, sort=False).drop_duplicates()
    return roster.sort_values(["season", "round", "driver_number"])


def _qualifying_frame(qualifying: pd.DataFrame, grid: pd.DataFrame) -> pd.DataFrame:
    if qualifying.empty and grid.empty:
        return pd.DataFrame()
    pieces = []
    if not qualifying.empty:
        q = qualifying.copy()
        q["qualifying_position"] = pd.to_numeric(q.get("qualifying_position"), errors="coerce")
        if "best_qualifying_seconds" in q:
            q["qualifying_gap_to_pole"] = q.groupby(["season", "round"])["best_qualifying_seconds"].transform(lambda s: s - s.min())
        pieces.append(q[["season", "round", "driver_number", "qualifying_position", "qualifying_gap_to_pole", "constructor_name"]])
    if not grid.empty:
        g = grid.rename(columns={"position": "grid_position", "driver_number": "driver_number"}).copy()
        for column in ("season", "meeting_key"):
            if column not in g.columns:
                g[column] = pd.NA
        if {"season", "driver_number"}.issubset(g.columns):
            keep = [column for column in ("season", "driver_number", "grid_position") if column in g.columns]
            pieces.append(g[keep])
    out = pieces[0]
    for piece in pieces[1:]:
        keys = [column for column in ("season", "round", "driver_number") if column in out.columns and column in piece.columns]
        if keys:
            out = out.merge(piece, on=keys, how="outer")
    return out


def _teammate_quali(qualifying: pd.DataFrame) -> pd.DataFrame:
    if qualifying.empty or "best_qualifying_seconds" not in qualifying.columns:
        return pd.DataFrame(columns=["season", "round", "driver_number", "teammate_quali_delta"])
    rows = []
    for _, group in qualifying.groupby(["season", "round", "constructor_name"], dropna=False):
        for _, row in group.iterrows():
            teammate = group[group["driver_number"] != row["driver_number"]]["best_qualifying_seconds"].dropna()
            delta = np.nan
            if pd.notna(row.get("best_qualifying_seconds")) and not teammate.empty:
                delta = row["best_qualifying_seconds"] - teammate.min()
            rows.append(
                {
                    "season": row["season"],
                    "round": row["round"],
                    "driver_number": row["driver_number"],
                    "teammate_quali_delta": delta,
                }
            )
    return pd.DataFrame(rows)


def _lap_pace_prior(laps: pd.DataFrame, season: int, round_number: int, driver_number: float) -> dict[str, float]:
    if laps.empty or "lap_time_seconds" not in laps.columns:
        return {"avg_lap_time_last3": np.nan, "long_run_pace_last3": np.nan}
    prior = _prior(laps, season, round_number)
    driver = prior[prior["driver_number"] == driver_number]
    recent_keys = driver[["season", "round"]].drop_duplicates().tail(3)
    if recent_keys.empty:
        return {"avg_lap_time_last3": np.nan, "long_run_pace_last3": np.nan}
    recent = driver[_race_keys(driver).isin(set(map(tuple, recent_keys.to_numpy())))]
    clean = recent[pd.to_numeric(recent["lap_time_seconds"], errors="coerce").notna()]
    long_run = clean.groupby(["season", "round", "stint_number"], dropna=False).filter(lambda group: len(group) >= 5)
    return {
        "avg_lap_time_last3": clean["lap_time_seconds"].mean(),
        "long_run_pace_last3": long_run["lap_time_seconds"].mean(),
    }


def _pit_prior(pit_stops: pd.DataFrame, season: int, round_number: int, driver_number: float) -> float:
    if pit_stops.empty:
        return np.nan
    prior = _prior(pit_stops, season, round_number)
    driver = prior[prior["driver_number"] == driver_number]
    if "pit_duration" in driver:
        return pd.to_numeric(driver["pit_duration"], errors="coerce").tail(6).mean()
    return driver.tail(6).shape[0]


def _weather_for_event(conditions: pd.DataFrame, season: int, round_number: int) -> dict[str, float]:
    if conditions.empty:
        return {"weather_air_temp": np.nan, "weather_track_temp": np.nan, "weather_rainfall": np.nan}
    event = conditions[(conditions["season"] == season) & (conditions["round"] == round_number)]
    cols = {column.lower(): column for column in event.columns}
    return {
        "weather_air_temp": pd.to_numeric(event.get(cols.get("airtemp", "AirTemp"), pd.Series(dtype=float)), errors="coerce").mean(),
        "weather_track_temp": pd.to_numeric(event.get(cols.get("tracktemp", "TrackTemp"), pd.Series(dtype=float)), errors="coerce").mean(),
        "weather_rainfall": pd.to_numeric(event.get(cols.get("rainfall", "Rainfall"), pd.Series(dtype=float)), errors="coerce").mean(),
    }


def _telemetry_for_event(telemetry: pd.DataFrame, season: int, driver_number: float) -> dict[str, float]:
    if telemetry.empty:
        return {"telemetry_speed_mean": np.nan, "telemetry_throttle_mean": np.nan, "telemetry_brake_mean": np.nan}
    prior = telemetry[(telemetry["season"] < season) & (telemetry["driver_number"] == driver_number)]
    return {
        "telemetry_speed_mean": pd.to_numeric(prior.get("speed_mean", pd.Series(dtype=float)), errors="coerce").tail(5).mean(),
        "telemetry_throttle_mean": pd.to_numeric(prior.get("throttle_mean", pd.Series(dtype=float)), errors="coerce").tail(5).mean(),
        "telemetry_brake_mean": pd.to_numeric(prior.get("brake_mean", pd.Series(dtype=float)), errors="coerce").tail(5).mean(),
    }


def build_rich_features() -> tuple[pd.DataFrame, pd.DataFrame]:
    ensure_directories()
    events = _read(EVENTS_TABLE_PATH)
    race_results = _read(RICH_RACE_RESULTS_TABLE_PATH)
    qualifying = _read(RICH_QUALIFYING_TABLE_PATH)
    grid = _read(GRID_ENTRIES_TABLE_PATH)
    laps = _read(LAP_TIMES_TABLE_PATH)
    stints = _read(STINT_SUMMARIES_TABLE_PATH)
    tyre = _read(TYRE_USAGE_TABLE_PATH)
    pit_stops = _read(PIT_STOPS_TABLE_PATH)
    conditions = _read(SESSION_CONDITIONS_TABLE_PATH)
    telemetry = _read(TELEMETRY_AGGREGATES_TABLE_PATH)
    if race_results.empty:
        raise FileNotFoundError("Missing rich race_results.parquet. Run f1_predictor.ingest.rich_pipeline first.")

    roster = _driver_constructor_roster(race_results, qualifying)
    q_frame = _qualifying_frame(qualifying, grid)
    teammate = _teammate_quali(qualifying)
    rows: list[dict[str, object]] = []

    history = race_results.sort_values(["season", "round", "finish_position"])
    for _, row in roster.iterrows():
        season = int(row["season"])
        round_number = int(row["round"])
        driver_number = row.get("driver_number")
        prior = _prior(history, season, round_number)
        driver_prior = prior[prior["driver_number"] == driver_number]
        constructor_prior = prior[prior["constructor_name"] == row.get("constructor_name")]
        event = events[(events["season"] == season) & (events["round"] == round_number)]
        circuit = event["location"].iloc[0] if not event.empty and "location" in event else None
        circuit_prior = driver_prior.merge(events[["season", "round", "location"]], on=["season", "round"], how="left")
        circuit_prior = circuit_prior[circuit_prior["location"] == circuit]
        driver_last3 = driver_prior.tail(3)
        driver_last5 = driver_prior.tail(5)
        constructor_last5 = constructor_prior.tail(10)
        base = {
            "season": season,
            "round": round_number,
            "driver_number": driver_number,
            "driver_code": row.get("driver_code"),
            "driver_name": row.get("driver_name"),
            "constructor_name": row.get("constructor_name"),
            "driver_last3_avg_finish": driver_last3["finish_position"].mean(),
            "driver_last5_avg_finish": driver_last5["finish_position"].mean(),
            "driver_last5_points": pd.to_numeric(driver_last5.get("points", pd.Series(dtype=float)), errors="coerce").sum(),
            "driver_last5_dnf_rate": driver_last5["status"].astype(str).str.lower().ne("finished").mean() if "status" in driver_last5 else np.nan,
            "constructor_last5_avg_finish": constructor_last5["finish_position"].mean(),
            "constructor_last5_points": pd.to_numeric(constructor_last5.get("points", pd.Series(dtype=float)), errors="coerce").sum(),
            "constructor_last5_dnf_rate": constructor_last5["status"].astype(str).str.lower().ne("finished").mean() if "status" in constructor_last5 else np.nan,
            "circuit_avg_finish": circuit_prior["finish_position"].tail(5).mean(),
            "circuit_points_rate": (pd.to_numeric(circuit_prior["points"], errors="coerce") > 0).tail(5).mean() if "points" in circuit_prior else np.nan,
        }
        base.update(_lap_pace_prior(laps, season, round_number, driver_number))
        base["pit_loss_last3"] = _pit_prior(pit_stops, season, round_number, driver_number)
        base.update(_weather_for_event(conditions, season, round_number))
        base.update(_telemetry_for_event(telemetry, season, driver_number))
        rows.append(base)

    features = pd.DataFrame(rows)
    for aux in (q_frame, teammate):
        if not aux.empty:
            keys = [column for column in ("season", "round", "driver_number") if column in aux.columns]
            features = features.merge(aux, on=keys, how="left")

    for column in PRE_RACE_FEATURE_COLUMNS:
        if column not in features.columns:
            features[column] = np.nan
        default = features[column].median() if pd.api.types.is_numeric_dtype(features[column]) else 0
        features[column] = pd.to_numeric(features[column], errors="coerce").fillna(0 if pd.isna(default) else default)

    race_targets = race_results[["season", "round", "driver_number", "finish_position", "podium", "top10", "points"]].copy()
    features = features.merge(race_targets, on=["season", "round", "driver_number"], how="left")
    sim_inputs = _build_race_sim_inputs(features, stints, tyre, conditions)

    version = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    RICH_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    features["feature_table_version"] = version
    sim_inputs["feature_table_version"] = version
    features.to_parquet(PRE_RACE_FEATURES_TABLE_PATH, index=False)
    sim_inputs.to_parquet(RACE_SIM_INPUTS_TABLE_PATH, index=False)
    metadata = {}
    if RICH_DATASET_METADATA_PATH.exists():
        metadata = json.loads(RICH_DATASET_METADATA_PATH.read_text(encoding="utf-8"))
    metadata["rich_features"] = {
        "built_at_utc": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "version": version,
        "pre_race_rows": int(len(features)),
        "race_sim_rows": int(len(sim_inputs)),
        "feature_columns": PRE_RACE_FEATURE_COLUMNS,
    }
    RICH_DATASET_METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Wrote {len(features):,} pre-race rows to {PRE_RACE_FEATURES_TABLE_PATH}")
    print(f"Wrote {len(sim_inputs):,} simulation rows to {RACE_SIM_INPUTS_TABLE_PATH}")
    return features, sim_inputs


def _build_race_sim_inputs(
    features: pd.DataFrame,
    stints: pd.DataFrame,
    tyre: pd.DataFrame,
    conditions: pd.DataFrame,
) -> pd.DataFrame:
    sim = features[
        [
            "season",
            "round",
            "driver_number",
            "driver_code",
            "constructor_name",
            "grid_position",
            "avg_lap_time_last3",
            "long_run_pace_last3",
            "pit_loss_last3",
            "weather_air_temp",
            "weather_track_temp",
            "weather_rainfall",
        ]
    ].copy()
    if not stints.empty:
        stint_prior = stints.groupby(["season", "round", "driver_number"], dropna=False).agg(
            expected_stints=("stint_number", "nunique"),
            mean_stint_laps=("stint_laps", "mean"),
        ).reset_index()
        sim = sim.merge(stint_prior, on=["season", "round", "driver_number"], how="left")
    if not tyre.empty:
        tyre_event = tyre.groupby(["season", "round"], dropna=False).agg(
            event_mean_stint_laps=("mean_stint_laps", "mean"),
            event_total_tyre_laps=("total_laps", "sum"),
        ).reset_index()
        sim = sim.merge(tyre_event, on=["season", "round"], how="left")
    for column in sim.columns:
        if column not in {"driver_code", "constructor_name"}:
            converted = pd.to_numeric(sim[column], errors="coerce")
            sim[column] = converted if converted.notna().any() else sim[column]
    return sim


def parse_args() -> argparse.Namespace:
    return argparse.ArgumentParser(description="Build rich leak-aware pre-race and race-simulation feature tables.").parse_args()


def main() -> None:
    parse_args()
    build_rich_features()


if __name__ == "__main__":
    main()
