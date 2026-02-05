import argparse
import json
import random
import time
from pathlib import Path

from src.pipeline.ingest import find_match_meta, load_events
from src.pipeline.features import build_features
from src.pipeline.generate_local import generate_content_pack_local
from src.pipeline.validate import validate_pack


def load_all_match_ids():
    base = Path("data/raw/statsbomb-open-data/data/matches")
    all_ids = []

    for comp_dir in base.iterdir():
        if not comp_dir.is_dir():
            continue
        for season_file in comp_dir.glob("*.json"):
            with season_file.open("r", encoding="utf-8") as f:
                matches = json.load(f)
            for m in matches:
                mid = m.get("match_id")
                if mid is not None:
                    all_ids.append(mid)

    return list(set(all_ids))


def ensure_dirs():
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    Path("outputs/packs").mkdir(parents=True, exist_ok=True)
    Path("outputs/reports").mkdir(parents=True, exist_ok=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=10)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--language", type=str, default="en")
    p.add_argument("--model", type=str, default="llama3.1:8b")
    args = p.parse_args()

    ensure_dirs()

    all_ids = load_all_match_ids()
    if len(all_ids) < args.n:
        raise RuntimeError(f"Only found {len(all_ids)} matches, cannot sample {args.n}.")

    random.seed(args.seed)
    sample_ids = random.sample(all_ids, args.n)

    summary = {
        "n": args.n,
        "seed": args.seed,
        "model": args.model,
        "language": args.language,
        "match_ids": sample_ids,
        "results": [],
    }

    for idx, mid in enumerate(sample_ids, start=1):
        t0 = time.time()
        status = {"match_id": mid, "ok": False}

        try:
            meta = find_match_meta(mid)
            events = load_events(mid)
            features = build_features(mid, meta, events)

            with open(f"data/processed/features_{mid}.json", "w", encoding="utf-8") as f:
                json.dump(features, f, ensure_ascii=False, indent=2)

            pack = generate_content_pack_local(features, language=args.language, model=args.model)

            with open(f"outputs/packs/match_{mid}.json", "w", encoding="utf-8") as f:
                json.dump(pack, f, ensure_ascii=False, indent=2)

            report = validate_pack(pack, features)
            report["generation_seconds"] = round(time.time() - t0, 2)

            with open(f"outputs/reports/report_{mid}.json", "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            m = features.get("match", {})
            status.update({
                "ok": True,
                "home": m.get("home_team"),
                "away": m.get("away_team"),
                "score": m.get("final_score"),
                "num_source_key_events": len(features.get("events", [])),
                "num_generated_key_moments": len(pack.get("key_moments", [])),
                "factual_valid": report.get("factual_valid"),
                "generation_seconds": report.get("generation_seconds"),
            })

            print(f"[{idx}/{args.n}] OK match_id={mid} factual={status['factual_valid']}")

        except Exception as e:
            err_report = {
                "match_id": mid,
                "ok": False,
                "error": str(e),
                "generation_seconds": round(time.time() - t0, 2),
            }
            with open(f"outputs/reports/report_{mid}.json", "w", encoding="utf-8") as f:
                json.dump(err_report, f, ensure_ascii=False, indent=2)

            status.update(err_report)
            print(f"[{idx}/{args.n}] FAIL match_id={mid} error={e}")

        summary["results"].append(status)

    ts = int(time.time())
    out_path = f"outputs/reports/random_batch_{ts}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("batch saved:", out_path)


if __name__ == "__main__":
    main()
