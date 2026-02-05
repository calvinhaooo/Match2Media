import json
from src.pipeline.ingest import load_events, find_match_meta
from src.pipeline.features import build_features

match_id = 8658
meta = find_match_meta(match_id)
events = load_events(match_id)
features = build_features(match_id, meta, events)

print("key events:", len(features["events"]))
print(features["events"][:3])

with open(f"data/processed/features_{match_id}.json", "w", encoding="utf-8") as f:
    json.dump(features, f, ensure_ascii=False, indent=2)
