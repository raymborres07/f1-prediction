from __future__ import annotations

import argparse
from datetime import UTC, datetime
from typing import Iterable

import fastf1
import pandas as pd

from f1_predictor.settings import (
    CACHE_DIR,
    PROCESSED_DIR,
    QUALIFYING_RESULTS_PATH,
    RACE_RESULTS_PATH,
    SCHEDULE_PATH,
    ensure_directories,
)


RESULT_COLUMNS = [
    "DriverNumber",
    "BroadcastName",
    "Abbreviation",
    "DriverId",
    "TeamName",
    "TeamColor",
    "Position",
    "ClassifiedPosition",
    "GridPosition",
    "Q1",
    "Q2",
    "Q3",
    "Time",
    "Status",
    "Points",
]


def _clean_results(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    cleaned = df.copy()
    for column in RESULT_COLUMNS:
        if column not in cleaned.columns:
            cleaned[column] = pd.NA
    return cleaned[RESULT_COLUMNS]


def _timestamp(value: object) -> pd.Timestamp:
    timestamp = pd.to_datetime(value, errors="coerce")
    if pd.isna(timestamp):
        return pd.NaT
    if getattr(timestamp, "tzinfo", None) is not None:
        return timestamp.tz_convert("UTC").tz_localize(None)
    return timestamp


def _normalise_schedule(schedule: pd.DataFrame, year: int) -> pd.DataFrame:
    rows = []
    for _, row in schedule.iterrows():
        event_format = str(row.get("EventFormat", "conventional"))
        if str(row.get("EventName", "")).lower().startswith("testing"):
            continue
        rows.append(
            {
                "year": year,
                "round": int(row["RoundNumber"]),
                "country": row.get("Country"),
                "location": row.get("Location"),
                "event_name": row.get("EventName"),
                "official_event_name": row.get("OfficialEventName"),
                "event_format": event_format,
                "event_date": _timestamp(row.get("EventDate")),
                "race_date": _timestamp(row.get("Session5Date")),
                "qualifying_date": _timestamp(row.get("Session4Date")),
            }
        )
    return pd.DataFrame(rows)


def _session_results(year: int, round_number: int, session_name: str) -> pd.DataFrame:
    try:
        session = fastf1.get_session(year, round_number, session_name)
        session.load(laps=False, telemetry=False, weather=False, messages=False)
        results = _clean_results(session.results)
    except Exception as exc:
        print(f"Skipping {year} round {round_number} {session_name}: {exc}")
        return pd.DataFrame()

    if results.empty:
        return results

    results.insert(0, "session", session_name)
    results.insert(0, "round", round_number)
    results.insert(0, "year", year)
    return results


def ingest_years(years: Iterable[int]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ensure_directories()
    fastf1.Cache.enable_cache(CACHE_DIR)

    schedule_frames: list[pd.DataFrame] = []
    race_frames: list[pd.DataFrame] = []
    quali_frames: list[pd.DataFrame] = []

    for year in years:
        print(f"Loading schedule for {year}")
        schedule = fastf1.get_event_schedule(year, include_testing=False)
        schedule_df = _normalise_schedule(schedule, year)
        schedule_frames.append(schedule_df)

        completed = schedule_df[
            schedule_df["race_date"].notna() & (schedule_df["race_date"] <= pd.Timestamp.utcnow().tz_localize(None))
        ]
        for round_number in completed["round"].astype(int).tolist():
            print(f"Loading {year} round {round_number}")
            race_frames.append(_session_results(year, round_number, "R"))
            quali_frames.append(_session_results(year, round_number, "Q"))

    schedule_all = pd.concat(schedule_frames, ignore_index=True) if schedule_frames else pd.DataFrame()
    races_all = pd.concat(race_frames, ignore_index=True) if race_frames else pd.DataFrame()
    quali_all = pd.concat(quali_frames, ignore_index=True) if quali_frames else pd.DataFrame()

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    schedule_all.to_parquet(SCHEDULE_PATH, index=False)
    races_all.to_parquet(RACE_RESULTS_PATH, index=False)
    quali_all.to_parquet(QUALIFYING_RESULTS_PATH, index=False)

    print(f"Wrote {len(schedule_all):,} schedule rows to {SCHEDULE_PATH}")
    print(f"Wrote {len(races_all):,} race result rows to {RACE_RESULTS_PATH}")
    print(f"Wrote {len(quali_all):,} qualifying rows to {QUALIFYING_RESULTS_PATH}")
    return schedule_all, races_all, quali_all


def parse_args() -> argparse.Namespace:
    current_year = datetime.now(UTC).year
    parser = argparse.ArgumentParser(description="Download FastF1 schedule, race, and qualifying data.")
    parser.add_argument("--start-year", type=int, default=max(2018, current_year - 4))
    parser.add_argument("--end-year", type=int, default=current_year)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    years = range(args.start_year, args.end_year + 1)
    ingest_years(years)


if __name__ == "__main__":
    main()
