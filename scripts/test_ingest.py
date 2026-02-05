from src.pipeline.ingest import load_events, find_match_meta

match_id = 8658
meta = find_match_meta(match_id)
events = load_events(match_id)

print(meta["home_team"]["home_team_name"], "vs", meta["away_team"]["away_team_name"])
print("events:", len(events))
print("first event keys:", events[0].keys())
