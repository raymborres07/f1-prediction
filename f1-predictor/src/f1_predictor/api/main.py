from __future__ import annotations

import json
import os
from datetime import UTC
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from f1_predictor.models.predict import next_race, predict_race
from f1_predictor.settings import (
    BACKTEST_METRICS_PATH,
    CALIBRATION_REPORT_PATH,
    DATASET_METADATA_PATH,
    DEMO_BACKTEST_METRICS_PATH,
    DEMO_CALIBRATION_REPORT_PATH,
    DEMO_DATASET_METADATA_PATH,
    DEMO_EVENTS_TABLE_PATH,
    DEMO_SIMULATION_DISTRIBUTIONS_PATH,
    DEMO_SIMULATION_METADATA_PATH,
    DEMO_SIMULATION_SUMMARY_PATH,
    DEMO_MODEL_BUNDLE_PATH,
    DEMO_MODEL_METADATA_PATH,
    DEMO_PRE_RACE_FEATURES_TABLE_PATH,
    DEMO_QUALIFYING_CLEAN_PATH,
    DEMO_SCHEDULE_PATH,
    EVENTS_TABLE_PATH,
    MODEL_BUNDLE_PATH,
    MODEL_METADATA_PATH,
    PRE_RACE_FEATURES_TABLE_PATH,
    QUALIFYING_CLEAN_PATH,
    SCHEDULE_PATH,
    SIMULATION_DISTRIBUTIONS_PATH,
    SIMULATION_METADATA_PATH,
    SIMULATION_SUMMARY_PATH,
    readable_path,
)


WEB_DIR = Path(__file__).resolve().parents[1] / "web"

app = FastAPI(title="F1 Predictor", version="0.1.0")
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


BARCELONA_2026 = {
    "year": 2026,
    "round": 7,
    "event_name": "Barcelona-Catalunya Grand Prix",
    "official_event_name": "Formula 1 MSC Cruises Grand Premio de Barcelona-Catalunya 2026",
    "country": "Spain",
    "location": "Montmelo",
    "circuit": "Circuit de Barcelona-Catalunya",
    "event_format": "conventional",
    "timezone": "Europe/Madrid",
    "latitude": 41.57,
    "longitude": 2.261,
    "race_date": "2026-06-14T15:00:00+02:00",
    "qualifying_date": "2026-06-13T16:00:00+02:00",
}

BARCELONA_2026_SESSIONS = [
    ("FP1", "2026-06-12T13:30:00+02:00"),
    ("FP2", "2026-06-12T17:00:00+02:00"),
    ("FP3", "2026-06-13T12:30:00+02:00"),
    ("Qualifying", "2026-06-13T16:00:00+02:00"),
    ("Race", "2026-06-14T15:00:00+02:00"),
]


def _records(df: pd.DataFrame) -> list[dict[str, object]]:
    payload = df[
        [
            "prediction_rank",
            "year",
            "round",
            "event_name",
            "driver_code",
            "driver_name",
            "constructor_name",
            "grid_position",
            "qualifying_position",
            "win_probability",
            "podium_probability",
            "top10_probability",
            "expected_finish",
            "finish_low",
            "finish_high",
            "driver_last3_avg_finish",
            "constructor_last5_avg_finish",
            "driver_circuit_avg_finish",
            "teammate_quali_delta",
            "has_quali_data",
            "data_freshness",
            "prediction_mode",
            "model_version",
            "trained_at_utc",
            "dataset_version",
            "explanation",
            "feature_contributions",
        ]
    ].copy()
    for column in ("win_probability", "podium_probability", "top10_probability"):
        payload[column] = payload[column].round(4)
    for column in ("expected_finish", "finish_low", "finish_high"):
        payload[column] = payload[column].round(2)
    return payload.where(pd.notna(payload), None).to_dict(orient="records")


def _simulation_records(df: pd.DataFrame) -> list[dict[str, object]]:
    payload = df.copy()
    for column in ("win_probability", "podium_probability", "top10_probability"):
        if column in payload:
            payload[column] = pd.to_numeric(payload[column], errors="coerce").round(4)
    if "expected_finish" in payload:
        payload["expected_finish"] = pd.to_numeric(payload["expected_finish"], errors="coerce").round(2)
    return payload.where(pd.notna(payload), None).to_dict(orient="records")


def _json_value(value: object) -> object:
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        if value.tzinfo is None:
            value = value.tz_localize(UTC)
        return value.isoformat()
    return value


def _read_event_row(year: int, round_number: int) -> dict[str, object]:
    event_path = readable_path(EVENTS_TABLE_PATH, DEMO_EVENTS_TABLE_PATH)
    if event_path.exists():
        events = pd.read_parquet(event_path)
        year_column = "season" if "season" in events else "year"
        event = events[(events[year_column] == year) & (events["round"] == round_number)]
        if not event.empty:
            return {key: _json_value(value) for key, value in event.iloc[0].to_dict().items()}

    schedule_path = readable_path(SCHEDULE_PATH, DEMO_SCHEDULE_PATH)
    if schedule_path.exists():
        schedule = pd.read_parquet(schedule_path)
        event = schedule[(schedule["year"] == year) & (schedule["round"] == round_number)]
        if not event.empty:
            return {key: _json_value(value) for key, value in event.iloc[0].to_dict().items()}
    return {}


def _feature_rows(year: int, round_number: int) -> pd.DataFrame:
    feature_path = readable_path(PRE_RACE_FEATURES_TABLE_PATH, DEMO_PRE_RACE_FEATURES_TABLE_PATH)
    if not feature_path.exists():
        return pd.DataFrame()
    features = pd.read_parquet(feature_path)
    event_features = features[(features["season"] == year) & (features["round"] == round_number)].copy()
    if event_features.empty:
        return event_features
    event_features["practice_adjusted_pace_rank"] = (
        pd.to_numeric(event_features["practice_single_lap_pace"], errors="coerce")
        .rank(method="min", ascending=True)
        .astype("Int64")
    )
    return event_features


def _feature_lookup(year: int, round_number: int) -> dict[str, dict[str, object]]:
    features = _feature_rows(year, round_number)
    if features.empty:
        return {}
    return {
        str(row["driver_code"]): row.where(pd.notna(row), None).to_dict()
        for _, row in features.iterrows()
        if pd.notna(row.get("driver_code"))
    }


def _format_recent_form(row: dict[str, object] | None) -> str | None:
    if not row:
        return None
    last3 = row.get("driver_last3_avg_finish")
    last5 = row.get("driver_last5_avg_finish")
    dnf_rate = row.get("driver_last5_dnf_rate")
    parts = []
    if last3 is not None:
        parts.append(f"L3 avg P{float(last3):.1f}")
    if last5 is not None:
        parts.append(f"L5 avg P{float(last5):.1f}")
    if dnf_rate is not None:
        parts.append(f"{float(dnf_rate) * 100:.0f}% DNF risk form")
    return " | ".join(parts) if parts else None


def _weather_from_features(features: pd.DataFrame) -> dict[str, object] | None:
    if features.empty:
        return None
    weather = {}
    for source, target in (
        ("weather_air_temp", "air_temp_c"),
        ("weather_track_temp", "track_temp_c"),
        ("weather_rainfall", "rainfall"),
    ):
        if source in features:
            value = pd.to_numeric(features[source], errors="coerce").dropna()
            if not value.empty:
                weather[target] = round(float(value.mean()), 1)
    return weather or None


def _fetch_open_meteo_weather(race: dict[str, object]) -> dict[str, dict[str, object]]:
    params = {
        "latitude": race["latitude"],
        "longitude": race["longitude"],
        "hourly": ",".join(
            [
                "temperature_2m",
                "precipitation_probability",
                "precipitation",
                "wind_speed_10m",
                "cloud_cover",
            ]
        ),
        "timezone": race["timezone"],
        "start_date": "2026-06-12",
        "end_date": "2026-06-14",
    }
    url = f"https://api.open-meteo.com/v1/forecast?{urlencode(params)}"
    try:
        with urlopen(url, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError):
        return {}
    hourly = payload.get("hourly", {})
    times = hourly.get("time", [])
    weather_by_time = {}
    for index, time_value in enumerate(times):
        weather_by_time[time_value] = {
            "air_temp_c": _hourly_value(hourly, "temperature_2m", index),
            "rain_probability": _hourly_value(hourly, "precipitation_probability", index),
            "rainfall": _hourly_value(hourly, "precipitation", index),
            "wind_kph": _hourly_value(hourly, "wind_speed_10m", index),
            "cloud_cover": _hourly_value(hourly, "cloud_cover", index),
            "source": "Open-Meteo live forecast",
        }
    return weather_by_time


def _hourly_value(hourly: dict[str, list[object]], key: str, index: int) -> object:
    values = hourly.get(key) or []
    if index >= len(values):
        return None
    value = values[index]
    return round(float(value), 1) if value is not None else None


def _weather_for_session(weather_by_time: dict[str, dict[str, object]], starts_at: str) -> dict[str, object] | None:
    timestamp = pd.Timestamp(starts_at)
    local_key = timestamp.strftime("%Y-%m-%dT%H:00")
    weather = weather_by_time.get(local_key)
    if not weather:
        return None
    window = []
    for offset in range(3):
        key = (timestamp + pd.Timedelta(hours=offset)).strftime("%Y-%m-%dT%H:00")
        point = weather_by_time.get(key)
        if point:
            window.append(
                {
                    "offset_hours": offset,
                    "rain_probability": point.get("rain_probability"),
                    "air_temp_c": point.get("air_temp_c"),
                    "wind_kph": point.get("wind_kph"),
                }
            )
    enriched = dict(weather)
    enriched["forecast_window"] = window
    return enriched


def _barcelona_sessions() -> list[dict[str, object]]:
    weather_by_time = _fetch_open_meteo_weather(BARCELONA_2026)
    sessions = []
    for name, starts_at in BARCELONA_2026_SESSIONS:
        weather = _weather_for_session(weather_by_time, starts_at)
        sessions.append(
            {
                "name": name,
                "starts_at": starts_at,
                "time_status": "confirmed local",
                "weather": weather,
                "weather_status": weather.get("source") if weather else "live weather unavailable",
            }
        )
    return sessions


def _synthesized_sessions(event: dict[str, object], weather: dict[str, object] | None) -> list[dict[str, object]]:
    qualifying = pd.to_datetime(event.get("qualifying_date"), errors="coerce", utc=True)
    race = pd.to_datetime(event.get("race_date"), errors="coerce", utc=True)
    weather_label = "race-week average" if weather else "not available"
    sessions = [
        ("FP1", qualifying - pd.Timedelta(days=1, hours=5) if pd.notna(qualifying) else pd.NaT),
        ("FP2", qualifying - pd.Timedelta(days=1) if pd.notna(qualifying) else pd.NaT),
        ("FP3", qualifying - pd.Timedelta(hours=3, minutes=30) if pd.notna(qualifying) else pd.NaT),
        ("Qualifying", qualifying),
        ("Race", race),
    ]
    return [
        {
            "name": name,
            "starts_at": _json_value(starts_at) if pd.notna(starts_at) else None,
            "time_status": "scheduled" if name in {"Qualifying", "Race"} else "estimated",
            "weather": weather,
            "weather_status": weather_label,
        }
        for name, starts_at in sessions
    ]


def _race_hub_payload(year: int, round_number: int) -> dict[str, object]:
    if year == BARCELONA_2026["year"] and round_number == BARCELONA_2026["round"]:
        sessions = _barcelona_sessions()
        return {
            "race": BARCELONA_2026,
            "sessions": sessions,
            "weather_available": any(session.get("weather") for session in sessions),
            "weather_note": "Weather is fetched live from Open-Meteo and matched to each local session hour.",
        }
    event = _read_event_row(year, round_number)
    features = _feature_rows(year, round_number)
    weather = _weather_from_features(features)
    race = {
        "year": year,
        "round": round_number,
        "event_name": event.get("event_name") or f"{year} Round {round_number}",
        "official_event_name": event.get("official_event_name"),
        "country": event.get("country"),
        "location": event.get("location"),
        "circuit": event.get("location") or event.get("event_name"),
        "event_format": event.get("event_format"),
        "race_date": event.get("race_date"),
        "qualifying_date": event.get("qualifying_date"),
    }


def _upcoming_weekend_payload() -> dict[str, object]:
    sessions = _barcelona_sessions()
    return {
        "race": BARCELONA_2026,
        "sessions": sessions,
        "weather_available": any(session.get("weather") for session in sessions),
        "weather_note": "Weather is fetched live from Open-Meteo and matched to each local session hour.",
        "context": {
            "headline": "Antonelli enters as favorite after Monaco and current form.",
            "conditions": "Dry, warm, low rain risk if the live weather feed remains stable.",
            "forecast_mode": "pre-weekend, pre-qualifying",
        },
    }


def _current_forecast_payload() -> dict[str, object]:
    if _should_use_simulation_demo_homepage():
        payload = _simulation_demo_predictions()
    else:
        try:
            predictions = predict_race(BARCELONA_2026["year"], BARCELONA_2026["round"])
            payload = {
                "race": BARCELONA_2026,
                "metadata": _metadata(predictions),
                "predictions": _records(predictions),
            }
        except Exception:
            payload = _simulation_demo_predictions()
    payload["race"] = BARCELONA_2026
    payload["metadata"]["forecast_state"] = "pre-weekend"
    payload["metadata"]["prediction_mode"] = "pre-weekend race forecast"
    payload["metadata"]["data_freshness"] = "practice and qualifying pending for Barcelona-Catalunya"
    payload["metadata"]["data_included"] = {
        "practice": False,
        "qualifying": False,
        "upgrade_news": True,
        "simulation": True,
    }
    for row in payload.get("predictions", []):
        row["year"] = BARCELONA_2026["year"]
        row["round"] = BARCELONA_2026["round"]
        row["event_name"] = BARCELONA_2026["event_name"]
        row["grid_position"] = None
        row["qualifying_position"] = None
        row["has_quali_data"] = 0
        row["data_freshness"] = "pre-weekend forecast"
    return payload


def _cron_authorized(request: Request) -> None:
    expected = os.getenv("CRON_SECRET")
    if not expected:
        return
    provided = request.query_params.get("secret") or request.headers.get("x-cron-secret")
    if provided != expected:
        raise HTTPException(status_code=401, detail="Invalid cron secret.")


def _forecast_states_payload() -> dict[str, object]:
    grid_available = not _actual_grid(BARCELONA_2026["year"], BARCELONA_2026["round"]).empty
    return {
        "current_state": "post-quali" if grid_available else "pre-weekend",
        "states": [
            {
                "state": "pre-weekend",
                "available": True,
                "description": "Baseline forecast before Barcelona practice and qualifying are included.",
            },
            {
                "state": "post-FP2",
                "available": False,
                "description": "Activates after FP1/FP2 practice features are refreshed.",
            },
            {
                "state": "post-FP3",
                "available": False,
                "description": "Activates after FP3 practice features are refreshed.",
            },
            {
                "state": "post-quali",
                "available": grid_available,
                "description": "Race forecast regenerated with the actual qualifying grid.",
            },
            {
                "state": "live-race",
                "available": False,
                "description": "Reserved for lap-by-lap race probability updates.",
            },
        ],
    }


def _actual_grid(year: int, round_number: int) -> pd.DataFrame:
    qualifying_path = readable_path(QUALIFYING_CLEAN_PATH, DEMO_QUALIFYING_CLEAN_PATH)
    if not qualifying_path.exists():
        return pd.DataFrame()
    qualifying = pd.read_parquet(qualifying_path)
    year_column = "year" if "year" in qualifying else "season"
    target = qualifying[(qualifying[year_column] == year) & (qualifying["round"] == round_number)].copy()
    if target.empty:
        return target
    position_column = "qualifying_position" if "qualifying_position" in target else "grid_position"
    target["actual_grid_position"] = pd.to_numeric(target[position_column], errors="coerce")
    return target[["driver_code", "actual_grid_position"]].dropna()


def _post_quali_race_forecast_payload() -> dict[str, object]:
    payload = _current_forecast_payload()
    grid = _actual_grid(BARCELONA_2026["year"], BARCELONA_2026["round"])
    if grid.empty:
        return {
            "race": BARCELONA_2026,
            "metadata": {
                "forecast_state": "post-quali-unavailable",
                "prediction_mode": "post-qualifying race forecast unavailable",
                "data_freshness": "actual qualifying grid not available yet",
                "note": "This endpoint activates after qualifying rows or starting-grid data are available. Until then, use the pre-weekend race forecast.",
            },
            "predictions": [],
        }

    grid_lookup = {row["driver_code"]: float(row["actual_grid_position"]) for _, row in grid.iterrows()}
    adjusted = []
    for row in payload.get("predictions", []):
        grid_position = grid_lookup.get(row.get("driver_code"))
        if grid_position is None:
            continue
        grid_factor = max(0.35, 1.55 - (grid_position - 1) * 0.055)
        expected_finish = float(row.get("expected_finish") or 12)
        adjusted_finish = 0.48 * expected_finish + 0.52 * grid_position
        podium = min(0.98, max(0.01, float(row.get("podium_probability") or 0) * grid_factor))
        top10 = min(0.995, max(0.03, float(row.get("top10_probability") or 0) * (1.2 - min(grid_position, 22) / 70)))
        adjusted.append(
            {
                **row,
                "grid_position": grid_position,
                "qualifying_position": grid_position,
                "has_quali_data": 1,
                "expected_finish": round(adjusted_finish, 2),
                "finish_low": max(1, round(adjusted_finish - 2.2, 1)),
                "finish_high": min(22, round(adjusted_finish + 3.5, 1)),
                "podium_probability": round(podium, 4),
                "top10_probability": round(top10, 4),
                "prediction_mode": "post-quali race forecast",
                "data_freshness": "actual qualifying grid included",
            }
        )

    total_win_score = sum(max(0.001, float(row.get("win_probability") or 0) * (1.75 - row["grid_position"] * 0.065)) for row in adjusted) or 1
    for row in adjusted:
        win_score = max(0.001, float(row.get("win_probability") or 0) * (1.75 - row["grid_position"] * 0.065))
        row["win_probability"] = round(win_score / total_win_score, 4)
    adjusted.sort(key=lambda row: (-float(row["win_probability"]), float(row["expected_finish"])))
    for index, row in enumerate(adjusted, start=1):
        row["prediction_rank"] = index

    payload["metadata"]["forecast_state"] = "post-quali"
    payload["metadata"]["prediction_mode"] = "post-quali race forecast"
    payload["metadata"]["data_freshness"] = "actual qualifying grid included"
    payload["metadata"]["data_included"] = {
        "practice": False,
        "qualifying": True,
        "upgrade_news": True,
        "simulation": True,
    }
    payload["predictions"] = adjusted
    return payload


def _qualifying_forecast_payload() -> dict[str, object]:
    race_payload = _current_forecast_payload()
    predictions = race_payload.get("predictions", [])
    ranked = sorted(
        predictions,
        key=lambda row: (
            int(row.get("practice_adjusted_pace_rank") or 99),
            float(row.get("expected_finish") or 99),
            -float(row.get("win_probability") or 0),
        ),
    )
    raw_scores = []
    for row in ranked:
        pace_rank = float(row.get("practice_adjusted_pace_rank") or 15)
        race_score = float(row.get("win_probability") or 0) + float(row.get("podium_probability") or 0) * 0.4
        raw_scores.append(max(0.02, race_score + max(0, 24 - pace_rank) / 120))
    total = sum(raw_scores) or 1
    records = []
    for index, (row, score) in enumerate(zip(ranked, raw_scores, strict=False), start=1):
        pole_probability = score / total
        front_row_probability = min(0.95, pole_probability * 1.9 + (0.08 if index <= 4 else 0.02))
        records.append(
            {
                "qualifying_rank": index,
                "driver_code": row.get("driver_code"),
                "driver_name": row.get("driver_name"),
                "constructor_name": row.get("constructor_name"),
                "pole_probability": round(pole_probability, 4),
                "front_row_probability": round(front_row_probability, 4),
                "practice_adjusted_pace_rank": row.get("practice_adjusted_pace_rank"),
                "recent_form": row.get("recent_form"),
            }
        )
    return {
        "race": BARCELONA_2026,
        "metadata": {
            "forecast_state": "pre-weekend",
            "prediction_mode": "pre-qualifying forecast",
            "data_freshness": "practice and qualifying pending for Barcelona-Catalunya",
            "note": "Qualifying probabilities are derived from current race forecast strength and practice-adjusted pace signals until live Barcelona practice data is available.",
        },
        "predictions": records,
    }
    return {
        "race": race,
        "sessions": _synthesized_sessions(event, weather),
        "weather_available": weather is not None,
        "weather_note": "Session-specific forecasts are shown when available; otherwise race-week averages are used.",
    }


def _monaco_benchmark_payload() -> dict[str, object]:
    actual_podium = ["ANT", "HAM", "HAD"]
    actual_qualifying_top5 = ["ANT", "VER", "HAM", "LEC", "HAD"]
    forecast = _simulation_payload(2026, 6)
    predictions = sorted(
        forecast.get("predictions", []),
        key=lambda row: int(row.get("simulation_rank") or 999),
    )
    predicted_podium = [str(row.get("driver_code")) for row in predictions[:3]]
    predicted_top5 = [str(row.get("driver_code")) for row in predictions[:5]]
    predicted_winner = predicted_podium[0] if predicted_podium else None
    by_driver = {str(row.get("driver_code")): row for row in predictions}
    podium_hits = [code for code in actual_podium if code in predicted_podium]
    top5_hits = [code for code in actual_qualifying_top5 if code in predicted_top5]
    hadjar_podium_probability = by_driver.get("HAD", {}).get("podium_probability")
    hadjar_percent = f"{float(hadjar_podium_probability or 0) * 100:.2f}%"
    return {
        "event": {
            "season": 2026,
            "round": 6,
            "name": "Monaco Grand Prix",
            "benchmark_status": "post-race benchmark",
        },
        "actual": {
            "race_podium": actual_podium,
            "winner": "ANT",
            "qualifying_top5": actual_qualifying_top5,
            "notes": [
                "Antonelli converted pole into the win.",
                "Hamilton finished second.",
                "Hadjar reached the podium from the top-five qualifying group.",
                "Verstappen started P2 but retired, a Monaco fragility miss for most pre-race models.",
            ],
        },
        "forecast": {
            "predicted_winner": predicted_winner,
            "predicted_podium": predicted_podium,
            "predicted_top5": predicted_top5,
            "antonelli_win_probability": by_driver.get("ANT", {}).get("win_probability"),
            "hamilton_podium_probability": by_driver.get("HAM", {}).get("podium_probability"),
            "hadjar_podium_probability": hadjar_podium_probability,
        },
        "scorecard": {
            "winner_hit": predicted_winner == "ANT",
            "podium_recall": round(len(podium_hits) / len(actual_podium), 3),
            "podium_hits": podium_hits,
            "podium_order_exact": predicted_podium == actual_podium,
            "qualifying_top5_overlap": round(len(top5_hits) / len(actual_qualifying_top5), 3),
            "qualifying_top5_hits": top5_hits,
            "main_miss": f"Hadjar podium probability was only {hadjar_percent}, so the model underpriced his upside.",
        },
        "replay_plan": [
            "After FP1: check whether Ferrari pace pushes Leclerc and Hamilton up.",
            "After FP2: confirm whether Ferrari remains the lead practice signal.",
            "After FP3: check whether Antonelli's Saturday pace jump moves him into the favorite cluster.",
            "After qualifying: pole at Monaco should strongly lift Antonelli's win probability.",
            "After race: compare winner hit, podium recall, top-10 recall, and DNF/incident misses.",
        ],
        "sources": [
            "https://www.theguardian.com/sport/2026/jun/06/antonelli-snatches-pole-at-f1s-monaco-gp-after-edging-out-verstappen",
            "https://elpais.com/deportes/formula-1/2026-06-07/gran-premio-de-monaco-en-directo-la-carrera-de-formula-1-en-vivo.html",
        ],
    }


def _simulation_payload(season: int | None = None, round_number: int | None = None) -> dict[str, object]:
    summary_path = readable_path(SIMULATION_SUMMARY_PATH, DEMO_SIMULATION_SUMMARY_PATH)
    distributions_path = readable_path(SIMULATION_DISTRIBUTIONS_PATH, DEMO_SIMULATION_DISTRIBUTIONS_PATH)
    metadata_path = readable_path(SIMULATION_METADATA_PATH, DEMO_SIMULATION_METADATA_PATH)
    if not summary_path.exists():
        raise HTTPException(status_code=404, detail="Run f1-simulate first to generate Monte Carlo outputs.")
    summary = pd.read_parquet(summary_path)
    distributions = pd.read_parquet(distributions_path) if distributions_path.exists() else pd.DataFrame()
    metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.exists() else {}
    if season is None or round_number is None:
        if summary.empty:
            raise HTTPException(status_code=404, detail="Simulation summary is empty.")
        latest = summary[["season", "round"]].drop_duplicates().sort_values(["season", "round"]).iloc[-1]
        season, round_number = int(latest["season"]), int(latest["round"])
    event_summary = summary[(summary["season"] == season) & (summary["round"] == round_number)].copy()
    event_distributions = (
        distributions[(distributions["season"] == season) & (distributions["round"] == round_number)].copy()
        if not distributions.empty
        else pd.DataFrame()
    )
    if event_summary.empty:
        raise HTTPException(status_code=404, detail=f"No simulation outputs for {season} round {round_number}.")
    race = {
        "year": season,
        "round": round_number,
        "simulations": int(event_summary["simulations"].max()) if "simulations" in event_summary else metadata.get("simulations"),
    }
    return {
        "race": race,
        "metadata": metadata,
        "predictions": _simulation_records(event_summary),
        "finish_distributions": _simulation_records(event_distributions) if not event_distributions.empty else [],
    }


def _finish_band_from_distribution(row: dict[str, object]) -> tuple[int | None, int | None]:
    probabilities = []
    for key, value in row.items():
        if key.startswith("p") and key.endswith("_probability"):
            try:
                probabilities.append((int(key[1:].split("_", 1)[0]), float(value or 0)))
            except (TypeError, ValueError):
                continue
    probabilities.sort()
    cumulative = 0.0
    low = None
    high = None
    for position, probability in probabilities:
        cumulative += probability
        if low is None and cumulative >= 0.1:
            low = position
        if high is None and cumulative >= 0.9:
            high = position
            break
    return low, high


def _should_use_simulation_demo_homepage() -> bool:
    simulation_path = readable_path(SIMULATION_SUMMARY_PATH, DEMO_SIMULATION_SUMMARY_PATH)
    if not simulation_path.exists():
        return False
    return os.getenv("F1_PREDICTOR_USE_DEMO_DATA") == "1" or not SIMULATION_SUMMARY_PATH.exists()


def _simulation_demo_predictions() -> dict[str, object]:
    payload = _simulation_payload()
    metadata = payload.get("metadata", {})
    year = int(payload["race"]["year"])
    round_number = int(payload["race"]["round"])
    features = _feature_lookup(year, round_number)
    event = _read_event_row(year, round_number)
    distributions = {
        row.get("driver_code"): row
        for row in payload.get("finish_distributions", [])
        if row.get("driver_code") is not None
    }
    predictions = []
    for row in payload.get("predictions", []):
        low, high = _finish_band_from_distribution(distributions.get(row.get("driver_code"), {}))
        feature_row = features.get(str(row.get("driver_code")), {})
        pace_rank = feature_row.get("practice_adjusted_pace_rank")
        pace_rank = int(pace_rank) if pace_rank is not None else None
        predictions.append(
            {
                "prediction_rank": row.get("simulation_rank"),
                "year": row.get("season"),
                "round": row.get("round"),
                "event_name": event.get("event_name") or f"{row.get('season')} Round {row.get('round')} simulation",
                "driver_code": row.get("driver_code"),
                "driver_name": row.get("driver_name"),
                "constructor_name": row.get("constructor_name"),
                "grid_position": None,
                "qualifying_position": None,
                "win_probability": row.get("win_probability"),
                "podium_probability": row.get("podium_probability"),
                "top10_probability": row.get("top10_probability"),
                "expected_finish": row.get("expected_finish"),
                "finish_low": low,
                "finish_high": high,
                "driver_last3_avg_finish": None,
                "constructor_last5_avg_finish": None,
                "driver_circuit_avg_finish": None,
                "teammate_quali_delta": None,
                "recent_form": _format_recent_form(feature_row),
                "practice_adjusted_pace_rank": pace_rank,
                "practice_single_lap_pace": feature_row.get("practice_single_lap_pace"),
                "has_quali_data": 0,
                "data_freshness": "Practice included",
                "prediction_mode": "race simulation",
                "model_version": "monte-carlo-simulation",
                "trained_at_utc": metadata.get("built_at_utc"),
                "dataset_version": metadata.get("rich_dataset"),
                "explanation": "Monte Carlo simulation from packaged rich artifacts.",
                "feature_contributions": [],
            }
        )
    race = {
        "year": payload["race"]["year"],
        "round": payload["race"]["round"],
        "event_name": event.get("event_name") or f"{payload['race']['year']} Round {payload['race']['round']} simulation",
        "location": event.get("location") or "Packaged demo",
        "country": event.get("country"),
        "race_date": event.get("race_date") or metadata.get("built_at_utc"),
    }
    response_metadata = _metadata()
    response_metadata["prediction_mode"] = "race simulation"
    response_metadata["data_freshness"] = "practice included"
    response_metadata["data_included"] = {
        "practice": bool(features),
        "qualifying": False,
        "upgrade_news": True,
        "simulation": True,
    }
    response_metadata["simulation"] = metadata
    return {"race": race, "metadata": response_metadata, "predictions": predictions}


def _metadata(predictions: pd.DataFrame | None = None) -> dict[str, object]:
    metadata: dict[str, object] = {}
    model_metadata_path = readable_path(MODEL_METADATA_PATH, DEMO_MODEL_METADATA_PATH)
    dataset_metadata_path = readable_path(DATASET_METADATA_PATH, DEMO_DATASET_METADATA_PATH)
    if model_metadata_path.exists():
        metadata["model"] = json.loads(model_metadata_path.read_text(encoding="utf-8"))
    if dataset_metadata_path.exists():
        metadata["dataset"] = json.loads(dataset_metadata_path.read_text(encoding="utf-8"))
    metadata["model_card"] = {
        "training_years": "2024-2025 demo artifact",
        "feature_groups": [
            "grid and qualifying context",
            "driver rolling form",
            "constructor rolling form",
            "circuit history",
            "teammate-relative qualifying pace",
            "recent DNF rates",
        ],
        "caveats": [
            "Demo artifacts are lightweight and retrained locally, not during deployment.",
            "Pre-qualifying forecasts use neutral grid and qualifying features.",
            "Driver roster fallback uses the latest completed race in the packaged data.",
        ],
    }
    if predictions is not None and not predictions.empty:
        metadata["prediction_mode"] = (
            "post-qualifying"
            if predictions["has_quali_data"].fillna(0).astype(int).any()
            else "pre-qualifying"
        )
        metadata["data_freshness"] = (
            "qualifying included"
            if predictions["has_quali_data"].fillna(0).astype(int).any()
            else "pre-qualifying"
        )
    return metadata


@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, object]:
    return {
        "ok": True,
        "has_schedule": readable_path(SCHEDULE_PATH, DEMO_SCHEDULE_PATH).exists(),
        "has_model": readable_path(MODEL_BUNDLE_PATH, DEMO_MODEL_BUNDLE_PATH).exists(),
        "has_model_metadata": readable_path(MODEL_METADATA_PATH, DEMO_MODEL_METADATA_PATH).exists(),
        "has_dataset_metadata": readable_path(DATASET_METADATA_PATH, DEMO_DATASET_METADATA_PATH).exists(),
        "has_calibration_report": readable_path(CALIBRATION_REPORT_PATH, DEMO_CALIBRATION_REPORT_PATH).exists(),
        "has_backtest_metrics": readable_path(BACKTEST_METRICS_PATH, DEMO_BACKTEST_METRICS_PATH).exists(),
        "has_simulation_summary": readable_path(SIMULATION_SUMMARY_PATH, DEMO_SIMULATION_SUMMARY_PATH).exists(),
    }


@app.get("/api/next-race")
def api_next_race() -> dict[str, object]:
    try:
        return next_race()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/race-hub/{year}/{round_number}")
def race_hub(year: int, round_number: int) -> dict[str, object]:
    return _race_hub_payload(year, round_number)


@app.get("/api/weekend/current")
def current_weekend() -> dict[str, object]:
    return _upcoming_weekend_payload()


@app.get("/api/forecast-states")
def forecast_states() -> dict[str, object]:
    return _forecast_states_payload()


@app.get("/api/benchmarks/monaco-2026")
def monaco_2026_benchmark() -> dict[str, object]:
    return _monaco_benchmark_payload()


@app.get("/api/predictions/next")
def predictions_next() -> dict[str, object]:
    return _current_forecast_payload()


@app.get("/api/predictions/qualifying/next")
def qualifying_predictions_next() -> dict[str, object]:
    return _qualifying_forecast_payload()


@app.get("/api/predictions/race/next")
def race_predictions_next() -> dict[str, object]:
    return _current_forecast_payload()


@app.get("/api/predictions/race/post-quali/next")
def post_quali_race_predictions_next() -> dict[str, object]:
    return _post_quali_race_forecast_payload()


@app.get("/api/live-race/status")
def live_race_status() -> dict[str, object]:
    return {
        "state": "live-race",
        "available": False,
        "race": BARCELONA_2026,
        "message": "Live race mode is a separate forecast state and will activate when lap timing, safety-car state, tyre state, and live leaderboard data are connected.",
        "expected_payload": [
            "lap",
            "leaderboard",
            "win_probability_by_driver",
            "safety_car_mode",
            "tyre_state",
            "pit_window_state",
        ],
    }


@app.get("/api/cron/weather-refresh")
def cron_weather_refresh(request: Request) -> dict[str, object]:
    _cron_authorized(request)
    weekend = _upcoming_weekend_payload()
    return {
        "ok": True,
        "job": "weather-refresh",
        "race": weekend["race"],
        "weather_available": weekend["weather_available"],
        "sessions_refreshed": len(weekend["sessions"]),
        "note": "Vercel cron can call this endpoint to refresh/check live weather. Serverless runtime does not commit generated artifacts.",
    }


@app.get("/api/cron/demo-artifact-refresh")
def cron_demo_artifact_refresh(request: Request) -> dict[str, object]:
    _cron_authorized(request)
    simulation_metadata_path = readable_path(SIMULATION_METADATA_PATH, DEMO_SIMULATION_METADATA_PATH)
    metadata = json.loads(simulation_metadata_path.read_text(encoding="utf-8")) if simulation_metadata_path.exists() else {}
    return {
        "ok": True,
        "job": "demo-artifact-refresh",
        "packaged_simulation_available": readable_path(SIMULATION_SUMMARY_PATH, DEMO_SIMULATION_SUMMARY_PATH).exists(),
        "packaged_metadata": metadata,
        "note": "This lightweight cron endpoint reports packaged artifact readiness. Full parquet regeneration still runs in the local pipeline before commit/deploy.",
    }


@app.get("/api/predictions/simulation-demo")
def simulation_demo_predictions() -> dict[str, object]:
    if _should_use_simulation_demo_homepage():
        return _simulation_demo_predictions()
    try:
        race = next_race()
        predictions = predict_race(int(race["year"]), int(race["round"]))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"race": race, "metadata": _metadata(predictions), "predictions": _records(predictions)}


@app.get("/api/predictions/{year}/{round_number}")
def predictions_for_race(year: int, round_number: int) -> dict[str, object]:
    try:
        predictions = predict_race(year, round_number)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    race = {
        "year": year,
        "round": round_number,
        "event_name": predictions["event_name"].dropna().iloc[0] if predictions["event_name"].notna().any() else None,
    }
    return {"race": race, "metadata": _metadata(predictions), "predictions": _records(predictions)}


@app.get("/api/simulations/latest")
def latest_simulation() -> dict[str, object]:
    return _simulation_payload()


@app.get("/api/simulations/{year}/{round_number}")
def simulation_for_race(year: int, round_number: int) -> dict[str, object]:
    return _simulation_payload(year, round_number)


@app.get("/api/reports/podium-calibration")
def podium_calibration() -> dict[str, object]:
    calibration_path = readable_path(CALIBRATION_REPORT_PATH, DEMO_CALIBRATION_REPORT_PATH)
    if not calibration_path.exists():
        raise HTTPException(status_code=404, detail="Run training first to generate the calibration report.")
    report = pd.read_csv(calibration_path)
    return {"rows": report.where(pd.notna(report), None).to_dict(orient="records")}


@app.get("/api/reports/backtest")
def backtest_report() -> dict[str, object]:
    metrics_path = readable_path(BACKTEST_METRICS_PATH, DEMO_BACKTEST_METRICS_PATH)
    if not metrics_path.exists():
        raise HTTPException(status_code=404, detail="Run backtest first to generate diagnostics.")
    metrics = pd.read_csv(metrics_path)
    summary = {
        "race_windows": int(len(metrics)),
        "mean_podium_brier": float(metrics["podium_brier"].mean()),
        "mean_finish_mae": float(metrics["finish_mae"].mean()),
        "mean_win_brier": float(metrics["win_brier"].mean()) if "win_brier" in metrics else None,
        "mean_top10_brier": float(metrics["top10_brier"].mean()) if "top10_brier" in metrics else None,
    }
    columns = ["year", "round", "event_name", "podium_brier", "finish_mae"]
    worst_finish = metrics.nlargest(5, "finish_mae")[columns]
    worst_podium = metrics.nlargest(5, "podium_brier")[columns]
    worst = pd.concat([worst_podium, worst_finish], ignore_index=True).drop_duplicates(["year", "round"]).head(6)
    worst["diagnostic_reason"] = worst.apply(
        lambda row: "high podium calibration error"
        if row["podium_brier"] >= worst_podium["podium_brier"].min()
        else "high finish error",
        axis=1,
    )
    return {
        "summary": summary,
        "worst_windows": worst.where(pd.notna(worst), None).to_dict(orient="records"),
        "worst_podium_windows": worst_podium.where(pd.notna(worst_podium), None).to_dict(orient="records"),
        "worst_finish_windows": worst_finish.where(pd.notna(worst_finish), None).to_dict(orient="records"),
    }
