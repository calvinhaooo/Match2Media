import json
from src.pipeline.validate import validate_pack

match_id = 8658
with open(f"data/processed/features_{match_id}.json", "r", encoding="utf-8") as f:
    features = json.load(f)

with open(f"outputs/packs/match_{match_id}.json", "r", encoding="utf-8") as f:
    pack = json.load(f)

report = validate_pack(pack, features)
print(report)

with open(f"outputs/reports/report_{match_id}.json", "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
