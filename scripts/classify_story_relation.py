#!/usr/bin/env python3
"""Classify a new brief event against frozen history without rewriting it.

This is deliberately deterministic and explainable. It proposes a story_id and
relation; the caller remains responsible for writing the new frozen event.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

RELATIONS = {"NEW", "REPEAT", "CONFIRM", "ACCELERATE", "DETERIORATE", "CONTRADICT", "RESOLVE"}
STOP = {"the","and","for","with","dans","les","des","une","pour","sur","aux","est","sont","de","la","le","un","en","et","du"}


def tokens(event):
    text = " ".join(str(event.get(k, "")) for k in ("title", "factual_summary", "theme", "subtheme", "sector"))
    return {x for x in re.findall(r"[a-z0-9]+", text.lower()) if len(x) > 2 and x not in STOP}


def similarity(a, b):
    ta, tb = tokens(a), tokens(b)
    lexical = len(ta & tb) / max(1, len(ta | tb))
    tick_a, tick_b = set(a.get("tickers", [])), set(b.get("tickers", []))
    company_a, company_b = set(a.get("companies", [])), set(b.get("companies", []))
    entity = 1.0 if tick_a & tick_b else (0.6 if company_a & company_b else 0.0)
    theme = 1.0 if a.get("subtheme") == b.get("subtheme") else (0.5 if a.get("theme") == b.get("theme") else 0.0)
    return 0.50 * lexical + 0.30 * entity + 0.20 * theme


def proposed_relation(new, old):
    # Relation is conservative: semantic similarity identifies a story, while
    # direction/materiality changes classify its evolution.
    if new.get("direction") != old.get("direction") and "neutral" not in {new.get("direction"), old.get("direction")}:
        return "CONTRADICT"
    ni, oi = new.get("importance", 0), old.get("importance", 0)
    if ni >= oi + 15:
        return "ACCELERATE"
    if ni <= oi - 15:
        return "DETERIORATE"
    if similarity(new, old) >= 0.72 and abs(ni - oi) <= 5:
        return "REPEAT"
    return "CONFIRM"


def classify(new, history):
    candidates = [(similarity(new, old), old) for old in history if old.get("frozen") is True]
    candidates.sort(key=lambda x: x[0], reverse=True)
    if not candidates or candidates[0][0] < 0.34:
        return {"story_id": None, "relation": "NEW", "matched_event_id": None, "similarity": round(candidates[0][0], 3) if candidates else 0.0}
    score, old = candidates[0]
    story = old.get("story") or {}
    story_id = story.get("story_id") or f"STORY-{old['event_id']}"
    return {"story_id": story_id, "relation": proposed_relation(new, old), "matched_event_id": old.get("event_id"), "similarity": round(score, 3)}


def load_history(path: Path):
    if path.is_dir():
        history = []
        for journal in sorted(path.glob("*.json")):
            payload = json.loads(journal.read_text(encoding="utf-8"))
            if not isinstance(payload, list):
                raise ValueError(f"{journal}: journal must be an array")
            history.extend(payload)
        return history
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("history must be an array")
    return payload


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: classify_story_relation.py NEW_EVENT.json HISTORY.json|JOURNAL_DIR")
    new = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    history = load_history(Path(sys.argv[2]))
    print(json.dumps(classify(new, history), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
