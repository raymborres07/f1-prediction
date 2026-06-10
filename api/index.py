from __future__ import annotations

import sys
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_SRC = ROOT / "f1-predictor" / "src"
if str(APP_SRC) not in sys.path:
    sys.path.insert(0, str(APP_SRC))

os.environ.setdefault("F1_PREDICTOR_USE_DEMO_DATA", "1")

from f1_predictor.api.main import app  # noqa: E402
