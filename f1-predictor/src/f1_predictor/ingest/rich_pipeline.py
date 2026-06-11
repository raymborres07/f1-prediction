from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from typing import Iterable

import fastf1
import numpy as np
import pandas as pd

from f1_predictor.ingest.openf1 import OpenF1Client
from f1_predictor.ingest.pipeline import _clean_results, _normalise_schedule
from f1_predictor.settings import (
    CACHE_DIR,
    EVENTS_TABLE_PATH,
    FASTF1_RAW_DIR,
    GRID_ENTRIES_TABLE_PATH,
    LAP_TIMES_TABLE_PATH,
    PIT_STOPS_TABLE_PATH,
    RICH_CONSTRUCTORS_TABLE_PATH,
    RICH_DATASET_METADATA_PATH,
    RICH_DRIVERS_TABLE_PATH,
    RICH_PROCESSED_DIR,
    RICH_QUALIFYING_TABLE_PATH,
    RICH_RACE_RESULTS_TABLE_PATH,
    SEASONS_TABLE_PATH,
    SESSIONS_TABLE_PATH,
    SESSION_CONDITIONS_TABLE_PATH,
    STINT_SUMMARIES_TABLE_PATH,
    TELEMETRY_AGGREGATES_TABLE_PATH,
    TYRE_USAGE_TABLE_PATH,
    WEATHER_CONDITIONS_TABLE_PATH,
    ensure_directories,
)


SESSION_CODES = ["FP1", "FP2", "FP3", "Q", "SQ", "S", "R"]
NUMERIC_IDENTIFIER_COLUMNS = {
    "season",
    "round",
    "driver_number",
    "meeting_key",
    "session_key",
    "lap_number",
    "stint_number",
    "position",
    "grid_position",
    "finish_position",
    "qualifying_position",
    "points",
}


def _seconds(value: object) -> float:
    if pd.isna(value):
        return np.nan
    try:
        return pd.Timedelta(value).total_seconds()
    except (TypeError, ValueError):
        return np.nan


def _parquet_safe(table: pd.DataFrame) -> pd.DataFrame:
    if table.empty:
        return table
    out = table.copy()
    for column in NUMERIC_IDENTIFIER_COLUMNS.intersection(out.columns):
        out[column] = pd.to_numeric(out[column], errors="coerce")
    for column in out.select_dtypes(include=["object"]).columns:
        values = out[column].dropna()
        if values.empty:
            continue
        types = {type(value) for value in values.head(500)}
        if len(types) > 1:
            out[column] = out[column].astype("string")
    return out


def _session_safe(year: int, round_number: int, code: str, load_laps: bool = False, load_weather: bool = False):
    try:
        session = fastf1.get_session(year, round_number, code)
        session.load(laps=load_laps, telemetry=False, weather=load_weather, messages=False)
        return session
    except Exception as exc:
        print(f"Skipping FastF1 {year} R{round_number} {code}: {exc}")
        return None


def _write_raw_fastf1(table: pd.DataFrame, version: str, name: str) -> None:
    if table.empty:
        return
    path = FASTF1_RAW_DIR / version / f"{name}.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    table.to_parquet(path, index=False)


def _fastf1_schedule(years: Iterable[int], version: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    schedules: list[pd.DataFrame] = []
    sessions: list[dict[str, object]] = []
    seasons: list[dict[str, object]] = []
    fastf1.Cache.enable_cache(CACHE_DIR)

    for year in years:
        print(f"FastF1 schedule {year}")
        raw_schedule = fastf1.get_event_schedule(year, include_testing=False)
        schedule = _normalise_schedule(raw_schedule, year)
        schedules.append(schedule)
        seasons.append(
            {
                "season": year,
                "event_count": int(len(schedule)),
                "source": "fastf1",
                "ingested_at_utc": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
            }
        )
        for _, event in raw_schedule.iterrows():
            if str(event.get("EventName", "")).lower().startswith("testing"):
                continue
            for index in range(1, 6):
                name = event.get(f"Session{index}")
                date = event.get(f"Session{index}Date")
                if pd.isna(name) or not name:
                    continue
                sessions.append(
                    {
                        "season": year,
                        "round": int(event["RoundNumber"]),
                        "event_name": event.get("EventName"),
                        "session_name": name,
                        "session_index": index,
                        "session_date": pd.to_datetime(date, errors="coerce", utc=True),
                        "source": "fastf1",
                    }
                )

    events = pd.concat(schedules, ignore_index=True) if schedules else pd.DataFrame()
    if not events.empty:
        events = events.rename(columns={"year": "season"})
        events["event_key"] = events["season"].astype(str) + "-" + events["round"].astype(str).str.zfill(2)
    sessions_df = pd.DataFrame(sessions)
    seasons_df = pd.DataFrame(seasons)
    _write_raw_fastf1(events, version, "event_schedule")
    return seasons_df, events, sessions_df


def _fastf1_results_and_laps(events: pd.DataFrame, version: str, include_laps: bool = True) -> dict[str, pd.DataFrame]:
    race_results: list[pd.DataFrame] = []
    qualifying: list[pd.DataFrame] = []
    practice_results: list[pd.DataFrame] = []
    lap_times: list[pd.DataFrame] = []
    weather: list[pd.DataFrame] = []

    race_dates = pd.to_datetime(events["race_date"], errors="coerce", utc=True).dt.tz_localize(None)
    completed = events[race_dates <= pd.Timestamp.now(tz=UTC).tz_localize(None)]
    for _, event in completed.iterrows():
        year = int(event["season"])
        round_number = int(event["round"])
        for code, sink in (("FP1", practice_results), ("FP2", practice_results), ("FP3", practice_results), ("R", race_results), ("Q", qualifying)):
            session = _session_safe(year, round_number, code, load_laps=include_laps and code in {"FP1", "FP2", "FP3", "R"}, load_weather=True)
            if session is None:
                continue
            results = _clean_results(session.results)
            if not results.empty:
                results.insert(0, "session_name", code)
                results.insert(0, "round", round_number)
                results.insert(0, "season", year)
                sink.append(results)
            if include_laps and code in {"FP1", "FP2", "FP3", "R"}:
                laps_source = getattr(session, "_laps", None)
                if laps_source is None or laps_source.empty:
                    continue
                laps = laps_source.copy()
                laps["season"] = year
                laps["round"] = round_number
                laps["session_name"] = code
                lap_times.append(laps)
            if hasattr(session, "weather_data") and session.weather_data is not None and not session.weather_data.empty:
                w = session.weather_data.copy()
                w["season"] = year
                w["round"] = round_number
                w["session_name"] = code
                weather.append(w)

    race_df = pd.concat(race_results, ignore_index=True) if race_results else pd.DataFrame()
    quali_df = pd.concat(qualifying, ignore_index=True) if qualifying else pd.DataFrame()
    practice_df = pd.concat(practice_results, ignore_index=True) if practice_results else pd.DataFrame()
    laps_df = pd.concat(lap_times, ignore_index=True) if lap_times else pd.DataFrame()
    weather_df = pd.concat(weather, ignore_index=True) if weather else pd.DataFrame()
    _write_raw_fastf1(race_df, version, "race_results")
    _write_raw_fastf1(quali_df, version, "qualifying_results")
    _write_raw_fastf1(practice_df, version, "practice_results")
    _write_raw_fastf1(laps_df, version, "race_laps")
    _write_raw_fastf1(weather_df, version, "weather")
    return {"race_results": race_df, "qualifying": quali_df, "practice": practice_df, "lap_times": laps_df, "weather": weather_df}


def _openf1_tables(years: Iterable[int], include_telemetry: bool, max_sessions: int | None) -> dict[str, pd.DataFrame]:
    client = OpenF1Client()
    frames: dict[str, list[pd.DataFrame]] = {
        "sessions": [],
        "drivers": [],
        "grid_entries": [],
        "session_result": [],
        "laps": [],
        "stints": [],
        "pit": [],
        "weather": [],
        "position": [],
        "intervals": [],
        "telemetry_aggregates": [],
    }
    for year in years:
        if year < 2023:
            continue
        sessions = client.get("sessions", year=year)
        if sessions.empty:
            continue
        sessions["season"] = year
        frames["sessions"].append(sessions)
        target_sessions = sessions.sort_values(["meeting_key", "session_key"])
        if max_sessions is not None:
            target_sessions = target_sessions.head(max_sessions)
        for _, session in target_sessions.iterrows():
            session_key = int(session["session_key"])
            meeting_key = int(session["meeting_key"])
            session_name = str(session.get("session_name", ""))
            print(f"OpenF1 {year} {session_name} session_key={session_key}")
            for endpoint, sink_name in (
                ("drivers", "drivers"),
                ("starting_grid", "grid_entries"),
                ("session_result", "session_result"),
                ("laps", "laps"),
                ("stints", "stints"),
                ("pit", "pit"),
                ("weather", "weather"),
                ("position", "position"),
                ("intervals", "intervals"),
            ):
                df = client.get(endpoint, session_key=session_key)
                if not df.empty:
                    df["season"] = year
                    frames[sink_name].append(df)
            if include_telemetry:
                car = client.get("car_data", session_key=session_key)
                loc = client.get("location", session_key=session_key)
                frames["telemetry_aggregates"].append(_openf1_telemetry_aggregate(car, loc, year, meeting_key, session_key))

    return {name: pd.concat(parts, ignore_index=True) if parts else pd.DataFrame() for name, parts in frames.items()}


def _openf1_telemetry_aggregate(
    car: pd.DataFrame,
    location: pd.DataFrame,
    season: int,
    meeting_key: int,
    session_key: int,
) -> pd.DataFrame:
    pieces: list[pd.DataFrame] = []
    if not car.empty:
        numeric = ["speed", "throttle", "brake", "rpm", "n_gear", "drs"]
        available = [column for column in numeric if column in car.columns]
        if available:
            agg = car.groupby("driver_number")[available].agg(["mean", "max"]).reset_index()
            agg.columns = [
                "driver_number" if column == ("driver_number", "") else f"{column[0]}_{column[1]}"
                for column in agg.columns
            ]
            pieces.append(agg)
    if not location.empty and {"x", "y", "z"}.issubset(location.columns):
        loc = location.sort_values(["driver_number", "date"]).copy()
        loc[["x_prev", "y_prev", "z_prev"]] = loc.groupby("driver_number")[["x", "y", "z"]].shift(1)
        loc["distance_delta"] = np.sqrt(
            (loc["x"] - loc["x_prev"]) ** 2 + (loc["y"] - loc["y_prev"]) ** 2 + (loc["z"] - loc["z_prev"]) ** 2
        )
        loc_agg = loc.groupby("driver_number", as_index=False).agg(
            location_samples=("x", "size"),
            path_distance_approx=("distance_delta", "sum"),
        )
        pieces.append(loc_agg)
    if not pieces:
        return pd.DataFrame()
    out = pieces[0]
    for piece in pieces[1:]:
        out = out.merge(piece, on="driver_number", how="outer")
    out["season"] = season
    out["meeting_key"] = meeting_key
    out["session_key"] = session_key
    out["source"] = "openf1"
    return out


def _infer_openf1_rounds(openf1_sessions: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    if openf1_sessions.empty:
        return openf1_sessions
    sessions = openf1_sessions.copy()
    if "round" in sessions.columns and sessions["round"].notna().any():
        return sessions
    sessions["round"] = pd.NA
    if events.empty or "meeting_key" not in sessions.columns:
        return sessions

    event_lookup = events.copy()
    event_lookup["race_date_sort"] = pd.to_datetime(event_lookup.get("race_date"), errors="coerce", utc=True)
    event_lookup = event_lookup.sort_values(["season", "race_date_sort", "round"])
    for season, season_sessions in sessions.groupby("season", dropna=False):
        season_events = event_lookup[event_lookup["season"] == season]
        if season_events.empty:
            continue
        meeting_order = (
            season_sessions.groupby("meeting_key", dropna=False)
            .agg(
                date_start=("date_start", "min") if "date_start" in season_sessions else ("session_key", "min"),
                meeting_name=("meeting_name", "first") if "meeting_name" in season_sessions else ("session_name", "first"),
                country_name=("country_name", "first") if "country_name" in season_sessions else ("session_name", "first"),
                location=("location", "first") if "location" in season_sessions else ("session_name", "first"),
                circuit_short_name=("circuit_short_name", "first") if "circuit_short_name" in season_sessions else ("session_name", "first"),
            )
            .reset_index()
        )
        meeting_order["date_start_sort"] = pd.to_datetime(meeting_order["date_start"], errors="coerce", utc=True)
        meeting_order = meeting_order.sort_values(["date_start_sort", "meeting_key"])
        for ordinal, meeting in enumerate(meeting_order.itertuples(index=False), start=0):
            text = " ".join(
                str(getattr(meeting, field, "")).lower()
                for field in ("meeting_name", "country_name", "location", "circuit_short_name")
            )
            matched_round = pd.NA
            for _, event in season_events.iterrows():
                candidates = [
                    str(event.get("event_name", "")).lower().replace(" grand prix", ""),
                    str(event.get("country", "")).lower(),
                    str(event.get("location", "")).lower(),
                ]
                if any(candidate and candidate in text for candidate in candidates):
                    matched_round = event["round"]
                    break
            if pd.isna(matched_round) and ordinal < len(season_events):
                matched_round = season_events.iloc[ordinal]["round"]
            sessions.loc[(sessions["season"] == season) & (sessions["meeting_key"] == meeting.meeting_key), "round"] = matched_round
    sessions["round"] = pd.to_numeric(sessions["round"], errors="coerce")
    return sessions


def _attach_openf1_session_context(table: pd.DataFrame, session_context: pd.DataFrame) -> pd.DataFrame:
    if table.empty or session_context.empty or "session_key" not in table.columns:
        return table
    context_cols = [
        column
        for column in ("session_key", "meeting_key", "season", "round", "session_name", "date_start")
        if column in session_context.columns
    ]
    context = session_context[context_cols].drop_duplicates("session_key")
    drop_cols = [column for column in ("meeting_key", "season", "round", "session_name", "date_start") if column in table.columns]
    return table.drop(columns=drop_cols, errors="ignore").merge(context, on="session_key", how="left")


def _attach_openf1_driver_context(table: pd.DataFrame, openf1_drivers: pd.DataFrame) -> pd.DataFrame:
    if table.empty or openf1_drivers.empty or "driver_number" not in table.columns or "driver_number" not in openf1_drivers.columns:
        return table
    drivers = openf1_drivers.rename(
        columns={
            "team_name": "constructor_name",
            "name_acronym": "driver_code",
            "full_name": "driver_name",
        }
    )
    keys = ["driver_number"]
    if "session_key" in table.columns and "session_key" in drivers.columns:
        keys.insert(0, "session_key")
    keep = [
        column
        for column in (*keys, "constructor_name", "driver_code", "driver_name")
        if column in drivers.columns
    ]
    context = drivers[keep].drop_duplicates(keys)
    drop_cols = [column for column in ("constructor_name", "driver_code", "driver_name") if column in table.columns]
    return table.drop(columns=drop_cols, errors="ignore").merge(context, on=keys, how="left")


def _normalise_race_results(race: pd.DataFrame) -> pd.DataFrame:
    if race.empty:
        return race
    df = race.rename(
        columns={
            "DriverNumber": "driver_number",
            "BroadcastName": "driver_name",
            "Abbreviation": "driver_code",
            "DriverId": "driver_id",
            "TeamName": "constructor_name",
            "Position": "finish_position",
            "ClassifiedPosition": "classified_position",
            "GridPosition": "grid_position",
            "Status": "status",
            "Points": "points",
        }
    )
    df["driver_number"] = pd.to_numeric(df["driver_number"], errors="coerce")
    df["finish_position"] = pd.to_numeric(df["finish_position"], errors="coerce")
    df["grid_position"] = pd.to_numeric(df["grid_position"], errors="coerce")
    df["podium"] = (df["finish_position"] <= 3).astype(int)
    df["top10"] = (df["finish_position"] <= 10).astype(int)
    df["source"] = "fastf1"
    return df


def _normalise_qualifying(quali: pd.DataFrame) -> pd.DataFrame:
    if quali.empty:
        return quali
    df = quali.rename(
        columns={
            "DriverNumber": "driver_number",
            "BroadcastName": "driver_name",
            "Abbreviation": "driver_code",
            "DriverId": "driver_id",
            "TeamName": "constructor_name",
            "Position": "qualifying_position",
        }
    )
    for column in ("Q1", "Q2", "Q3", "Time"):
        if column in df:
            df[f"{column.lower()}_seconds"] = df[column].map(_seconds)
    time_cols = [column for column in ("q1_seconds", "q2_seconds", "q3_seconds", "time_seconds") if column in df]
    df["best_qualifying_seconds"] = df[time_cols].min(axis=1) if time_cols else np.nan
    df["source"] = "fastf1"
    return df


def _normalise_laps(laps: pd.DataFrame) -> pd.DataFrame:
    if laps.empty:
        return laps
    df = laps.copy()
    rename = {
        "DriverNumber": "driver_number",
        "Driver": "driver_code",
        "Team": "constructor_name",
        "LapNumber": "lap_number",
        "LapTime": "lap_time",
        "Stint": "stint_number",
        "Compound": "compound",
        "TyreLife": "tyre_life",
        "PitInTime": "pit_in_time",
        "PitOutTime": "pit_out_time",
        "Sector1Time": "sector1_time",
        "Sector2Time": "sector2_time",
        "Sector3Time": "sector3_time",
        "TrackStatus": "track_status",
        "IsAccurate": "is_accurate",
    }
    df = df.rename(columns=rename)
    for column in ("lap_time", "sector1_time", "sector2_time", "sector3_time"):
        if column in df:
            df[f"{column}_seconds"] = df[column].map(_seconds)
    df["driver_number"] = pd.to_numeric(df.get("driver_number", pd.Series(dtype=float)), errors="coerce")
    df["source"] = "fastf1"
    return df


def _stints_from_laps(laps: pd.DataFrame) -> pd.DataFrame:
    if laps.empty:
        return laps
    required = {"season", "round", "driver_number", "driver_code", "stint_number", "compound", "lap_number"}
    if not required.issubset(laps.columns):
        return pd.DataFrame()
    grouped = laps.groupby(["season", "round", "driver_number", "driver_code", "stint_number", "compound"], dropna=False)
    return grouped.agg(
        stint_start_lap=("lap_number", "min"),
        stint_end_lap=("lap_number", "max"),
        stint_laps=("lap_number", "count"),
        mean_lap_time_seconds=("lap_time_seconds", "mean"),
        median_lap_time_seconds=("lap_time_seconds", "median"),
    ).reset_index()


def _pit_stops_from_laps(laps: pd.DataFrame) -> pd.DataFrame:
    if laps.empty or "pit_in_time" not in laps.columns:
        return pd.DataFrame()
    stops = laps[laps["pit_in_time"].notna() | laps["pit_out_time"].notna()].copy()
    if stops.empty:
        return stops
    return stops[["season", "round", "driver_number", "driver_code", "lap_number", "pit_in_time", "pit_out_time", "compound"]]


def _tyre_usage(stints: pd.DataFrame) -> pd.DataFrame:
    if stints.empty:
        return stints
    return stints.groupby(["season", "round", "compound"], dropna=False).agg(
        total_stints=("stint_number", "count"),
        total_laps=("stint_laps", "sum"),
        mean_stint_laps=("stint_laps", "mean"),
    ).reset_index()


def _session_conditions(weather: pd.DataFrame) -> pd.DataFrame:
    if weather.empty:
        return weather
    numeric = [column for column in weather.columns if column not in {"season", "round", "session_name", "Time"}]
    numeric = [column for column in numeric if pd.api.types.is_numeric_dtype(weather[column])]
    return weather.groupby(["season", "round", "session_name"], dropna=False)[numeric].mean().reset_index()


def _merge_driver_constructor(race: pd.DataFrame, quali: pd.DataFrame, openf1_drivers: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    parts = []
    for df in (race, quali):
        columns = [column for column in ("season", "driver_number", "driver_code", "driver_name", "driver_id") if column in df]
        if columns:
            parts.append(df[columns])
    if not openf1_drivers.empty:
        drivers = openf1_drivers.rename(columns={"name_acronym": "driver_code", "full_name": "driver_name"})
        columns = [column for column in ("season", "driver_number", "driver_code", "driver_name", "first_name", "last_name") if column in drivers]
        parts.append(drivers[columns])
    driver_table = pd.concat(parts, ignore_index=True).drop_duplicates() if parts else pd.DataFrame()
    constructor_parts = []
    for df in (race, quali):
        if "constructor_name" in df:
            constructor_parts.append(df[["season", "constructor_name"]])
    if not openf1_drivers.empty and "team_name" in openf1_drivers:
        constructor_parts.append(openf1_drivers.rename(columns={"team_name": "constructor_name"})[["season", "constructor_name"]])
    constructors = pd.concat(constructor_parts, ignore_index=True).dropna().drop_duplicates() if constructor_parts else pd.DataFrame()
    return driver_table, constructors


def build_rich_dataset(
    years: Iterable[int],
    include_openf1: bool = True,
    include_telemetry: bool = False,
    max_openf1_sessions: int | None = None,
) -> dict[str, pd.DataFrame]:
    ensure_directories()
    version = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    years = list(years)
    seasons, events, sessions = _fastf1_schedule(years, version)
    fastf1_tables = _fastf1_results_and_laps(events, version, include_laps=True)
    openf1_tables = _openf1_tables(years, include_telemetry, max_openf1_sessions) if include_openf1 else {}

    race_results = _normalise_race_results(fastf1_tables["race_results"])
    qualifying = _normalise_qualifying(fastf1_tables["qualifying"])
    lap_times = _normalise_laps(fastf1_tables["lap_times"])
    stint_summaries = _stints_from_laps(lap_times)
    pit_stops = _pit_stops_from_laps(lap_times)
    tyre_usage = _tyre_usage(stint_summaries)
    weather = fastf1_tables["weather"]
    session_conditions = _session_conditions(weather)

    if include_openf1:
        openf1_sessions = _infer_openf1_rounds(openf1_tables.get("sessions", pd.DataFrame()), events)
        context_cols = [
            column
            for column in ("session_key", "meeting_key", "season", "round", "session_name", "date_start")
            if column in openf1_sessions.columns
        ]
        session_context = openf1_sessions[context_cols].copy() if context_cols else pd.DataFrame()
        driver_context = openf1_tables.get("drivers", pd.DataFrame())
        sessions = pd.concat([sessions, openf1_sessions], ignore_index=True, sort=False)
        grid_entries = _attach_openf1_driver_context(_attach_openf1_session_context(openf1_tables.get("grid_entries", pd.DataFrame()), session_context), driver_context)
        openf1_laps = _attach_openf1_driver_context(_attach_openf1_session_context(openf1_tables.get("laps", pd.DataFrame()), session_context), driver_context)
        if not openf1_laps.empty:
            openf1_laps["source"] = "openf1"
            lap_times = pd.concat([lap_times, openf1_laps], ignore_index=True, sort=False)
        openf1_stints = _attach_openf1_driver_context(_attach_openf1_session_context(openf1_tables.get("stints", pd.DataFrame()), session_context), driver_context)
        if not openf1_stints.empty:
            stint_summaries = pd.concat([stint_summaries, openf1_stints.assign(source="openf1")], ignore_index=True, sort=False)
        openf1_pit = _attach_openf1_driver_context(_attach_openf1_session_context(openf1_tables.get("pit", pd.DataFrame()), session_context), driver_context)
        if not openf1_pit.empty:
            pit_stops = pd.concat([pit_stops, openf1_pit.assign(source="openf1")], ignore_index=True, sort=False)
        openf1_weather = _attach_openf1_session_context(openf1_tables.get("weather", pd.DataFrame()), session_context)
        if not openf1_weather.empty:
            weather = pd.concat([weather, openf1_weather.assign(source="openf1")], ignore_index=True, sort=False)
        telemetry = _attach_openf1_driver_context(_attach_openf1_session_context(openf1_tables.get("telemetry_aggregates", pd.DataFrame()), session_context), driver_context)
    else:
        grid_entries = pd.DataFrame()
        telemetry = pd.DataFrame()
    session_conditions = _session_conditions(weather)

    drivers, constructors = _merge_driver_constructor(race_results, qualifying, openf1_tables.get("drivers", pd.DataFrame()))
    tables = {
        "seasons": seasons,
        "events": events,
        "sessions": sessions,
        "drivers": drivers,
        "constructors": constructors,
        "grid_entries": grid_entries,
        "qualifying": qualifying,
        "race_results": race_results,
        "lap_times": lap_times,
        "stint_summaries": stint_summaries,
        "tyre_usage": tyre_usage,
        "pit_stops": pit_stops,
        "weather_conditions": weather,
        "session_conditions": session_conditions,
        "telemetry_aggregates": telemetry,
    }
    paths = {
        "seasons": SEASONS_TABLE_PATH,
        "events": EVENTS_TABLE_PATH,
        "sessions": SESSIONS_TABLE_PATH,
        "drivers": RICH_DRIVERS_TABLE_PATH,
        "constructors": RICH_CONSTRUCTORS_TABLE_PATH,
        "grid_entries": GRID_ENTRIES_TABLE_PATH,
        "qualifying": RICH_QUALIFYING_TABLE_PATH,
        "race_results": RICH_RACE_RESULTS_TABLE_PATH,
        "lap_times": LAP_TIMES_TABLE_PATH,
        "stint_summaries": STINT_SUMMARIES_TABLE_PATH,
        "tyre_usage": TYRE_USAGE_TABLE_PATH,
        "pit_stops": PIT_STOPS_TABLE_PATH,
        "weather_conditions": WEATHER_CONDITIONS_TABLE_PATH,
        "session_conditions": SESSION_CONDITIONS_TABLE_PATH,
        "telemetry_aggregates": TELEMETRY_AGGREGATES_TABLE_PATH,
    }
    RICH_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    metadata = {
        "dataset_version": version,
        "built_at_utc": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "years": years,
        "sources": ["fastf1", *([] if not include_openf1 else ["openf1"])],
        "include_telemetry": include_telemetry,
        "tables": {},
        "notes": [
            "OpenF1 historical coverage starts in 2023.",
            "Telemetry aggregates are opt-in to keep raw pulls manageable.",
            "2026 schedules and 22-car grids are represented dynamically; no fixed 20-car assumptions are used.",
        ],
    }
    for name, table in tables.items():
        table = _parquet_safe(table)
        tables[name] = table
        table.to_parquet(paths[name], index=False)
        table.to_parquet(RICH_PROCESSED_DIR / f"{name}_{version}.parquet", index=False)
        metadata["tables"][name] = {"rows": int(len(table)), "path": str(paths[name])}
        print(f"Wrote {len(table):,} rows to {paths[name]}")
    RICH_DATASET_METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Wrote rich metadata to {RICH_DATASET_METADATA_PATH}")
    return tables


def parse_args() -> argparse.Namespace:
    current_year = datetime.now(UTC).year
    parser = argparse.ArgumentParser(description="Build rich normalized FastF1/OpenF1 tables.")
    parser.add_argument("--start-year", type=int, default=max(2023, current_year - 2))
    parser.add_argument("--end-year", type=int, default=current_year)
    parser.add_argument("--no-openf1", action="store_true", help="Skip OpenF1 supplemental historical timing data.")
    parser.add_argument("--include-telemetry", action="store_true", help="Fetch OpenF1 car/location streams and aggregate them.")
    parser.add_argument("--max-openf1-sessions", type=int, help="Limit OpenF1 session pulls for smoke tests.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    build_rich_dataset(
        range(args.start_year, args.end_year + 1),
        include_openf1=not args.no_openf1,
        include_telemetry=args.include_telemetry,
        max_openf1_sessions=args.max_openf1_sessions,
    )


if __name__ == "__main__":
    main()
