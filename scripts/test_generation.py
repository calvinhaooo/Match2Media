import json
from pathlib import Path
from src.pipeline.generate_local import generate_content_pack_local

match_id = 8658

with open(f"data/processed/features_{match_id}.json", "r", encoding="utf-8") as f:
    features = json.load(f)

pack = generate_content_pack_local(features, language="en", model="llama3.1:8b")

Path("outputs/packs").mkdir(parents=True, exist_ok=True)
with open(f"outputs/packs/match_{match_id}.json", "w", encoding="utf-8") as f:
    json.dump(pack, f, ensure_ascii=False, indent=2)

print("saved:", f"outputs/packs/match_{match_id}.json")
print("titles:", pack["titles"])
print("captions platforms:", [c["platform"] for c in pack["captions"]])
print("num key_moments:", len(pack["key_moments"]))
