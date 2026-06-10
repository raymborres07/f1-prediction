from __future__ import annotations

import argparse
from datetime import UTC, datetime

from f1_predictor.features.pipeline import build_dataset
from f1_predictor.ingest.pipeline import ingest_years
from f1_predictor.models.backtest import run_backtest
from f1_predictor.models.predict import next_race, predict_race
from f1_predictor.models.train import train_models


def parse_args() -> argparse.Namespace:
    current_year = datetime.now(UTC).year
    parser = argparse.ArgumentParser(description="Run ingestion, dataset build, training, and next-race prediction.")
    parser.add_argument("--start-year", type=int, default=max(2018, current_year - 4))
    parser.add_argument("--end-year", type=int, default=current_year)
    parser.add_argument("--backtest", action="store_true", help="Also run chronological walk-forward backtest.")
    parser.add_argument("--min-train-races", type=int, default=12)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ingest_years(range(args.start_year, args.end_year + 1))
    build_dataset()
    if args.backtest:
        run_backtest(min_train_races=args.min_train_races)
    train_models()
    race = next_race()
    predict_race(int(race["year"]), int(race["round"]))
    print(f"Refreshed next-race predictions for {race['event_name']} ({race['year']} round {race['round']})")


if __name__ == "__main__":
    main()
