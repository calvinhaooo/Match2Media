import json
from pathlib import Path

BASE = Path("data/raw/statsbomb-open-data/data")

def _read_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def load_events(match_id: int):
    path = BASE / "events" / f"{match_id}.json"
    return _read_json(path)

def find_match_meta(match_id: int):
    matches_dir = BASE / "matches"
    for competition_dir in matches_dir.iterdir():
        if not competition_dir.is_dir():
            continue
        for season_file in competition_dir.glob("*.json"):
            matches = _read_json(season_file)
            for m in matches:
                if m.get("match_id") == match_id:
                    return m
    raise FileNotFoundError(f"match_id {match_id} not found in matches")
