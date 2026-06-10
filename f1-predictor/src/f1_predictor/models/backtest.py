from __future__ import annotations

import argparse

import pandas as pd
from sklearn.metrics import brier_score_loss, mean_absolute_error

from f1_predictor.features.pipeline import FEATURE_COLUMNS
from f1_predictor.models.train import _positive_probability, _regression_pipeline, fit_classifier
from f1_predictor.settings import BACKTEST_METRICS_PATH, BACKTEST_PREDICTIONS_PATH, FEATURES_PATH, ensure_directories


def _race_key_frame(df: pd.DataFrame) -> pd.Series:
    return df[["year", "round"]].apply(tuple, axis=1)


def run_backtest(min_train_races: int = 12) -> tuple[pd.DataFrame, pd.DataFrame]:
    ensure_directories()
    if not FEATURES_PATH.exists():
        raise FileNotFoundError(f"Missing modeling table at {FEATURES_PATH}. Run features first.")

    data = pd.read_parquet(FEATURES_PATH).dropna(subset=["finish_position", "podium", "win", "top10"])
    data = data.sort_values(["year", "round", "driver_code"])
    races = data[["year", "round", "event_name"]].drop_duplicates().reset_index(drop=True)

    prediction_frames: list[pd.DataFrame] = []
    metric_rows: list[dict[str, object]] = []

    for race_index in range(min_train_races, len(races)):
        target_race = races.iloc[race_index]
        train_races = races.iloc[:race_index]
        train_keys = set(map(tuple, train_races[["year", "round"]].to_numpy()))
        target_key = (target_race["year"], target_race["round"])

        train = data[_race_key_frame(data).isin(train_keys)]
        target = data[_race_key_frame(data) == target_key]
        if train.empty or target.empty:
            continue

        x_train = train[FEATURE_COLUMNS]
        x_target = target[FEATURE_COLUMNS]

        podium_model = fit_classifier(x_train, train["podium"])
        win_model = fit_classifier(x_train, train["win"])
        top10_model = fit_classifier(x_train, train["top10"])
        finish_model = _regression_pipeline()
        finish_model.fit(x_train, train["finish_position"].astype(float))

        preds = target.copy()
        preds["win_probability"] = _positive_probability(win_model, x_target)
        preds["podium_probability"] = _positive_probability(podium_model, x_target)
        preds["top10_probability"] = _positive_probability(top10_model, x_target)
        preds["podium_probability"] = preds[["podium_probability", "win_probability"]].max(axis=1)
        preds["top10_probability"] = preds[["top10_probability", "podium_probability"]].max(axis=1)
        preds["expected_finish"] = finish_model.predict(x_target)
        preds["prediction_rank"] = preds["podium_probability"].rank(ascending=False, method="first").astype(int)
        prediction_frames.append(preds)

        metric_rows.append(
            {
                "year": int(target_race["year"]),
                "round": int(target_race["round"]),
                "event_name": target_race["event_name"],
                "train_races": int(len(train_races)),
                "train_rows": int(len(train)),
                "prediction_rows": int(len(target)),
                "win_brier": float(brier_score_loss(target["win"].astype(int), preds["win_probability"])),
                "podium_brier": float(brier_score_loss(target["podium"].astype(int), preds["podium_probability"])),
                "top10_brier": float(brier_score_loss(target["top10"].astype(int), preds["top10_probability"])),
                "finish_mae": float(mean_absolute_error(target["finish_position"].astype(float), preds["expected_finish"])),
            }
        )
        print(
            f"{int(target_race['year'])} R{int(target_race['round'])}: "
            f"podium Brier {metric_rows[-1]['podium_brier']:.4f}, "
            f"finish MAE {metric_rows[-1]['finish_mae']:.3f}"
        )

    predictions = pd.concat(prediction_frames, ignore_index=True) if prediction_frames else pd.DataFrame()
    metrics = pd.DataFrame(metric_rows)
    BACKTEST_PREDICTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    predictions.to_parquet(BACKTEST_PREDICTIONS_PATH, index=False)
    metrics.to_csv(BACKTEST_METRICS_PATH, index=False)

    if not metrics.empty:
        print(f"Wrote backtest predictions to {BACKTEST_PREDICTIONS_PATH}")
        print(f"Wrote race metrics to {BACKTEST_METRICS_PATH}")
        print(f"Mean podium Brier: {metrics['podium_brier'].mean():.4f}")
        print(f"Mean finish MAE: {metrics['finish_mae'].mean():.3f}")
    return predictions, metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run chronological walk-forward backtest.")
    parser.add_argument("--min-train-races", type=int, default=12)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_backtest(min_train_races=args.min_train_races)


if __name__ == "__main__":
    main()
