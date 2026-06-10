from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime

import joblib
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import brier_score_loss, mean_absolute_error, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from f1_predictor.features.pipeline import FEATURE_COLUMNS
from f1_predictor.settings import (
    CALIBRATION_REPORT_PATH,
    DATASET_METADATA_PATH,
    FEATURES_PATH,
    METRICS_PATH,
    MODEL_BUNDLE_PATH,
    MODEL_METADATA_PATH,
    ensure_directories,
)


@dataclass
class TrainMetrics:
    win_brier: float
    podium_brier: float
    top10_brier: float
    podium_auc: float | None
    finish_mae: float
    train_rows: int
    validation_rows: int


def _classification_pipeline() -> Pipeline:
    return Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("model", HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05, random_state=42)),
        ]
    )


def _regression_pipeline(loss: str = "squared_error", quantile: float | None = None) -> Pipeline:
    params: dict[str, object] = {"max_iter": 200, "learning_rate": 0.05, "random_state": 42, "loss": loss}
    if quantile is not None:
        params["quantile"] = quantile
    return Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("model", HistGradientBoostingRegressor(**params)),
        ]
    )


def _calibrated_classifier() -> CalibratedClassifierCV:
    base = _classification_pipeline()
    try:
        return CalibratedClassifierCV(estimator=base, method="sigmoid", cv=3)
    except TypeError:
        return CalibratedClassifierCV(base_estimator=base, method="sigmoid", cv=3)


def fit_classifier(x: pd.DataFrame, y: pd.Series):
    y = y.astype(int)
    if y.nunique() < 2:
        model = DummyClassifier(strategy="constant", constant=int(y.iloc[0]))
    elif y.value_counts().min() < 3:
        model = _classification_pipeline()
    else:
        model = _calibrated_classifier()
    model.fit(x, y)
    return model


def _positive_probability(model, x: pd.DataFrame) -> pd.Series:
    probabilities = model.predict_proba(x)
    if probabilities.shape[1] == 1:
        cls = int(model.classes_[0])
        value = 1.0 if cls == 1 else 0.0
        return pd.Series(value, index=x.index)
    class_index = list(model.classes_).index(1)
    return pd.Series(probabilities[:, class_index], index=x.index)


def _time_split(features: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    ordered = features.sort_values(["year", "round"])
    unique_races = ordered[["year", "round"]].drop_duplicates()
    if len(unique_races) < 4:
        return ordered, ordered
    split_index = max(1, int(len(unique_races) * 0.8))
    train_races = unique_races.iloc[:split_index]
    valid_races = unique_races.iloc[split_index:]
    train_keys = set(map(tuple, train_races[["year", "round"]].to_numpy()))
    valid_keys = set(map(tuple, valid_races[["year", "round"]].to_numpy()))
    row_keys = ordered[["year", "round"]].apply(tuple, axis=1)
    return ordered[row_keys.isin(train_keys)], ordered[row_keys.isin(valid_keys)]


def _score_auc(y_true: pd.Series, y_prob: pd.Series) -> float | None:
    try:
        return float(roc_auc_score(y_true.astype(int), y_prob))
    except ValueError:
        return None


def _load_dataset_metadata() -> dict[str, object]:
    if DATASET_METADATA_PATH.exists():
        return json.loads(DATASET_METADATA_PATH.read_text(encoding="utf-8"))
    return {}


def _calibration_report(y_true: pd.Series, y_prob: pd.Series, bins: int = 10) -> pd.DataFrame:
    report = pd.DataFrame({"actual": y_true.astype(int).to_numpy(), "predicted": y_prob.to_numpy()})
    report["bin"] = pd.cut(report["predicted"], bins=bins, include_lowest=True, duplicates="drop")
    grouped = report.groupby("bin", observed=True).agg(
        count=("actual", "size"),
        mean_predicted_probability=("predicted", "mean"),
        observed_podium_rate=("actual", "mean"),
    )
    grouped["calibration_error"] = (
        grouped["mean_predicted_probability"] - grouped["observed_podium_rate"]
    ).abs()
    grouped = grouped.reset_index()
    grouped["bin"] = grouped["bin"].astype(str)
    return grouped


def train_models() -> tuple[dict[str, object], TrainMetrics]:
    ensure_directories()
    if not FEATURES_PATH.exists():
        raise FileNotFoundError(f"Missing features at {FEATURES_PATH}. Run feature generation first.")

    features = pd.read_parquet(FEATURES_PATH).dropna(subset=["finish_position", "podium", "win", "top10"])
    train, valid = _time_split(features)

    x_train = train[FEATURE_COLUMNS]
    x_valid = valid[FEATURE_COLUMNS]

    win_model = fit_classifier(x_train, train["win"])
    podium_model = fit_classifier(x_train, train["podium"])
    top10_model = fit_classifier(x_train, train["top10"])
    finish_model = _regression_pipeline()
    finish_lower_model = _regression_pipeline(loss="quantile", quantile=0.2)
    finish_upper_model = _regression_pipeline(loss="quantile", quantile=0.8)

    y_finish = train["finish_position"].astype(float)
    finish_model.fit(x_train, y_finish)
    finish_lower_model.fit(x_train, y_finish)
    finish_upper_model.fit(x_train, y_finish)

    win_prob = _positive_probability(win_model, x_valid)
    podium_prob = _positive_probability(podium_model, x_valid)
    top10_prob = _positive_probability(top10_model, x_valid)
    podium_prob = pd.concat([podium_prob, win_prob], axis=1).max(axis=1)
    top10_prob = pd.concat([top10_prob, podium_prob], axis=1).max(axis=1)
    finish_pred = finish_model.predict(x_valid)

    metrics = TrainMetrics(
        win_brier=float(brier_score_loss(valid["win"].astype(int), win_prob)),
        podium_brier=float(brier_score_loss(valid["podium"].astype(int), podium_prob)),
        top10_brier=float(brier_score_loss(valid["top10"].astype(int), top10_prob)),
        podium_auc=_score_auc(valid["podium"], podium_prob),
        finish_mae=float(mean_absolute_error(valid["finish_position"].astype(float), finish_pred)),
        train_rows=int(len(train)),
        validation_rows=int(len(valid)),
    )
    trained_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    model_version = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    dataset_metadata = _load_dataset_metadata()
    calibration = _calibration_report(valid["podium"], podium_prob)

    bundle = {
        "model_version": model_version,
        "trained_at_utc": trained_at,
        "dataset_version": dataset_metadata.get("dataset_version"),
        "feature_columns": FEATURE_COLUMNS,
        "win_model": win_model,
        "podium_model": podium_model,
        "top10_model": top10_model,
        "finish_model": finish_model,
        "finish_lower_model": finish_lower_model,
        "finish_upper_model": finish_upper_model,
        "metrics": asdict(metrics),
    }
    MODEL_BUNDLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, MODEL_BUNDLE_PATH)

    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    metadata = {
        "model_version": model_version,
        "trained_at_utc": trained_at,
        "dataset_version": dataset_metadata.get("dataset_version"),
        "model_path": str(MODEL_BUNDLE_PATH),
        "metrics": asdict(metrics),
    }
    METRICS_PATH.write_text(json.dumps(asdict(metrics), indent=2), encoding="utf-8")
    MODEL_METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    calibration.to_csv(CALIBRATION_REPORT_PATH, index=False)

    print(f"Wrote model bundle to {MODEL_BUNDLE_PATH}")
    print(f"Wrote metrics to {METRICS_PATH}")
    print(f"Wrote model metadata to {MODEL_METADATA_PATH}")
    print(f"Wrote podium calibration report to {CALIBRATION_REPORT_PATH}")
    print(f"Validation podium Brier: {metrics.podium_brier:.4f}")
    if metrics.podium_auc is not None:
        print(f"Validation podium AUC: {metrics.podium_auc:.4f}")
    print(f"Validation finish MAE: {metrics.finish_mae:.3f}")
    return bundle, metrics


def parse_args() -> argparse.Namespace:
    return argparse.ArgumentParser(description="Train calibrated baseline models.").parse_args()


def main() -> None:
    parse_args()
    train_models()


if __name__ == "__main__":
    main()
