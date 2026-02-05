from typing import Dict, List, Any
from pathlib import Path
Path("data/processed").mkdir(parents=True, exist_ok=True)

def build_features(match_id: int, meta: Dict[str, Any], events: List[Dict[str, Any]]) -> Dict[str, Any]:
    home = meta["home_team"]["home_team_name"]
    away = meta["away_team"]["away_team_name"]

    # extract goals cards penalties (key events)
    key_events = []
    for e in events:
        etype = e.get("type", {}).get("name")
        minute = e.get("minute")
        team = e.get("team", {}).get("name")
        player = e.get("player", {}).get("name")

        if etype in {"Shot", "Foul Committed"}:
            # Goal event
            if etype == "Shot":
                outcome = e.get("shot", {}).get("outcome", {}).get("name")
                if outcome == "Goal":
                    key_events.append({
                        "minute": minute,
                        "team": team,
                        "player": player,
                        "event_type": "goal",
                        "evidence": {"event_id": e.get("id"), "type": etype}
                    })
            # penalties
            if etype == "Foul Committed":
                card = e.get("foul_committed", {}).get("card", {}).get("name")
                if card in {"Red Card", "Second Yellow"}:
                    key_events.append({
                        "minute": minute,
                        "team": team,
                        "player": player,
                        "event_type": "red_card",
                        "evidence": {"event_id": e.get("id"), "type": etype, "card": card}
                    })

    score = f"{meta.get('home_score')}-{meta.get('away_score')}"

    features = {
        "match": {
            "match_id": match_id,
            "home_team": home,
            "away_team": away,
            "final_score": score,
            "competition": meta.get("competition", {}).get("competition_name"),
            "season": meta.get("season", {}).get("season_name"),
            "match_date": meta.get("match_date"),
        },
        "events": key_events,
        "allowed": {
            "teams": [home, away],
            "players": sorted({ke["player"] for ke in key_events if ke.get("player")}),
            "minutes": sorted({ke["minute"] for ke in key_events if ke.get("minute") is not None}),
            "score": score,
        }
    }
    return features
