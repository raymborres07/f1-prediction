from __future__ import annotations

import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen

import pandas as pd

from f1_predictor.settings import OPENF1_RAW_DIR, ensure_directories


BASE_URL = "https://api.openf1.org/v1"
OPENF1_ENDPOINTS = {
    "car_data",
    "drivers",
    "intervals",
    "laps",
    "location",
    "meetings",
    "pit",
    "position",
    "race_control",
    "session_result",
    "sessions",
    "starting_grid",
    "stints",
    "weather",
}


class OpenF1Client:
    """Small OpenF1 REST client with versioned raw JSON cache.

    OpenF1 historical data is available from 2023 onward. Keep request cadence
    conservative because the public free tier is rate limited.
    """

    def __init__(self, raw_dir: Path = OPENF1_RAW_DIR, sleep_seconds: float = 0.35) -> None:
        ensure_directories()
        self.raw_dir = raw_dir
        self.sleep_seconds = sleep_seconds
        self.version = datetime.now(UTC).strftime("%Y%m%d%H%M%S")

    def _cache_path(self, endpoint: str, params: dict[str, Any]) -> Path:
        stable = json.dumps({"endpoint": endpoint, "params": params}, sort_keys=True, default=str)
        digest = hashlib.sha256(stable.encode("utf-8")).hexdigest()[:16]
        return self.raw_dir / self.version / endpoint / f"{digest}.json"

    def get(self, endpoint: str, **params: Any) -> pd.DataFrame:
        if endpoint not in OPENF1_ENDPOINTS:
            raise ValueError(f"Unsupported OpenF1 endpoint: {endpoint}")
        clean_params = {key: value for key, value in params.items() if value is not None}
        path = self._cache_path(endpoint, clean_params)
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            url = f"{BASE_URL}/{endpoint}"
            if clean_params:
                url = f"{url}?{urlencode(clean_params)}"
            with urlopen(url, timeout=60) as response:
                data = json.loads(response.read().decode("utf-8"))
            path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            time.sleep(self.sleep_seconds)
        return pd.DataFrame(data)


def sessions_for_year(client: OpenF1Client, year: int) -> pd.DataFrame:
    sessions = client.get("sessions", year=year)
    if sessions.empty:
        return sessions
    sessions["year"] = year
    return sessions
