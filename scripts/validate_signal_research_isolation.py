"""Session separation guard: signal_research.json may never use Capacity Monitor outputs.

A primary source may appear independently in both researches; citing the
Capacity Monitor artefacts or analysis as a scoring source or context may not.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; RESEARCH=ROOT/"data/signal_research.json"
FORBIDDEN_URL=("/data/capacity","capacity_monitor","ai-investment-signals")
FORBIDDEN_TEXT=("capacity_monitor","capacity monitor","absorption stress","commitment ladder","e-c-t-d-f")

def violations(research):
    out=[]
    for ticker,entry in research.items():
        for component,item in (entry or {}).items():
            if not isinstance(item,dict): continue
            for url in item.get("sources") or []:
                if any(f in str(url).lower() for f in FORBIDDEN_URL): out.append(f"{ticker}.{component}: source {url}")
            text=str(item.get("rationale","")).lower()
            for f in FORBIDDEN_TEXT:
                if f in text: out.append(f"{ticker}.{component}: rationale mentions {f!r}")
    return out

if __name__=="__main__":
    found=violations(json.loads(RESEARCH.read_text(encoding="utf-8")))
    if found:
        print("signal_research isolation failed:\n"+"\n".join(found),file=sys.stderr); raise SystemExit(1)
    print("signal_research isolation verified")
