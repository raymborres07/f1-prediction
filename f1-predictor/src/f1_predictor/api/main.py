from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException
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
    DEMO_SIMULATION_DISTRIBUTIONS_PATH,
    DEMO_SIMULATION_METADATA_PATH,
    DEMO_SIMULATION_SUMMARY_PATH,
    DEMO_MODEL_BUNDLE_PATH,
    DEMO_MODEL_METADATA_PATH,
    DEMO_SCHEDULE_PATH,
    MODEL_BUNDLE_PATH,
    MODEL_METADATA_PATH,
    SCHEDULE_PATH,
    SIMULATION_DISTRIBUTIONS_PATH,
    SIMULATION_METADATA_PATH,
    SIMULATION_SUMMARY_PATH,
    readable_path,
)


WEB_DIR = Path(__file__).resolve().parents[1] / "web"

app = FastAPI(title="F1 Predictor", version="0.1.0")
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


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
    distributions = {
        row.get("driver_code"): row
        for row in payload.get("finish_distributions", [])
        if row.get("driver_code") is not None
    }
    predictions = []
    for row in payload.get("predictions", []):
        low, high = _finish_band_from_distribution(distributions.get(row.get("driver_code"), {}))
        predictions.append(
            {
                "prediction_rank": row.get("simulation_rank"),
                "year": row.get("season"),
                "round": row.get("round"),
                "event_name": f"{row.get('season')} Round {row.get('round')} simulation",
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
                "has_quali_data": 0,
                "data_freshness": "Monte Carlo packaged demo",
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
        "event_name": f"{payload['race']['year']} Round {payload['race']['round']} simulation",
        "location": "Packaged demo",
        "race_date": metadata.get("built_at_utc"),
    }
    response_metadata = _metadata()
    response_metadata["prediction_mode"] = "race simulation"
    response_metadata["data_freshness"] = "Monte Carlo packaged demo"
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


@app.get("/api/predictions/next")
def predictions_next() -> dict[str, object]:
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
