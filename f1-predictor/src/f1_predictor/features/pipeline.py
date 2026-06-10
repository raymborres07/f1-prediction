from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime

import numpy as np
import pandas as pd

from f1_predictor.settings import (
    CONSTRUCTORS_PATH,
    DATASET_METADATA_PATH,
    DRIVERS_PATH,
    FEATURES_PATH,
    MODELING_TABLE_PATH,
    PROCESSED_DIR,
    QUALIFYING_CLEAN_PATH,
    QUALIFYING_RESULTS_PATH,
    RACES_CLEAN_PATH,
    RACE_RESULTS_PATH,
    SCHEDULE_PATH,
    ensure_directories,
)


FEATURE_COLUMNS = [
    "grid_position",
    "qualifying_position",
    "qualifying_gap_to_pole",
    "teammate_quali_delta",
    "driver_last3_avg_finish",
    "driver_last5_avg_finish",
    "driver_last3_podium_rate",
    "driver_last5_top10_rate",
    "constructor_last3_avg_finish",
    "constructor_last5_avg_finish",
    "constructor_last5_podium_rate",
    "driver_circuit_avg_finish",
    "driver_circuit_podium_rate",
    "driver_dnf_rate",
    "constructor_dnf_rate",
    "has_quali_data",
]


IDENTITY_COLUMNS = [
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
]


def _load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    missing = [
        str(path)
        for path in (SCHEDULE_PATH, RACE_RESULTS_PATH, QUALIFYING_RESULTS_PATH)
        if not path.exists()
    ]
    if missing:
        raise FileNotFoundError(f"Missing processed inputs. Run ingestion first: {', '.join(missing)}")
    return (
        pd.read_parquet(SCHEDULE_PATH),
        pd.read_parquet(RACE_RESULTS_PATH),
        pd.read_parquet(QUALIFYING_RESULTS_PATH),
    )


def _finish_position(value: object) -> float:
    number = pd.to_numeric(value, errors="coerce")
    return float(number) if pd.notna(number) else np.nan


def _is_dnf(status: object, finish_position: object) -> int:
    text = str(status or "").lower()
    if not text or text in {"finished", "+1 lap", "+2 laps", "+3 laps", "+4 laps", "+5 laps"}:
        return 0
    non_finish_markers = {
        "retired",
        "accident",
        "collision",
        "engine",
        "gearbox",
        "hydraulics",
        "electrical",
        "brakes",
        "suspension",
        "disqualified",
        "withdrawn",
    }
    return int(any(reason in text for reason in non_finish_markers) or pd.isna(finish_position))


def _timedelta_seconds(value: object) -> float:
    if pd.isna(value):
        return np.nan
    try:
        return pd.Timedelta(value).total_seconds()
    except (TypeError, ValueError):
        return np.nan


def _best_quali_seconds(row: pd.Series) -> float:
    times = [_timedelta_seconds(row.get(column)) for column in ("Q1", "Q2", "Q3", "Time")]
    times = [value for value in times if pd.notna(value)]
    return min(times) if times else np.nan


def clean_race_results(races: pd.DataFrame, schedule: pd.DataFrame) -> pd.DataFrame:
    df = races.copy()
    df["finish_position"] = df["Position"].map(_finish_position)
    df["grid_position"] = pd.to_numeric(df["GridPosition"], errors="coerce")
    df["driver_number"] = pd.to_numeric(df["DriverNumber"], errors="coerce")
    df["podium"] = (df["finish_position"] <= 3).astype(int)
    df["win"] = (df["finish_position"] == 1).astype(int)
    df["top10"] = (df["finish_position"] <= 10).astype(int)
    df["dnf"] = df.apply(lambda row: _is_dnf(row.get("Status"), row.get("finish_position")), axis=1)
    clean = df.rename(
        columns={
            "Abbreviation": "driver_code",
            "BroadcastName": "driver_name",
            "DriverId": "driver_id",
            "TeamName": "constructor_name",
            "Status": "status",
            "Points": "points",
        }
    )
    clean = clean.merge(
        schedule[["year", "round", "event_name", "location", "race_date", "event_format"]],
        on=["year", "round"],
        how="left",
    )
    columns = [
        *IDENTITY_COLUMNS,
        "grid_position",
        "finish_position",
        "classified_position",
        "status",
        "points",
        "podium",
        "win",
        "top10",
        "dnf",
        "event_format",
    ]
    clean = clean.rename(columns={"ClassifiedPosition": "classified_position"})
    for column in columns:
        if column not in clean.columns:
            clean[column] = pd.NA
    return clean[columns].sort_values(["year", "round", "finish_position"], na_position="last")


def clean_qualifying_results(quali: pd.DataFrame) -> pd.DataFrame:
    if quali.empty:
        return pd.DataFrame(
            columns=[
                "year",
                "round",
                "driver_code",
                "driver_id",
                "driver_name",
                "constructor_name",
                "qualifying_position",
                "qualifying_seconds",
                "qualifying_gap_to_pole",
            ]
        )

    df = quali.copy()
    df["qualifying_position"] = pd.to_numeric(df["Position"], errors="coerce")
    df["qualifying_seconds"] = df.apply(_best_quali_seconds, axis=1)
    df["qualifying_gap_to_pole"] = df.groupby(["year", "round"])["qualifying_seconds"].transform(lambda s: s - s.min())
    clean = df.rename(
        columns={
            "Abbreviation": "driver_code",
            "BroadcastName": "driver_name",
            "DriverId": "driver_id",
            "TeamName": "constructor_name",
        }
    )
    return clean[
        [
            "year",
            "round",
            "driver_code",
            "driver_id",
            "driver_name",
            "constructor_name",
            "qualifying_position",
            "qualifying_seconds",
            "qualifying_gap_to_pole",
        ]
    ].sort_values(["year", "round", "qualifying_position"], na_position="last")


def _drivers_table(races: pd.DataFrame) -> pd.DataFrame:
    return (
        races[["driver_id", "driver_code", "driver_name", "driver_number"]]
        .drop_duplicates()
        .sort_values(["driver_code", "driver_name"])
        .reset_index(drop=True)
    )


def _constructors_table(races: pd.DataFrame) -> pd.DataFrame:
    return (
        races[["constructor_name"]]
        .dropna()
        .drop_duplicates()
        .sort_values("constructor_name")
        .reset_index(drop=True)
    )


def _prior_rows(history: pd.DataFrame, row: pd.Series) -> pd.DataFrame:
    return history[
        ((history["year"] < row["year"]) | ((history["year"] == row["year"]) & (history["round"] < row["round"])))
        & history["finish_position"].notna()
    ]


def _rolling_prior_features(races: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    history = races.sort_values(["year", "round", "driver_code"])

    for _, row in history.iterrows():
        prior = _prior_rows(history, row)
        driver_prior = prior[prior["driver_code"] == row["driver_code"]]
        constructor_prior = prior[prior["constructor_name"] == row["constructor_name"]]
        circuit_prior = driver_prior[driver_prior["location"] == row["location"]]

        driver_last3 = driver_prior.tail(3)
        driver_last5 = driver_prior.tail(5)
        constructor_last3 = constructor_prior.tail(6)
        constructor_last5 = constructor_prior.tail(10)

        rows.append(
            {
                "year": row["year"],
                "round": row["round"],
                "driver_code": row["driver_code"],
                "driver_last3_avg_finish": driver_last3["finish_position"].mean(),
                "driver_last5_avg_finish": driver_last5["finish_position"].mean(),
                "driver_last3_podium_rate": driver_last3["podium"].mean(),
                "driver_last5_top10_rate": driver_last5["top10"].mean(),
                "constructor_last3_avg_finish": constructor_last3["finish_position"].mean(),
                "constructor_last5_avg_finish": constructor_last5["finish_position"].mean(),
                "constructor_last5_podium_rate": constructor_last5["podium"].mean(),
                "driver_circuit_avg_finish": circuit_prior.tail(5)["finish_position"].mean(),
                "driver_circuit_podium_rate": circuit_prior.tail(5)["podium"].mean(),
                "driver_dnf_rate": driver_prior.tail(10)["dnf"].mean(),
                "constructor_dnf_rate": constructor_prior.tail(20)["dnf"].mean(),
            }
        )

    return pd.DataFrame(rows)


def _qualifying_features(qualifying: pd.DataFrame) -> pd.DataFrame:
    if qualifying.empty:
        return pd.DataFrame(
            columns=[
                "year",
                "round",
                "driver_code",
                "qualifying_position",
                "qualifying_gap_to_pole",
                "teammate_quali_delta",
                "has_quali_data",
            ]
        )

    rows: list[dict[str, object]] = []
    for _, group in qualifying.groupby(["year", "round", "constructor_name"], dropna=False):
        group = group.sort_values("qualifying_seconds")
        for _, row in group.iterrows():
            teammate = group[group["driver_code"] != row["driver_code"]]
            teammate_seconds = teammate["qualifying_seconds"].dropna()
            own_seconds = row["qualifying_seconds"]
            delta = np.nan
            if pd.notna(own_seconds) and not teammate_seconds.empty:
                delta = own_seconds - teammate_seconds.iloc[0]
            rows.append(
                {
                    "year": row["year"],
                    "round": row["round"],
                    "driver_code": row["driver_code"],
                    "qualifying_position": row["qualifying_position"],
                    "qualifying_gap_to_pole": row["qualifying_gap_to_pole"],
                    "teammate_quali_delta": delta,
                    "has_quali_data": int(pd.notna(own_seconds)),
                }
            )
    return pd.DataFrame(rows)


def _fill_feature_defaults(modeling: pd.DataFrame, history: pd.DataFrame | None = None) -> pd.DataFrame:
    df = modeling.copy()
    source = history if history is not None and not history.empty else df
    finish_mean = source["finish_position"].mean() if "finish_position" in source else 10.5
    defaults = {
        "grid_position": source["grid_position"].median() if "grid_position" in source else 10.5,
        "qualifying_position": source["grid_position"].median() if "grid_position" in source else 10.5,
        "qualifying_gap_to_pole": 2.0,
        "teammate_quali_delta": 0.0,
        "driver_last3_avg_finish": finish_mean,
        "driver_last5_avg_finish": finish_mean,
        "driver_last3_podium_rate": source["podium"].mean() if "podium" in source else 0.15,
        "driver_last5_top10_rate": source["top10"].mean() if "top10" in source else 0.5,
        "constructor_last3_avg_finish": finish_mean,
        "constructor_last5_avg_finish": finish_mean,
        "constructor_last5_podium_rate": source["podium"].mean() if "podium" in source else 0.15,
        "driver_circuit_avg_finish": finish_mean,
        "driver_circuit_podium_rate": source["podium"].mean() if "podium" in source else 0.15,
        "driver_dnf_rate": source["dnf"].mean() if "dnf" in source else 0.1,
        "constructor_dnf_rate": source["dnf"].mean() if "dnf" in source else 0.1,
        "has_quali_data": 0,
    }
    for column, default in defaults.items():
        fallback = 0.0 if pd.isna(default) else default
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(float(fallback))
    return df


def build_modeling_table(races: pd.DataFrame, qualifying: pd.DataFrame) -> pd.DataFrame:
    modeling = races[
        [
            *IDENTITY_COLUMNS,
            "grid_position",
            "finish_position",
            "podium",
            "win",
            "top10",
            "dnf",
        ]
    ].copy()
    modeling = modeling.merge(_rolling_prior_features(races), on=["year", "round", "driver_code"], how="left")
    modeling = modeling.merge(_qualifying_features(qualifying), on=["year", "round", "driver_code"], how="left")
    modeling = _fill_feature_defaults(modeling, races)
    modeling["modeling_table_version"] = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    return modeling.sort_values(["year", "round", "driver_code"])


def build_dataset(write_versioned: bool = True) -> dict[str, pd.DataFrame]:
    ensure_directories()
    schedule, races_raw, quali_raw = _load_inputs()
    races = clean_race_results(races_raw, schedule)
    qualifying = clean_qualifying_results(quali_raw)
    drivers = _drivers_table(races)
    constructors = _constructors_table(races)
    modeling = build_modeling_table(races, qualifying)

    tables = {
        "races": races,
        "qualifying": qualifying,
        "drivers": drivers,
        "constructors": constructors,
        "modeling_table": modeling,
    }
    paths = {
        "races": RACES_CLEAN_PATH,
        "qualifying": QUALIFYING_CLEAN_PATH,
        "drivers": DRIVERS_PATH,
        "constructors": CONSTRUCTORS_PATH,
        "modeling_table": MODELING_TABLE_PATH,
    }
    version = modeling["modeling_table_version"].iloc[0]
    for name, table in tables.items():
        table.to_parquet(paths[name], index=False)
        if write_versioned:
            table.to_parquet(PROCESSED_DIR / f"{name}_{version}.parquet", index=False)
        print(f"Wrote {len(table):,} rows to {paths[name]}")

    modeling.to_parquet(FEATURES_PATH, index=False)
    metadata = {
        "dataset_version": version,
        "built_at_utc": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "tables": {
            name: {"rows": int(len(table)), "path": str(paths[name])}
            for name, table in tables.items()
        },
        "feature_columns": FEATURE_COLUMNS,
    }
    DATASET_METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Wrote modeling alias to {FEATURES_PATH}")
    print(f"Wrote dataset metadata to {DATASET_METADATA_PATH}")
    return tables


def build_features() -> pd.DataFrame:
    return build_dataset()["modeling_table"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build clean processed tables and modeling table.")
    parser.add_argument("--no-versioned", action="store_true", help="Skip timestamped table copies.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    build_dataset(write_versioned=not args.no_versioned)


if __name__ == "__main__":
    main()
