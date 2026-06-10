from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd

from f1_predictor.settings import (
    EVENTS_TABLE_PATH,
    RAW_DIR,
    RICH_DATASET_METADATA_PATH,
    UPGRADE_FEATURES_TABLE_PATH,
    UPGRADE_NEWS_TABLE_PATH,
    ensure_directories,
)


DEFAULT_FEEDS = [
    "https://www.formula1.com/en/latest/all.xml",
    "https://www.autosport.com/rss/f1/news/",
    "https://www.motorsport.com/rss/f1/news/",
]

CONSTRUCTOR_ALIASES = {
    "Red Bull Racing": ["red bull", "rbr"],
    "Ferrari": ["ferrari", "scuderia"],
    "Mercedes": ["mercedes"],
    "McLaren": ["mclaren"],
    "Aston Martin": ["aston martin"],
    "Alpine": ["alpine"],
    "Williams": ["williams"],
    "RB": ["racing bulls", "rb"],
    "Haas F1 Team": ["haas"],
    "Kick Sauber": ["sauber", "stake", "kick sauber"],
}

UPDATE_KEYWORDS = {
    "aero_update": ["aero", "aerodynamic", "bodywork", "sidepod", "beam wing", "diffuser"],
    "floor_update": ["floor", "edge wing"],
    "front_wing_update": ["front wing", "nose"],
    "rear_wing_update": ["rear wing"],
    "suspension_update": ["suspension", "pushrod", "pullrod"],
    "cooling_update": ["cooling", "louvre", "inlet", "outlet"],
}


def _fetch_feed(url: str, raw_dir: Path, version: str) -> str:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    path = raw_dir / version / f"{digest}.xml"
    if path.exists():
        return path.read_text(encoding="utf-8", errors="ignore")
    path.parent.mkdir(parents=True, exist_ok=True)
    request = Request(url, headers={"User-Agent": "f1-predictor/0.1"})
    with urlopen(request, timeout=45) as response:
        text = response.read().decode("utf-8", errors="ignore")
    path.write_text(text, encoding="utf-8")
    time.sleep(0.5)
    return text


def _text(element: ET.Element, names: list[str]) -> str:
    for name in names:
        found = element.find(name)
        if found is not None and found.text:
            return found.text.strip()
    return ""


def _parse_feed(feed_xml: str, source_url: str) -> list[dict[str, object]]:
    root = ET.fromstring(feed_xml)
    items = root.findall(".//item")
    if not items:
        items = root.findall(".//{http://www.w3.org/2005/Atom}entry")
    rows = []
    for item in items:
        title = _text(item, ["title", "{http://www.w3.org/2005/Atom}title"])
        summary = _text(item, ["description", "summary", "{http://www.w3.org/2005/Atom}summary"])
        published = _text(item, ["pubDate", "published", "updated", "{http://www.w3.org/2005/Atom}published"])
        link = _text(item, ["link", "{http://www.w3.org/2005/Atom}link"])
        if not link:
            atom_link = item.find("{http://www.w3.org/2005/Atom}link")
            link = atom_link.attrib.get("href", "") if atom_link is not None else ""
        rows.append(
            {
                "source_url": source_url,
                "title": title,
                "summary": re.sub("<[^<]+?>", " ", summary),
                "published_at": pd.to_datetime(published, errors="coerce", utc=True),
                "url": link,
            }
        )
    return rows


def _tag_constructor(text: str) -> str | None:
    lower = text.lower()
    for constructor, aliases in CONSTRUCTOR_ALIASES.items():
        if any(alias in lower for alias in aliases):
            return constructor
    return None


def _tag_event(text: str, events: pd.DataFrame) -> tuple[int | None, int | None, str | None]:
    lower = text.lower()
    if events.empty:
        return None, None, None
    for _, event in events.iterrows():
        event_name = str(event.get("event_name", ""))
        country = str(event.get("country", ""))
        location = str(event.get("location", ""))
        candidates = [event_name.lower(), country.lower(), location.lower(), event_name.lower().replace(" grand prix", "")]
        if any(candidate and candidate in lower for candidate in candidates):
            return int(event["season"]), int(event["round"]), event_name
    return None, None, None


def _tag_updates(text: str) -> dict[str, object]:
    lower = text.lower()
    tags = {name: int(any(keyword in lower for keyword in keywords)) for name, keywords in UPDATE_KEYWORDS.items()}
    scope = sum(tags.values())
    intensity_terms = ["major", "significant", "package", "upgrade", "new", "revised", "changed"]
    intensity = min(1.0, 0.15 * scope + 0.1 * sum(term in lower for term in intensity_terms))
    tags.update(
        {
            "upgrade_present": int(scope > 0 or "upgrade" in lower or "update" in lower),
            "upgrade_scope": scope,
            "estimated_upgrade_intensity": round(float(intensity), 3),
        }
    )
    return tags


def _published_before_cutoff(published_at: object, events: pd.DataFrame, season: int | None, round_number: int | None) -> bool:
    if season is None or round_number is None or events.empty:
        return False
    event = events[(events["season"] == season) & (events["round"] == round_number)]
    if event.empty:
        return False
    cutoff_value = event["qualifying_date"].iloc[0] if "qualifying_date" in event.columns else pd.NaT
    if pd.isna(cutoff_value) and "race_date" in event.columns:
        cutoff_value = event["race_date"].iloc[0]
    published = pd.to_datetime(published_at, errors="coerce", utc=True)
    cutoff = pd.to_datetime(cutoff_value, errors="coerce", utc=True)
    if pd.isna(published) or pd.isna(cutoff):
        return False
    return bool(published <= cutoff)


def ingest_upgrade_news(feed_urls: list[str] | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    ensure_directories()
    version = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    raw_dir = RAW_DIR / "upgrade_news"
    feed_urls = feed_urls or DEFAULT_FEEDS
    events = pd.read_parquet(EVENTS_TABLE_PATH) if EVENTS_TABLE_PATH.exists() else pd.DataFrame()
    rows: list[dict[str, object]] = []
    for url in feed_urls:
        try:
            feed_xml = _fetch_feed(url, raw_dir, version)
            rows.extend(_parse_feed(feed_xml, url))
        except Exception as exc:
            print(f"Skipping upgrade feed {url}: {exc}")
    news = pd.DataFrame(rows)
    if news.empty:
        features = pd.DataFrame()
    else:
        tagged_rows = []
        for _, item in news.iterrows():
            text = f"{item.get('title', '')} {item.get('summary', '')}"
            constructor = _tag_constructor(text)
            season, round_number, event_name = _tag_event(text, events)
            tags = _tag_updates(text)
            tagged_rows.append(
                {
                    **item.to_dict(),
                    "season": season,
                    "round": round_number,
                    "event_name": event_name,
                    "constructor_name": constructor,
                    "published_before_qualifying": _published_before_cutoff(item.get("published_at"), events, season, round_number),
                    **tags,
                }
            )
        news = pd.DataFrame(tagged_rows)
        feature_cols = [
            "upgrade_present",
            "upgrade_scope",
            "aero_update",
            "floor_update",
            "front_wing_update",
            "rear_wing_update",
            "suspension_update",
            "cooling_update",
            "estimated_upgrade_intensity",
        ]
        features = (
            news.dropna(subset=["season", "round", "constructor_name"])
            .query("published_before_qualifying == True")
            .groupby(["season", "round", "event_name", "constructor_name"], dropna=False)[feature_cols]
            .max()
            .reset_index()
        )

    news.to_parquet(UPGRADE_NEWS_TABLE_PATH, index=False)
    features.to_parquet(UPGRADE_FEATURES_TABLE_PATH, index=False)
    metadata = {}
    if RICH_DATASET_METADATA_PATH.exists():
        metadata = json.loads(RICH_DATASET_METADATA_PATH.read_text(encoding="utf-8"))
    metadata["upgrade_news"] = {
        "built_at_utc": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "raw_version": version,
        "sources": feed_urls,
        "news_rows": int(len(news)),
        "feature_rows": int(len(features)),
        "leakage_guard": "Items are intended for pre-session use; downstream filters should enforce published_at <= qualifying or race cutoff.",
    }
    RICH_DATASET_METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Wrote {len(news):,} upgrade news rows to {UPGRADE_NEWS_TABLE_PATH}")
    print(f"Wrote {len(features):,} upgrade feature rows to {UPGRADE_FEATURES_TABLE_PATH}")
    return news, features


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest race-weekend team upgrade news from RSS/Atom feeds.")
    parser.add_argument("--feed", action="append", dest="feeds", help="RSS/Atom feed URL. Can be passed multiple times.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ingest_upgrade_news(args.feeds)


if __name__ == "__main__":
    main()
