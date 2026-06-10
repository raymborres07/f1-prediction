from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime

import numpy as np
import pandas as pd

from f1_predictor.settings import (
    PRE_RACE_FEATURES_TABLE_PATH,
    RACE_SIM_INPUTS_TABLE_PATH,
    RICH_DATASET_METADATA_PATH,
    SIMULATION_DISTRIBUTIONS_PATH,
    SIMULATION_METADATA_PATH,
    SIMULATION_SUMMARY_PATH,
    SIMULATIONS_DIR,
    ensure_directories,
)


POSITION_COLUMNS = [f"p{position}_probability" for position in range(1, 23)]


def _load_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    if not PRE_RACE_FEATURES_TABLE_PATH.exists():
        raise FileNotFoundError("Missing pre_race_features.parquet. Run f1-features-rich first.")
    pre = pd.read_parquet(PRE_RACE_FEATURES_TABLE_PATH)
    sim = pd.read_parquet(RACE_SIM_INPUTS_TABLE_PATH) if RACE_SIM_INPUTS_TABLE_PATH.exists() else pd.DataFrame()
    return pre, sim


def _latest_event(features: pd.DataFrame) -> tuple[int, int]:
    latest = features[["season", "round"]].drop_duplicates().sort_values(["season", "round"]).iloc[-1]
    return int(latest["season"]), int(latest["round"])


def _feature_or_default(df: pd.DataFrame, column: str, default: float) -> pd.Series:
    if column not in df:
        return pd.Series(default, index=df.index, dtype=float)
    values = pd.to_numeric(df[column], errors="coerce")
    return values.fillna(values.median() if values.notna().any() else default)


def _build_driver_parameters(event: pd.DataFrame, sim_inputs: pd.DataFrame) -> pd.DataFrame:
    params = event.copy()
    if not sim_inputs.empty:
        sim_cols = [
            "season",
            "round",
            "driver_number",
            "expected_stints",
            "mean_stint_laps",
            "event_mean_stint_laps",
            "event_total_tyre_laps",
        ]
        available = [column for column in sim_cols if column in sim_inputs.columns]
        params = params.merge(sim_inputs[available], on=["season", "round", "driver_number"], how="left")

    grid = _feature_or_default(params, "grid_position", 11.5)
    quali_gap = _feature_or_default(params, "qualifying_gap_to_pole", 2.0)
    recent_finish = _feature_or_default(params, "driver_last5_avg_finish", 11.5)
    constructor_finish = _feature_or_default(params, "constructor_last5_avg_finish", 11.5)
    long_run = _feature_or_default(params, "practice_long_run_pace", _feature_or_default(params, "long_run_pace_last3", 92.0).median())
    single_lap = _feature_or_default(params, "practice_single_lap_pace", _feature_or_default(params, "avg_lap_time_last3", 92.0).median())
    dnf = _feature_or_default(params, "driver_last5_dnf_rate", 0.1)
    constructor_dnf = _feature_or_default(params, "constructor_last5_dnf_rate", 0.1)
    pit_loss = _feature_or_default(params, "pit_loss_last3", 2.5)
    stint_consistency = _feature_or_default(params, "practice_stint_consistency", 0.6)
    speed = _feature_or_default(params, "practice_speed_trap_max", _feature_or_default(params, "telemetry_speed_mean", 305.0).median())
    teammate_delta = _feature_or_default(params, "practice_teammate_single_lap_delta", _feature_or_default(params, "teammate_quali_delta", 0.0).median())
    upgrade_intensity = _feature_or_default(params, "estimated_upgrade_intensity", 0.0)

    params["latent_race_pace"] = (
        0.28 * recent_finish
        + 0.22 * constructor_finish
        + 0.18 * grid
        + 0.16 * quali_gap
        + 0.10 * (long_run - long_run.median())
        + 0.06 * (single_lap - single_lap.median())
        + 0.35 * teammate_delta
        - 0.6 * upgrade_intensity
    )
    params["reliability_risk"] = (0.65 * dnf + 0.35 * constructor_dnf).clip(0.01, 0.45)
    params["start_performance"] = (11.5 - grid).clip(-12, 12) / 16.0
    params["tyre_degradation"] = (0.45 * stint_consistency + 0.05 * _feature_or_default(params, "mean_stint_laps", 18.0)).clip(0.1, 6.0)
    params["pit_stop_loss"] = pit_loss.clip(0, 30)
    params["overtaking_strength"] = ((speed - speed.median()) / 18.0 + (11.5 - grid) / 22.0).clip(-2.0, 2.0)
    params["defending_strength"] = ((11.5 - constructor_finish) / 12.0 - teammate_delta / 2.5).clip(-2.0, 2.0)
    return params


def _simulate_event(params: pd.DataFrame, simulations: int, seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    drivers = params.reset_index(drop=True)
    n = len(drivers)
    finish_counts = np.zeros((n, max(22, n)), dtype=int)
    wins = np.zeros(n, dtype=int)
    podiums = np.zeros(n, dtype=int)
    top10 = np.zeros(n, dtype=int)
    expected = np.zeros(n, dtype=float)

    pace = drivers["latent_race_pace"].to_numpy(dtype=float)
    reliability = drivers["reliability_risk"].to_numpy(dtype=float)
    start = drivers["start_performance"].to_numpy(dtype=float)
    tyre = drivers["tyre_degradation"].to_numpy(dtype=float)
    pit = drivers["pit_stop_loss"].to_numpy(dtype=float)
    overtake = drivers["overtaking_strength"].to_numpy(dtype=float)
    defend = drivers["defending_strength"].to_numpy(dtype=float)

    for _ in range(simulations):
        start_noise = rng.normal(-start, 0.55, n)
        race_noise = rng.normal(0, 1.25, n)
        tyre_noise = rng.gamma(shape=2.0, scale=np.maximum(tyre, 0.1) / 8.0)
        pit_noise = rng.normal(pit / 10.0, 0.35, n)
        combat = rng.normal(-(overtake + defend) / 4.0, 0.3, n)
        dnf = rng.random(n) < reliability
        score = pace + start_noise + race_noise + tyre_noise + pit_noise + combat
        score[dnf] += 30 + rng.random(dnf.sum()) * 8
        order = np.argsort(score)
        positions = np.empty(n, dtype=int)
        positions[order] = np.arange(1, n + 1)
        for idx, position in enumerate(positions):
            finish_counts[idx, position - 1] += 1
        wins += positions == 1
        podiums += positions <= 3
        top10 += positions <= 10
        expected += positions

    summary = drivers[
        ["season", "round", "driver_number", "driver_code", "driver_name", "constructor_name"]
    ].copy()
    summary["win_probability"] = wins / simulations
    summary["podium_probability"] = podiums / simulations
    summary["top10_probability"] = top10 / simulations
    summary["expected_finish"] = expected / simulations
    summary["simulations"] = simulations
    summary = summary.sort_values(["win_probability", "podium_probability", "expected_finish"], ascending=[False, False, True])
    summary["simulation_rank"] = range(1, len(summary) + 1)

    distributions = drivers[
        ["season", "round", "driver_number", "driver_code", "driver_name", "constructor_name"]
    ].copy()
    for position in range(1, max(22, n) + 1):
        distributions[f"p{position}_probability"] = finish_counts[:, position - 1] / simulations
    return summary, distributions


def run_monte_carlo(
    season: int | None = None,
    round_number: int | None = None,
    simulations: int = 10_000,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    ensure_directories()
    features, sim_inputs = _load_inputs()
    if season is None or round_number is None:
        season, round_number = _latest_event(features)
    event = features[(features["season"] == season) & (features["round"] == round_number)].copy()
    if event.empty:
        raise ValueError(f"No rich feature rows for {season} round {round_number}")
    event_sim = sim_inputs[(sim_inputs["season"] == season) & (sim_inputs["round"] == round_number)].copy() if not sim_inputs.empty else pd.DataFrame()
    params = _build_driver_parameters(event, event_sim)
    summary, distributions = _simulate_event(params, simulations=simulations, seed=seed)

    SIMULATIONS_DIR.mkdir(parents=True, exist_ok=True)
    summary.to_parquet(SIMULATION_SUMMARY_PATH, index=False)
    distributions.to_parquet(SIMULATION_DISTRIBUTIONS_PATH, index=False)
    metadata = {
        "built_at_utc": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "season": season,
        "round": round_number,
        "simulations": simulations,
        "seed": seed,
        "model_components": [
            "latent_race_pace",
            "reliability_risk",
            "start_performance",
            "tyre_degradation",
            "pit_stop_loss",
            "overtaking_strength",
            "defending_strength",
        ],
    }
    if RICH_DATASET_METADATA_PATH.exists():
        metadata["rich_dataset"] = json.loads(RICH_DATASET_METADATA_PATH.read_text(encoding="utf-8")).get("dataset_version")
    SIMULATION_METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Wrote simulation summary to {SIMULATION_SUMMARY_PATH}")
    print(f"Wrote finish distributions to {SIMULATION_DISTRIBUTIONS_PATH}")
    return summary, distributions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Monte Carlo race simulations from rich feature tables.")
    parser.add_argument("--season", type=int)
    parser.add_argument("--round", dest="round_number", type=int)
    parser.add_argument("--simulations", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_monte_carlo(args.season, args.round_number, args.simulations, args.seed)


if __name__ == "__main__":
    main()
