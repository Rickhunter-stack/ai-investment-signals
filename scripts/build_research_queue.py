"""Build a deterministic research queue from the latest frozen weekly snapshot.

The queue is advisory only. It never writes signal_research.json or weekly scores.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = ("novelty", "pricing_headroom", "execution_risk")


def build(root=ROOT):
    history = json.loads((root / "data/weekly_signals.json").read_text())
    if not history:
        return {"schema_version": "research-queue-v1", "snapshot_date": None, "items": []}
    latest = history[-1]
    brief_dir = root / "data/brief_events"
    recent_tickers = {}
    if brief_dir.exists():
        for path in sorted(brief_dir.glob("*.json")):
            try:
                events = json.loads(path.read_text())
            except Exception:
                continue
            if not isinstance(events, list):
                continue
            for event in events:
                for ticker in event.get("tickers") or []:
                    recent_tickers[ticker] = recent_tickers.get(ticker, 0) + 1
    items = []
    for ticker, score in latest["scores"].items():
        missing = [c for c in COMPONENTS if score.get(c) is None]
        if not missing:
            continue
        # Missing research is the primary need; recent brief evidence breaks ties.
        priority = len(missing) * 10 + min(recent_tickers.get(ticker, 0), 9)
        items.append({
            "ticker": ticker,
            "missing_research": missing,
            "recent_brief_events": recent_tickers.get(ticker, 0),
            "priority": priority,
            "reason": "Missing qualitative research components in latest frozen snapshot",
        })
    items.sort(key=lambda x: (-x["priority"], x["ticker"]))
    return {"schema_version": "research-queue-v1", "snapshot_date": latest["date"], "items": items}


def main():
    payload = build()
    target = ROOT / "data/research_queue.json"
    target.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"{target}: {len(payload['items'])} queued tickers")


if __name__ == "__main__":
    main()
