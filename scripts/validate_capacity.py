"""Validate the Capacity Monitor journal and snapshots (PIT, wall, reproducibility)."""
from __future__ import annotations
import json, sys
import capacity_common as cc

def validate(root=cc.ROOT):
    definitions,sha=cc.load_definitions(root)
    if definitions.get("method_version")!=cc.METHOD or definitions.get("scoring_use")!="none" or definitions.get("aggregate_score") is not None:
        raise ValueError("definitions must stay non-scoring with no aggregate score")
    refs=cc.weekly_refs(root); observations=cc.load_observations(root)
    n=cc.validate_journal(observations,definitions,refs)
    m=cc.validate_snapshots(cc.load_snapshots(root),definitions,sha,observations,refs)
    return n,m

if __name__=="__main__":
    try: n,m=validate(); print(f"capacity monitor validated: {n} observation(s), {m} snapshot(s)")
    except (ValueError,json.JSONDecodeError) as exc:
        print(f"capacity validation failed: {exc}",file=sys.stderr); raise SystemExit(1)
