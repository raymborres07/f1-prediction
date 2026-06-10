from __future__ import annotations

import argparse
from datetime import UTC, datetime

import joblib
import numpy as np
import pandas as pd

from f1_predictor.features.pipeline import (
    FEATURE_COLUMNS,
    _fill_feature_defaults,
    _qualifying_features,
    _rolling_prior_features,
    clean_qualifying_results,
    clean_race_results,
)
from f1_predictor.models.train import _positive_probability
from f1_predictor.settings import (
    CACHE_DIR,
    DEMO_MODEL_BUNDLE_PATH,
    DEMO_PREDICTIONS_PATH,
    DEMO_QUALIFYING_CLEAN_PATH,
    DEMO_RACES_CLEAN_PATH,
    DEMO_SCHEDULE_PATH,
    MODEL_BUNDLE_PATH,
    PREDICTIONS_PATH,
    QUALIFYING_CLEAN_PATH,
    QUALIFYING_RESULTS_PATH,
    RACES_CLEAN_PATH,
    RACE_RESULTS_PATH,
    SCHEDULE_PATH,
    ensure_directories,
    readable_path,
)


def next_race(schedule: pd.DataFrame | None = None) -> dict[str, object]:
    ensure_directories()
    if schedule is None:
        schedule_path = readable_path(SCHEDULE_PATH, DEMO_SCHEDULE_PATH)
        if schedule_path.exists():
            schedule = pd.read_parquet(schedule_path)
        else:
            import fastf1

            fastf1.Cache.enable_cache(CACHE_DIR)
            year = datetime.now(UTC).year
            schedule = fastf1.get_event_schedule(year, include_testing=False)
            schedule = schedule.rename(
                columns={
                    "RoundNumber": "round",
                    "EventName": "event_name",
                    "Location": "location",
                    "Session5Date": "race_date",
                    "EventFormat": "event_format",
                }
            )
            schedule["year"] = year

    races = schedule.copy()
    races["race_date"] = pd.to_datetime(races["race_date"], errors="coerce")
    now = pd.Timestamp.utcnow().tz_localize(None)
    future = races[races["race_date"].isna() | (races["race_date"] >= now)].sort_values(["race_date", "year", "round"])
    if future.empty:
        predictions_path = readable_path(PREDICTIONS_PATH, DEMO_PREDICTIONS_PATH)
        if predictions_path.exists():
            predictions = pd.read_parquet(predictions_path)
            if not predictions.empty:
                first_prediction = predictions.iloc[0]
                return {
                    "year": int(first_prediction["year"]),
                    "round": int(first_prediction["round"]),
                    "event_name": first_prediction.get("event_name"),
                    "location": first_prediction.get("location"),
                    "race_date": str(first_prediction.get("race_date")),
                }
        import fastf1

        latest_year = int(races["year"].max())
        fastf1.Cache.enable_cache(CACHE_DIR)
        upcoming = fastf1.get_event_schedule(latest_year + 1, include_testing=False)
        first = upcoming[~upcoming["EventName"].str.lower().str.startswith("testing")].iloc[0]
        return {
            "year": int(latest_year + 1),
            "round": int(first["RoundNumber"]),
            "event_name": first["EventName"],
            "location": first["Location"],
            "race_date": str(first.get("Session5Date")),
        }

    first = future.iloc[0]
    return {
        "year": int(first["year"]),
        "round": int(first["round"]),
        "event_name": first.get("event_name"),
        "location": first.get("location"),
        "race_date": str(first.get("race_date")),
    }


def _load_clean_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    races_path = readable_path(RACES_CLEAN_PATH, DEMO_RACES_CLEAN_PATH)
    qualifying_path = readable_path(QUALIFYING_CLEAN_PATH, DEMO_QUALIFYING_CLEAN_PATH)
    schedule_path = readable_path(SCHEDULE_PATH, DEMO_SCHEDULE_PATH)

    if races_path.exists():
        races = pd.read_parquet(races_path)
    elif RACE_RESULTS_PATH.exists() and SCHEDULE_PATH.exists():
        races = clean_race_results(pd.read_parquet(RACE_RESULTS_PATH), pd.read_parquet(SCHEDULE_PATH))
    else:
        raise FileNotFoundError("Run ingestion and dataset build before prediction.")

    if qualifying_path.exists():
        qualifying = pd.read_parquet(qualifying_path)
    elif QUALIFYING_RESULTS_PATH.exists():
        qualifying = clean_qualifying_results(pd.read_parquet(QUALIFYING_RESULTS_PATH))
    else:
        qualifying = pd.DataFrame()

    schedule = pd.read_parquet(schedule_path) if schedule_path.exists() else pd.DataFrame()
    return schedule, races, qualifying


def _target_schedule_row(schedule: pd.DataFrame, year: int, round_number: int) -> dict[str, object]:
    target_schedule = schedule[(schedule["year"] == year) & (schedule["round"] == round_number)]
    if not target_schedule.empty:
        return target_schedule.iloc[0].to_dict()

    predictions_path = readable_path(PREDICTIONS_PATH, DEMO_PREDICTIONS_PATH)
    if predictions_path.exists():
        predictions = pd.read_parquet(predictions_path)
        matching = predictions[(predictions["year"] == year) & (predictions["round"] == round_number)]
        if not matching.empty:
            first = matching.iloc[0]
            return {
                "event_name": first.get("event_name"),
                "location": first.get("location"),
                "race_date": first.get("race_date"),
            }

    try:
        import fastf1

        fastf1.Cache.enable_cache(CACHE_DIR)
        fetched = fastf1.get_event_schedule(year, include_testing=False)
        fetched = fetched.rename(
            columns={
                "RoundNumber": "round",
                "EventName": "event_name",
                "Location": "location",
                "Session5Date": "race_date",
                "EventFormat": "event_format",
            }
        )
        fetched["year"] = year
        fetched_target = fetched[fetched["round"] == round_number]
        if not fetched_target.empty:
            return fetched_target.iloc[0].to_dict()
    except Exception:
        pass

    return {"event_name": f"Round {round_number}", "location": None, "race_date": pd.NaT}


def build_race_feature_frame(year: int, round_number: int) -> pd.DataFrame:
    schedule, races, qualifying = _load_clean_inputs()
    completed_target = races[(races["year"] == year) & (races["round"] == round_number)]

    if not completed_target.empty:
        starters = completed_target.copy()
    else:
        latest_race = races[["year", "round"]].drop_duplicates().sort_values(["year", "round"]).iloc[-1]
        latest_roster = races[(races["year"] == latest_race["year"]) & (races["round"] == latest_race["round"])]
        race_meta = _target_schedule_row(schedule, year, round_number)
        starters = latest_roster.copy()
        starters["year"] = year
        starters["round"] = round_number
        starters["event_name"] = race_meta.get("event_name")
        starters["location"] = race_meta.get("location")
        starters["race_date"] = race_meta.get("race_date")
        starters["finish_position"] = np.nan
        starters["podium"] = np.nan
        starters["win"] = np.nan
        starters["top10"] = np.nan
        starters["dnf"] = np.nan
        starters["grid_position"] = np.nan

    history_plus_target = pd.concat([races, starters], ignore_index=True).drop_duplicates(
        ["year", "round", "driver_code"], keep="last"
    )
    target = starters[
        [
            "year",
            "round",
            "event_name",
            "location",
            "race_date",
            "driver_id",
            "driver_number",
            "driver_code",
            "driver_name",
            "constructor_name",
            "grid_position",
            "finish_position",
            "podium",
            "win",
            "top10",
            "dnf",
        ]
    ].copy()
    target = target.merge(_rolling_prior_features(history_plus_target), on=["year", "round", "driver_code"], how="left")
    target_quali = qualifying[(qualifying["year"] == year) & (qualifying["round"] == round_number)]
    target = target.merge(_qualifying_features(target_quali), on=["year", "round", "driver_code"], how="left")
    target["grid_position"] = pd.to_numeric(target["grid_position"], errors="coerce").fillna(
        pd.to_numeric(target["qualifying_position"], errors="coerce")
    )
    return _fill_feature_defaults(target, races)


def _explain(row: pd.Series) -> str:
    parts: list[str] = []
    if int(row.get("has_quali_data", 0)) == 1 and pd.notna(row.get("qualifying_position")):
        parts.append(f"qualified P{int(row['qualifying_position'])}")
    else:
        parts.append("pre-qualifying forecast")

    if row.get("constructor_last5_avg_finish", 99) <= 6:
        parts.append("strong constructor form")
    elif row.get("constructor_last5_avg_finish", 0) >= 13:
        parts.append("constructor form is a headwind")

    if row.get("driver_circuit_avg_finish", 99) <= 6:
        parts.append("strong circuit history")
    elif row.get("driver_circuit_avg_finish", 0) >= 13:
        parts.append("limited circuit history")

    if row.get("driver_last3_avg_finish", 99) <= 6:
        parts.append("recent top-end form")
    elif row.get("driver_dnf_rate", 0) >= 0.25:
        parts.append("recent reliability risk")

    return ", ".join(parts[:3])


def _feature_contributions(row: pd.Series) -> list[dict[str, object]]:
    candidates = [
        ("Recent form", 10.5 - float(row.get("driver_last3_avg_finish", 10.5)), "Lower recent average finish is better."),
        ("Constructor form", 10.5 - float(row.get("constructor_last5_avg_finish", 10.5)), "Team has been finishing near the front."),
        ("Circuit history", 10.5 - float(row.get("driver_circuit_avg_finish", 10.5)), "Driver has prior strength at this circuit."),
        ("Qualifying", 10.5 - float(row.get("qualifying_position", 10.5)), "Starting closer to the front improves race outlook."),
        ("Reliability", 0.15 - float(row.get("driver_dnf_rate", 0.15)), "Recent low DNF rate supports the forecast."),
    ]
    ranked = sorted(candidates, key=lambda item: abs(item[1]), reverse=True)
    return [
        {"name": name, "impact": round(score, 2), "description": description}
        for name, score, description in ranked[:3]
    ]


def predict_race(year: int, round_number: int) -> pd.DataFrame:
    ensure_directories()
    model_path = readable_path(MODEL_BUNDLE_PATH, DEMO_MODEL_BUNDLE_PATH)
    if not model_path.exists():
        raise FileNotFoundError(f"Missing model bundle at {MODEL_BUNDLE_PATH}. Run training first.")

    bundle = joblib.load(model_path)
    rows = build_race_feature_frame(year, round_number)
    x = rows[FEATURE_COLUMNS]
    rows["win_probability"] = _positive_probability(bundle["win_model"], x)
    rows["podium_probability"] = _positive_probability(bundle["podium_model"], x)
    rows["top10_probability"] = _positive_probability(bundle["top10_model"], x)
    rows["podium_probability"] = rows[["podium_probability", "win_probability"]].max(axis=1)
    rows["top10_probability"] = rows[["top10_probability", "podium_probability"]].max(axis=1)
    rows["expected_finish"] = bundle["finish_model"].predict(x)
    rows["finish_p20"] = bundle["finish_lower_model"].predict(x)
    rows["finish_p80"] = bundle["finish_upper_model"].predict(x)
    rows["finish_low"] = rows[["finish_p20", "finish_p80"]].min(axis=1).clip(lower=1)
    rows["finish_high"] = rows[["finish_p20", "finish_p80"]].max(axis=1).clip(lower=1)
    rows["data_freshness"] = np.where(rows["has_quali_data"].astype(int) == 1, "qualifying included", "pre-qualifying")
    rows["prediction_mode"] = np.where(rows["has_quali_data"].astype(int) == 1, "post-qualifying", "pre-qualifying")
    rows["model_version"] = bundle.get("model_version")
    rows["trained_at_utc"] = bundle.get("trained_at_utc")
    rows["dataset_version"] = bundle.get("dataset_version")
    rows["explanation"] = rows.apply(_explain, axis=1)
    rows["feature_contributions"] = rows.apply(_feature_contributions, axis=1)
    rows = rows.sort_values(["podium_probability", "expected_finish"], ascending=[False, True])
    rows["prediction_rank"] = range(1, len(rows) + 1)
    try:
        PREDICTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
        rows.to_parquet(PREDICTIONS_PATH, index=False)
    except OSError:
        pass
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Predict a race or the next race.")
    parser.add_argument("--year", type=int)
    parser.add_argument("--round", dest="round_number", type=int)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.year is None or args.round_number is None:
        race = next_race()
        year = int(race["year"])
        round_number = int(race["round"])
    else:
        year = args.year
        round_number = args.round_number
    predictions = predict_race(year, round_number)
    print(predictions[["prediction_rank", "driver_code", "constructor_name", "podium_probability", "expected_finish", "explanation"]])


if __name__ == "__main__":
    main()
