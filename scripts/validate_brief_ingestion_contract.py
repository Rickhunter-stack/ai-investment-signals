"""Smoke-check files required before activating daily ChatGPT ingestion."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REQUIRED=[ROOT/"schemas/brief_event_v1.schema.json",ROOT/"scripts/validate_brief_events.py",ROOT/"scripts/ingest_brief_events.py",ROOT/"docs/DAILY_BRIEF_EVENT_PROMPT.md"]
missing=[str(p.relative_to(ROOT)) for p in REQUIRED if not p.exists()]
if missing: raise SystemExit("missing brief ingestion contract files: "+", ".join(missing))
print("Brief ingestion contract ready")
