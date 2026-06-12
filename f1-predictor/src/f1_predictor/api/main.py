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
    DEMO_RACES_CLEAN_PATH,
    DEMO_SCHEDULE_PATH,
    EVENTS_TABLE_PATH,
    MODEL_BUNDLE_PATH,
    MODEL_METADATA_PATH,
    PRE_RACE_FEATURES_TABLE_PATH,
    QUALIFYING_CLEAN_PATH,
    RACES_CLEAN_PATH,
    RICH_QUALIFYING_TABLE_PATH,
    RICH_RACE_RESULTS_TABLE_PATH,
    LAP_TIMES_TABLE_PATH,
    STINT_SUMMARIES_TABLE_PATH,
    SESSION_CONDITIONS_TABLE_PATH,
    TYRE_USAGE_TABLE_PATH,
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
                "weather_code",
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
            "weather_code": _hourly_value(hourly, "weather_code", index),
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
    enriched["weather_risk_score"] = _weather_risk_score(enriched)
    enriched["weather_risk_label"] = _weather_risk_label(enriched["weather_risk_score"])
    enriched["weather_risk_reason"] = _weather_risk_reason(enriched)
    enriched.update(_weather_condition(enriched))
    enriched["risk_score"] = enriched["weather_risk_score"]
    enriched["risk_label"] = enriched["weather_risk_label"]
    return enriched


def _weather_risk_score(weather: dict[str, object]) -> int:
    rain = float(weather.get("rain_probability") or 0)
    wind = float(weather.get("wind_kph") or 0)
    cloud = float(weather.get("cloud_cover") or 0)
    air_temp = float(weather.get("air_temp_c") or 0)
    code = int(float(weather.get("weather_code") or 0))
    rain_component = rain * 0.55
    cloud_component = cloud * 0.18
    wind_component = max(0, wind - 18) * 1.4
    heat_component = max(0, air_temp - 28) * 3.0
    code_component = _weather_code_severity(code)
    return int(round(min(100, rain_component + cloud_component + wind_component + heat_component + code_component)))


def _weather_code_severity(code: int) -> int:
    if code >= 95:
        return 35
    if code >= 80:
        return 25
    if code >= 60:
        return 18
    if code >= 45:
        return 10
    return 0


def _weather_risk_label(score: int) -> str:
    if score >= 60:
        return "high"
    if score >= 30:
        return "medium"
    return "low"


def _weather_risk_reason(weather: dict[str, object]) -> str:
    rain = weather.get("rain_probability")
    wind = weather.get("wind_kph")
    cloud = weather.get("cloud_cover")
    parts = []
    if rain is not None:
        parts.append(f"rain chance {float(rain):.0f}%")
    if wind is not None:
        parts.append(f"wind {float(wind):.0f} kph")
    if cloud is not None:
        parts.append(f"cloud {float(cloud):.0f}%")
    return ", ".join(parts) if parts else "risk inputs unavailable"


def _weather_condition(weather: dict[str, object]) -> dict[str, object]:
    code = int(float(weather.get("weather_code") or 0))
    rain = float(weather.get("rain_probability") or 0)
    rainfall = float(weather.get("rainfall") or 0)
    cloud = float(weather.get("cloud_cover") or 0)
    wind = float(weather.get("wind_kph") or 0)
    if code >= 95:
        label, icon, class_name = "Storm Risk", "⛈️", "weather-storm"
    elif code >= 80 or code >= 60 or rain >= 55 or rainfall >= 1:
        label, icon, class_name = "Wet", "🌧️", "weather-wet"
    elif rain >= 20 or rainfall > 0:
        label, icon, class_name = "Damp Risk", "🌦️", "weather-damp"
    elif code >= 45 or cloud >= 75:
        label, icon, class_name = "Cloudy", "☁️", "weather-cloudy"
    elif code == 0 and cloud <= 25 and wind < 30:
        label, icon, class_name = "Sunny", "☀️", "weather-sunny"
    else:
        label, icon, class_name = "Dry", "🌤️", "weather-dry"
    return {
        "weather_condition": label,
        "weather_icon": icon,
        "weather_class": class_name,
        "weather_condition_reason": f"{label}: rain {rain:.0f}%, cloud {cloud:.0f}%, wind {wind:.0f} kph",
    }


def _barcelona_sessions() -> list[dict[str, object]]:
    weather_by_time = _fetch_open_meteo_weather(BARCELONA_2026)
    sessions = []
    for name, starts_at in BARCELONA_2026_SESSIONS:
        weather = _weather_for_session(weather_by_time, starts_at) or _fallback_session_weather(starts_at)
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


def _fallback_session_weather(starts_at: str) -> dict[str, object]:
    timestamp = pd.Timestamp(starts_at)
    weather = {
        "air_temp_c": 27.0 if timestamp.hour >= 13 else 24.0,
        "rain_probability": 2.0,
        "rainfall": 0.0,
        "wind_kph": 11.0,
        "cloud_cover": 12.0,
        "weather_code": 0.0,
        "source": "Fallback dry-weekend snapshot",
    }
    weather["forecast_window"] = [
        {
            "offset_hours": offset,
            "rain_probability": 2.0,
            "air_temp_c": weather["air_temp_c"],
            "wind_kph": weather["wind_kph"],
        }
        for offset in range(3)
    ]
    weather["weather_risk_score"] = _weather_risk_score(weather)
    weather["weather_risk_label"] = _weather_risk_label(weather["weather_risk_score"])
    weather["weather_risk_reason"] = _weather_risk_reason(weather)
    weather.update(_weather_condition(weather))
    weather["risk_score"] = weather["weather_risk_score"]
    weather["risk_label"] = weather["weather_risk_label"]
    return weather


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
            "weather_note": "Weather is fetched live from Open-Meteo when reachable, with a transparent fallback snapshot for demo uptime.",
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
    sessions = _synthesized_sessions(event, weather)
    return {
        "race": race,
        "sessions": sessions,
        "weather_available": any(session.get("weather") for session in sessions),
        "weather_note": "Weather is estimated from processed feature data when live session weather is unavailable.",
    }


def _upcoming_weekend_payload() -> dict[str, object]:
    sessions = _barcelona_sessions()
    return {
        "race": BARCELONA_2026,
        "sessions": sessions,
        "weather_available": any(session.get("weather") for session in sessions),
        "weather_note": "Weather is fetched live from Open-Meteo when reachable, with a transparent fallback snapshot for demo uptime.",
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
    authorization = request.headers.get("authorization", "")
    authorization_parts = authorization.split(" ", 1)
    bearer = (
        authorization_parts[1].strip()
        if len(authorization_parts) == 2 and authorization_parts[0].lower() == "bearer"
        else None
    )
    provided = bearer or request.headers.get("x-cron-secret") or request.query_params.get("secret")
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

    baseline_lookup = {row.get("driver_code"): row for row in payload.get("predictions", [])}
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
        baseline = baseline_lookup.get(row.get("driver_code"), {})
        row["delta_win_probability"] = round(row["win_probability"] - float(baseline.get("win_probability") or 0), 4)
        row["delta_podium_probability"] = round(
            float(row.get("podium_probability") or 0) - float(baseline.get("podium_probability") or 0),
            4,
        )
        row["delta_top10_probability"] = round(
            float(row.get("top10_probability") or 0) - float(baseline.get("top10_probability") or 0),
            4,
        )
        row["delta_expected_finish"] = round(
            float(row.get("expected_finish") or 0) - float(baseline.get("expected_finish") or 0),
            2,
        )
    adjusted.sort(key=lambda row: (-float(row["win_probability"]), float(row["expected_finish"])))
    for index, row in enumerate(adjusted, start=1):
        baseline = baseline_lookup.get(row.get("driver_code"), {})
        row["prediction_rank"] = index
        baseline_rank = pd.to_numeric(baseline.get("prediction_rank"), errors="coerce")
        row["delta_rank"] = int(index - baseline_rank) if pd.notna(baseline_rank) else None

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


def _read_parquet_if_exists(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path) if path.exists() else pd.DataFrame()


def _history_schedule() -> pd.DataFrame:
    schedule = _read_parquet_if_exists(readable_path(SCHEDULE_PATH, DEMO_SCHEDULE_PATH))
    if schedule.empty:
        events = _read_parquet_if_exists(readable_path(EVENTS_TABLE_PATH, DEMO_EVENTS_TABLE_PATH))
        schedule = events.rename(columns={"season": "year"}).copy() if not events.empty else events
    if "season" in schedule and "year" not in schedule:
        schedule = schedule.rename(columns={"season": "year"})
    return schedule


def _history_races() -> pd.DataFrame:
    rich = _read_parquet_if_exists(RICH_RACE_RESULTS_TABLE_PATH)
    if not rich.empty:
        return rich.rename(columns={"season": "year"}).copy()
    races = _read_parquet_if_exists(readable_path(RACES_CLEAN_PATH, DEMO_RACES_CLEAN_PATH))
    if "season" in races and "year" not in races:
        races = races.rename(columns={"season": "year"})
    return races


def _history_qualifying() -> pd.DataFrame:
    rich = _read_parquet_if_exists(RICH_QUALIFYING_TABLE_PATH)
    if not rich.empty:
        return rich.rename(columns={"season": "year"}).copy()
    qualifying = _read_parquet_if_exists(readable_path(QUALIFYING_CLEAN_PATH, DEMO_QUALIFYING_CLEAN_PATH))
    if "season" in qualifying and "year" not in qualifying:
        qualifying = qualifying.rename(columns={"season": "year"})
    return qualifying


def _history_scope_metadata() -> dict[str, object]:
    return {
        "coverage": {
            "broad_results": "packaged race, qualifying, and schedule tables where available",
            "rich_session_detail": "local rich FastF1/OpenF1 lap, stint, weather, and telemetry tables when generated",
            "deep_modern_detail": "OpenF1-enriched history from 2023 onward when local rich ingest has been run",
        },
        "mode_guidance": {
            "basic": "race results, qualifying, podiums, fastest laps, and season summaries",
            "geek": "lap tables, stints, weather overlays, sector data, and telemetry comparisons where available",
        },
    }


def _history_records(df: pd.DataFrame, limit: int | None = None) -> list[dict[str, object]]:
    if df.empty:
        return []
    payload = df.head(limit).copy() if limit is not None else df.copy()
    payload = payload.map(_history_json_value)
    return payload.where(pd.notna(payload), None).to_dict(orient="records")


def _history_json_value(value: object) -> object:
    if isinstance(value, (list, tuple)):
        return [_history_json_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _history_json_value(item) for key, item in value.items()}
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timedelta):
        return round(value.total_seconds(), 6)
    return _json_value(value)


def _history_event_rows(year: int | None = None) -> pd.DataFrame:
    events = _history_schedule()
    if events.empty:
        return events
    events = events.copy()
    events["year"] = pd.to_numeric(events["year"], errors="coerce").astype("Int64")
    events["round"] = pd.to_numeric(events["round"], errors="coerce").astype("Int64")
    if year is not None:
        events = events[events["year"] == year]
    return events.sort_values(["year", "round"])


def _history_race_rows(year: int, round_number: int | None = None) -> pd.DataFrame:
    races = _history_races()
    if races.empty:
        return races
    races = races.copy()
    races["year"] = pd.to_numeric(races["year"], errors="coerce").astype("Int64")
    races["round"] = pd.to_numeric(races["round"], errors="coerce").astype("Int64")
    races = races[races["year"] == year]
    if round_number is not None:
        races = races[races["round"] == round_number]
    return races


def _history_quali_rows(year: int, round_number: int | None = None) -> pd.DataFrame:
    qualifying = _history_qualifying()
    if qualifying.empty:
        return qualifying
    qualifying = qualifying.copy()
    qualifying["year"] = pd.to_numeric(qualifying["year"], errors="coerce").astype("Int64")
    qualifying["round"] = pd.to_numeric(qualifying["round"], errors="coerce").astype("Int64")
    qualifying = qualifying[qualifying["year"] == year]
    if round_number is not None:
        qualifying = qualifying[qualifying["round"] == round_number]
    return qualifying


def _driver_at_position(rows: pd.DataFrame, position_column: str, position: int) -> str | None:
    if rows.empty or position_column not in rows:
        return None
    frame = rows.copy()
    frame[position_column] = pd.to_numeric(frame[position_column], errors="coerce")
    target = frame[frame[position_column] == position]
    return str(target.iloc[0]["driver_code"]) if not target.empty and pd.notna(target.iloc[0].get("driver_code")) else None


def _sort_by_numeric(df: pd.DataFrame, column: str) -> pd.DataFrame:
    if df.empty or column not in df:
        return df
    frame = df.copy()
    frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame.sort_values(column, na_position="last")


def _history_season_payload() -> dict[str, object]:
    events = _history_event_rows()
    races = _history_races()
    if events.empty:
        return {"seasons": [], "season_cards": [], "metadata": _history_scope_metadata()}
    grouped = events.groupby("year", dropna=True).agg(event_count=("round", "nunique")).reset_index()
    if not races.empty and "driver_code" in races:
        race_counts = races.rename(columns={"season": "year"}).copy()
        race_counts["year"] = pd.to_numeric(race_counts["year"], errors="coerce")
        race_counts = race_counts.groupby("year", dropna=True).agg(result_rows=("driver_code", "count")).reset_index()
        grouped = grouped.merge(race_counts, on="year", how="left")
    season_cards = [_history_season_card(int(row["year"])) for _, row in grouped.sort_values("year", ascending=False).iterrows()]
    return {
        "seasons": _history_records(grouped.sort_values("year", ascending=False)),
        "season_cards": season_cards,
        "metadata": _history_scope_metadata(),
    }


def _history_season_card(year: int) -> dict[str, object]:
    races = _history_race_rows(year)
    qualifying = _history_quali_rows(year)
    if races.empty:
        return {"year": year, "wins_leader": None, "podiums_leader": None, "points_leader": None, "pole_leader": None}
    frame = races.copy()
    frame["finish_position"] = pd.to_numeric(frame.get("finish_position"), errors="coerce")
    points = pd.to_numeric(frame.get("points"), errors="coerce").fillna(0) if "points" in frame else pd.Series(dtype=float)
    frame["points_numeric"] = points
    wins = _leader_record(frame[frame["finish_position"] == 1], "driver_code")
    podiums = _leader_record(frame[frame["finish_position"] <= 3], "driver_code")
    points_leader = _leader_from_sum(frame, "driver_code", "points_numeric")
    pole_leader = None
    if not qualifying.empty:
        q = qualifying.copy()
        q["qualifying_position"] = pd.to_numeric(q.get("qualifying_position"), errors="coerce")
        pole_leader = _leader_record(q[q["qualifying_position"] == 1], "driver_code")
    return {
        "year": year,
        "race_count": int(frame["round"].nunique()) if "round" in frame else int(len(frame)),
        "wins_leader": wins,
        "podiums_leader": podiums,
        "points_leader": points_leader,
        "pole_leader": pole_leader,
    }


def _leader_record(rows: pd.DataFrame, column: str) -> dict[str, object] | None:
    if rows.empty or column not in rows:
        return None
    counts = rows[column].dropna().astype(str).value_counts()
    if counts.empty:
        return None
    return {"code": counts.index[0], "count": int(counts.iloc[0])}


def _leader_from_sum(rows: pd.DataFrame, group_column: str, value_column: str) -> dict[str, object] | None:
    if rows.empty or group_column not in rows or value_column not in rows:
        return None
    sums = rows.groupby(group_column, dropna=True)[value_column].sum().sort_values(ascending=False)
    if sums.empty:
        return None
    return {"code": str(sums.index[0]), "value": round(float(sums.iloc[0]), 2)}


def _history_year_payload(year: int) -> dict[str, object]:
    events = _history_event_rows(year)
    races = _history_race_rows(year)
    qualifying = _history_quali_rows(year)
    rows = []
    for _, event in events.iterrows():
        round_number = int(event["round"])
        race_rows = races[races["round"] == round_number] if not races.empty else pd.DataFrame()
        quali_rows = qualifying[qualifying["round"] == round_number] if not qualifying.empty else pd.DataFrame()
        podium = (
            _sort_by_numeric(race_rows, "finish_position").head(3)["driver_code"].dropna().astype(str).tolist()
            if not race_rows.empty and "finish_position" in race_rows
            else []
        )
        rows.append(
            {
                "year": year,
                "round": round_number,
                "event_name": event.get("event_name"),
                "country": event.get("country"),
                "location": event.get("location"),
                "circuit": event.get("location") or event.get("event_name"),
                "race_date": _json_value(event.get("race_date")),
                "winner": _driver_at_position(race_rows, "finish_position", 1),
                "pole": _driver_at_position(quali_rows, "qualifying_position", 1),
                "podium": podium,
                "result_rows": int(len(race_rows)),
                "qualifying_rows": int(len(quali_rows)),
            }
        )
    return {"year": year, "races": rows, "metadata": _history_scope_metadata()}


def _history_lap_frame(year: int, round_number: int) -> pd.DataFrame:
    laps = _read_parquet_if_exists(LAP_TIMES_TABLE_PATH)
    if laps.empty:
        return laps
    if "season" in laps and "year" not in laps:
        laps = laps.rename(columns={"season": "year"})
    laps["year"] = pd.to_numeric(laps["year"], errors="coerce").astype("Int64")
    laps["round"] = pd.to_numeric(laps["round"], errors="coerce").astype("Int64")
    laps = laps[(laps["year"] == year) & (laps["round"] == round_number)].copy()
    if "lap_time_seconds" not in laps and "lap_time" in laps:
        laps["lap_time_seconds"] = pd.to_timedelta(laps["lap_time"], errors="coerce").dt.total_seconds()
    return laps


def _history_fastest_laps(year: int, round_number: int) -> list[dict[str, object]]:
    laps = _history_lap_frame(year, round_number)
    if laps.empty or "lap_time_seconds" not in laps:
        return []
    frame = laps.dropna(subset=["lap_time_seconds"]).sort_values("lap_time_seconds")
    columns = [column for column in ["driver_code", "lap_number", "lap_time_seconds", "compound", "session_name"] if column in frame]
    return _history_records(frame[columns].head(10))


def _history_summary_payload(year: int, round_number: int) -> dict[str, object]:
    events = _history_event_rows(year)
    event = events[events["round"] == round_number]
    race_rows = _sort_by_numeric(_history_race_rows(year, round_number), "finish_position")
    quali_rows = _sort_by_numeric(_history_quali_rows(year, round_number), "qualifying_position")
    return {
        "event": _history_records(event.head(1))[0] if not event.empty else {"year": year, "round": round_number},
        "podium": _history_records(race_rows.head(3)),
        "race_results": _history_records(race_rows),
        "qualifying_top10": _history_records(quali_rows.head(10)),
        "fastest_laps": _history_fastest_laps(year, round_number),
        "stint_summary": _history_stint_summary(year, round_number),
        "tyre_summary": _history_tyre_summary(year, round_number),
        "weather_summary": _history_weather_summary(year, round_number),
        "metadata": _history_scope_metadata(),
    }


def _history_stint_summary(year: int, round_number: int) -> list[dict[str, object]]:
    stints = _read_parquet_if_exists(STINT_SUMMARIES_TABLE_PATH)
    if stints.empty:
        return []
    if "season" in stints and "year" not in stints:
        stints = stints.rename(columns={"season": "year"})
    stints["year"] = pd.to_numeric(stints["year"], errors="coerce").astype("Int64")
    stints["round"] = pd.to_numeric(stints["round"], errors="coerce").astype("Int64")
    stints = stints[(stints["year"] == year) & (stints["round"] == round_number)].copy()
    if stints.empty:
        return []
    grouped = stints.groupby("driver_code", dropna=True).agg(
        stints=("stint_number", "nunique"),
        total_laps=("stint_laps", "sum"),
        mean_stint_laps=("stint_laps", "mean"),
        mean_lap_time_seconds=("mean_lap_time_seconds", "mean"),
    ).reset_index()
    return _history_records(grouped.sort_values(["stints", "total_laps"], ascending=[False, False]).head(12))


def _history_tyre_summary(year: int, round_number: int) -> list[dict[str, object]]:
    tyre = _read_parquet_if_exists(TYRE_USAGE_TABLE_PATH)
    if tyre.empty:
        return []
    if "season" in tyre and "year" not in tyre:
        tyre = tyre.rename(columns={"season": "year"})
    tyre["year"] = pd.to_numeric(tyre["year"], errors="coerce").astype("Int64")
    tyre["round"] = pd.to_numeric(tyre["round"], errors="coerce").astype("Int64")
    tyre = tyre[(tyre["year"] == year) & (tyre["round"] == round_number)].copy()
    return _history_records(tyre.sort_values("total_laps", ascending=False)) if not tyre.empty else []


def _history_weather_summary(year: int, round_number: int) -> dict[str, object]:
    conditions = _read_parquet_if_exists(SESSION_CONDITIONS_TABLE_PATH)
    if conditions.empty:
        return {}
    if "season" in conditions and "year" not in conditions:
        conditions = conditions.rename(columns={"season": "year"})
    conditions["year"] = pd.to_numeric(conditions["year"], errors="coerce").astype("Int64")
    conditions["round"] = pd.to_numeric(conditions["round"], errors="coerce").astype("Int64")
    conditions = conditions[(conditions["year"] == year) & (conditions["round"] == round_number)].copy()
    if conditions.empty:
        return {}
    air = pd.to_numeric(conditions.get("air_temperature", conditions.get("AirTemp")), errors="coerce")
    track = pd.to_numeric(conditions.get("track_temperature", conditions.get("TrackTemp")), errors="coerce")
    rainfall = pd.to_numeric(conditions.get("rainfall", conditions.get("Rainfall")), errors="coerce")
    wind = pd.to_numeric(conditions.get("wind_speed", conditions.get("WindSpeed")), errors="coerce")
    return {
        "average_air_temp_c": round(float(air.dropna().mean()), 1) if air.notna().any() else None,
        "average_track_temp_c": round(float(track.dropna().mean()), 1) if track.notna().any() else None,
        "rain_samples": int((rainfall.fillna(0) > 0).sum()) if not rainfall.empty else 0,
        "average_wind_kph": round(float(wind.dropna().mean()), 1) if wind.notna().any() else None,
    }


def _history_laps_payload(year: int, round_number: int, limit: int = 250) -> dict[str, object]:
    laps = _history_lap_frame(year, round_number)
    columns = [
        "driver_code",
        "lap_number",
        "stint_number",
        "compound",
        "lap_time_seconds",
        "sector1_time",
        "sector2_time",
        "sector3_time",
        "SpeedST",
        "session_name",
    ]
    available = [column for column in columns if column in laps]
    rows = _history_records(_sort_by_numeric(laps[available], "lap_number"), limit=limit) if available else []
    return {
        "year": year,
        "round": round_number,
        "rows": rows,
        "metadata": {
            **_history_scope_metadata(),
            "available": not laps.empty,
            "row_count": int(len(laps)),
            "note": "Lap detail requires generated rich FastF1/OpenF1 artifacts.",
        },
    }


def _history_driver_payload(driver_code: str) -> dict[str, object]:
    code = driver_code.upper()
    races = _history_races()
    if races.empty or "driver_code" not in races:
        return {"driver_code": code, "summary": {}, "results": [], "metadata": _history_scope_metadata()}
    rows = races.rename(columns={"season": "year"}).copy()
    rows = rows[rows["driver_code"].astype(str).str.upper() == code].copy()
    if rows.empty:
        return {"driver_code": code, "summary": {}, "results": [], "metadata": _history_scope_metadata()}
    rows["finish_position"] = pd.to_numeric(rows.get("finish_position"), errors="coerce")
    rows["grid_position"] = pd.to_numeric(rows.get("grid_position"), errors="coerce")
    points = pd.to_numeric(rows.get("points"), errors="coerce").fillna(0) if "points" in rows else pd.Series(dtype=float)
    summary = {
        "starts": int(len(rows)),
        "wins": int((rows["finish_position"] == 1).sum()),
        "podiums": int((rows["finish_position"] <= 3).sum()),
        "points": round(float(points.sum()), 2) if not points.empty else None,
        "average_finish": round(float(rows["finish_position"].dropna().mean()), 2) if rows["finish_position"].notna().any() else None,
        "average_grid": round(float(rows["grid_position"].dropna().mean()), 2) if rows["grid_position"].notna().any() else None,
        "teams": sorted(rows.get("constructor_name", pd.Series(dtype=str)).dropna().astype(str).unique().tolist()),
    }
    return {
        "driver_code": code,
        "driver_name": rows["driver_name"].dropna().iloc[-1] if "driver_name" in rows and rows["driver_name"].notna().any() else code,
        "summary": summary,
        "season_summaries": _history_entity_seasons(rows, "driver"),
        "teammate_summary": _history_teammate_summary(code),
        "results": _history_records(rows.sort_values(["year", "round"], ascending=[False, False]).head(60)),
        "metadata": _history_scope_metadata(),
    }


def _history_team_payload(team_name: str) -> dict[str, object]:
    races = _history_races()
    if races.empty or "constructor_name" not in races:
        return {"team_name": team_name, "summary": {}, "results": [], "metadata": _history_scope_metadata()}
    rows = races.rename(columns={"season": "year"}).copy()
    rows = rows[rows["constructor_name"].astype(str).str.lower().str.contains(team_name.lower(), regex=False)].copy()
    if rows.empty:
        return {"team_name": team_name, "summary": {}, "results": [], "metadata": _history_scope_metadata()}
    rows["finish_position"] = pd.to_numeric(rows.get("finish_position"), errors="coerce")
    points = pd.to_numeric(rows.get("points"), errors="coerce").fillna(0) if "points" in rows else pd.Series(dtype=float)
    summary = {
        "entries": int(len(rows)),
        "wins": int((rows["finish_position"] == 1).sum()),
        "podiums": int((rows["finish_position"] <= 3).sum()),
        "points": round(float(points.sum()), 2) if not points.empty else None,
        "average_finish": round(float(rows["finish_position"].dropna().mean()), 2) if rows["finish_position"].notna().any() else None,
        "drivers": sorted(rows.get("driver_code", pd.Series(dtype=str)).dropna().astype(str).unique().tolist()),
    }
    return {
        "team_name": rows["constructor_name"].dropna().iloc[-1] if rows["constructor_name"].notna().any() else team_name,
        "summary": summary,
        "season_summaries": _history_entity_seasons(rows, "team"),
        "lineup_history": _history_team_lineup(rows),
        "results": _history_records(rows.sort_values(["year", "round"], ascending=[False, False]).head(80)),
        "metadata": _history_scope_metadata(),
    }


def _history_entity_seasons(rows: pd.DataFrame, entity_type: str) -> list[dict[str, object]]:
    if rows.empty:
        return []
    frame = rows.copy()
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce").astype("Int64")
    frame["finish_position"] = pd.to_numeric(frame.get("finish_position"), errors="coerce")
    frame["grid_position"] = pd.to_numeric(frame.get("grid_position"), errors="coerce")
    frame["points_numeric"] = pd.to_numeric(frame.get("points"), errors="coerce").fillna(0) if "points" in frame else 0
    grouped = frame.groupby("year", dropna=True).agg(
        entries=("round", "count"),
        wins=("finish_position", lambda s: int((s == 1).sum())),
        podiums=("finish_position", lambda s: int((s <= 3).sum())),
        points=("points_numeric", "sum"),
        average_finish=("finish_position", "mean"),
        average_grid=("grid_position", "mean"),
    ).reset_index()
    if entity_type == "team" and "driver_code" in frame:
        drivers = frame.groupby("year")["driver_code"].apply(lambda s: sorted(s.dropna().astype(str).unique().tolist())).reset_index(name="drivers")
        grouped = grouped.merge(drivers, on="year", how="left")
    grouped["points"] = grouped["points"].round(2)
    grouped["average_finish"] = grouped["average_finish"].round(2)
    grouped["average_grid"] = grouped["average_grid"].round(2)
    return _history_records(grouped.sort_values("year", ascending=False))


def _history_team_lineup(rows: pd.DataFrame) -> list[dict[str, object]]:
    if rows.empty or "driver_code" not in rows:
        return []
    frame = rows.copy()
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce").astype("Int64")
    lineup = frame.groupby("year")["driver_code"].apply(lambda s: sorted(s.dropna().astype(str).unique().tolist())).reset_index(name="drivers")
    return _history_records(lineup.sort_values("year", ascending=False))


def _history_teammate_summary(driver_code: str) -> list[dict[str, object]]:
    races = _history_races()
    if races.empty or "constructor_name" not in races or "driver_code" not in races:
        return []
    frame = races.rename(columns={"season": "year"}).copy()
    frame["finish_position"] = pd.to_numeric(frame.get("finish_position"), errors="coerce")
    own = frame[frame["driver_code"].astype(str).str.upper() == driver_code.upper()]
    records = []
    for _, row in own.iterrows():
        teammates = frame[
            (frame["year"] == row["year"])
            & (frame["round"] == row["round"])
            & (frame["constructor_name"] == row["constructor_name"])
            & (frame["driver_code"].astype(str).str.upper() != driver_code.upper())
        ]
        for _, teammate in teammates.iterrows():
            records.append(
                {
                    "year": row["year"],
                    "teammate": teammate.get("driver_code"),
                    "driver_ahead": bool(row["finish_position"] < teammate.get("finish_position"))
                    if pd.notna(row["finish_position"]) and pd.notna(teammate.get("finish_position"))
                    else None,
                    "finish_delta": float(row["finish_position"] - teammate.get("finish_position"))
                    if pd.notna(row["finish_position"]) and pd.notna(teammate.get("finish_position"))
                    else None,
                }
            )
    if not records:
        return []
    teammate_df = pd.DataFrame(records)
    teammate_df = teammate_df.dropna(subset=["driver_ahead"])
    if teammate_df.empty:
        return []
    grouped = teammate_df.groupby(["year", "teammate"], dropna=True).agg(
        head_to_head_wins=("driver_ahead", "sum"),
        comparisons=("driver_ahead", "count"),
        average_finish_delta=("finish_delta", "mean"),
    ).reset_index()
    grouped["average_finish_delta"] = grouped["average_finish_delta"].round(2)
    return _history_records(grouped.sort_values(["year", "comparisons"], ascending=[False, False]).head(12))


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


@app.get("/api/history/seasons")
def history_seasons() -> dict[str, object]:
    return _history_season_payload()


@app.get("/api/history/{year}/races")
def history_races(year: int) -> dict[str, object]:
    return _history_year_payload(year)


@app.get("/api/history/{year}/{round_number}/summary")
def history_race_summary(year: int, round_number: int) -> dict[str, object]:
    return _history_summary_payload(year, round_number)


@app.get("/api/history/{year}/{round_number}/qualifying")
def history_qualifying(year: int, round_number: int) -> dict[str, object]:
    qualifying = _sort_by_numeric(_history_quali_rows(year, round_number), "qualifying_position")
    return {
        "year": year,
        "round": round_number,
        "rows": _history_records(qualifying),
        "metadata": _history_scope_metadata(),
    }


@app.get("/api/history/{year}/{round_number}/laps")
def history_laps(year: int, round_number: int, limit: int = 250) -> dict[str, object]:
    return _history_laps_payload(year, round_number, limit=max(1, min(limit, 1000)))


@app.get("/api/history/drivers/{driver_code}")
def history_driver(driver_code: str) -> dict[str, object]:
    return _history_driver_payload(driver_code)


@app.get("/api/history/teams/{team_name}")
def history_team(team_name: str) -> dict[str, object]:
    return _history_team_payload(team_name)


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
