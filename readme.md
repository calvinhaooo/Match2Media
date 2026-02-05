# Match2Media: Verified Football Content Pack Pipeline

A production minded demo that converts football match events into structured social content packs using a local LLM, with reliability controls and per match quality reports.

## What it does
Given a StatsBomb `match_id`, the pipeline:
1. Loads match metadata from `matches/` and event level data from `events/<match_id>.json`
2. Extracts grounded features such as teams, final score, and key events
3. Generates a strict JSON content pack for social publishing
4. Validates structure and factual consistency, then writes a quality report

## Reliability safeguards
### 1. Structured output enforcement
The model is instructed to output JSON only and must pass Pydantic schema validation.
If parsing or schema validation fails, generation retries with the validation error as feedback.

### 2. Source grounded generation
The LLM is only allowed to use facts that exist in extracted `features`:
- teams, score
- minutes, players
- event evidence ids

The model only decides wording and tone.

### 3. Factual consistency checks
After generation, the pipeline checks:
- `team` is one of the two match teams
- `player` exists in the extracted event set
- `minute` exists in extracted key events
- `evidence.event_id` exists and is traceable to source events
The report records `factual_valid` and a list of concrete errors.

### 4. Traceability with evidence
Each key moment includes an `evidence` object referencing the original source `event_id`.
This enables auditing and debugging.

### 5. Batch visibility
Batch runs write a report for every match:
- success reports include validation results and simple stats
- failure reports include the exception message and runtime


## Data source
This demo uses the StatsBomb Open Data repository as an offline, reproducible dataset.

It reads:
- `data/raw/statsbomb-open-data/data/matches/...` for match metadata and final score
- `data/raw/statsbomb-open-data/data/events/<match_id>.json` for event level facts

## Requirements
- macOS
- Python 3.10+
- Ollama installed and running locally

## Setup

### 1. Create and activate a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies
```
pip install -r requirements.txt
```

### 3. Download Statsbomb Dataset
```
cd data/raw
git clone https://github.com/statsbomb/open-data.git statsbomb-open-data
cd ../..
```

### 4. Install ollama
```
ollama pull llama3.1:8b
# quick check
ollama run llama3.1:8b "Return JSON only: {\"ok\": true}"
```

### 5. Run the whole project

```
python scripts/run.py --n 10 --seed 42 --language en --model llama3.1:8b
```