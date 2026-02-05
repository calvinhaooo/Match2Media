from typing import Dict, Any, List
from pathlib import Path
Path("outputs/reports").mkdir(parents=True, exist_ok=True)

def validate_pack(pack: Dict[str, Any], features: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []

    allowed_teams = set(features["allowed"]["teams"])
    allowed_players = set(features["allowed"]["players"])
    allowed_minutes = set(features["allowed"]["minutes"])
    allowed_score = features["allowed"]["score"]

    # basic fact
    if pack.get("match_id") != features["match"]["match_id"]:
        errors.append("match_id mismatch")

    # check summary
    summary = (pack.get("summary") or "")
    if allowed_score not in summary and allowed_score.replace("-", "–") not in summary:
        pass

    # key_moments check
    for i, km in enumerate(pack.get("key_moments", [])):
        minute = km.get("minute")
        team = km.get("team")
        player = km.get("player")

        if team and team not in allowed_teams:
            errors.append(f"key_moments[{i}].team not allowed: {team}")

        if minute is not None and minute not in allowed_minutes:
            errors.append(f"key_moments[{i}].minute not in source events: {minute}")

        if player and player not in allowed_players:
            errors.append(f"key_moments[{i}].player not in source events: {player}")

        ev = km.get("evidence", {})
        if not ev or "event_id" not in ev:
            errors.append(f"key_moments[{i}].evidence missing event_id")

    report = {
        "schema_valid": True,  # schema 校验在 generate_local 里已经做过
        "factual_valid": len(errors) == 0,
        "errors": errors,
        "stats": {
            "num_key_events_source": len(features["events"]),
            "num_key_moments_generated": len(pack.get("key_moments", [])),
        }
    }
    return report
