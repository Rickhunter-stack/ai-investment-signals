"""Capacity Monitor v0.1 core: PIT observations, wall, snapshot computation.

EXPERIMENTAL - NON SCORING. Nothing here reads or writes anything used by the
weekly Signal Score except a read-only lookup of frozen weekly snapshot
metadata (captured_at, research SHA-256) used to anchor the methodological
wall. See docs/CAPACITY_MONITOR.md.
"""
from __future__ import annotations
import hashlib, json, statistics
from datetime import date, datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
METHOD="capacity_monitor_v0.1"
OBS_SCHEMA="capacity-observation-v0.1"; SNAP_SCHEMA="capacity-snapshot-v0.1"
LEVELS=("C0","C1","C2","C3","C4","C5","X","UNKNOWN")
KINDS=("project","demand","assessment")
SCRIPT_FIELDS={"schema_version","observation_id","method_version","observed_at","weekly_snapshot_date","historical_seed","frozen"}

def paths(root=ROOT):
    root=Path(root)
    return {"definitions":root/"config/capacity/definitions_capacity_monitor_v0.1.json",
            "observations":root/"data/capacity/observations","snapshots":root/"data/capacity/snapshots.json",
            "weekly":root/"data/weekly_signals.json"}

def ts(value,field):
    try: t=datetime.fromisoformat(str(value).replace("Z","+00:00"))
    except ValueError as exc: raise ValueError(f"{field} must be an ISO timestamp") from exc
    if t.tzinfo is None: raise ValueError(f"{field} must be timezone-aware")
    return t

def load_definitions(root=ROOT):
    raw=paths(root)["definitions"].read_bytes()
    return json.loads(raw),hashlib.sha256(raw).hexdigest()

def load_observations(root=ROOT):
    out=[]
    for p in sorted(paths(root)["observations"].glob("*.json")):
        rows=json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(rows,list): raise ValueError(f"{p}: capacity journal must be a JSON array")
        out.extend(rows)
    return out

def load_snapshots(root=ROOT):
    p=paths(root)["snapshots"]
    rows=json.loads(p.read_text(encoding="utf-8")) if p.exists() else []
    if not isinstance(rows,list): raise ValueError("capacity snapshots must be a JSON array")
    return rows

def weekly_refs(root=ROOT):
    """Frozen weekly Signal snapshots as (date, captured_at, research sha), read-only."""
    refs=[]
    for s in json.loads(paths(root)["weekly"].read_text(encoding="utf-8")):
        if s.get("frozen") is True and s.get("captured_at") and s.get("input_sha256",{}).get("research"):
            refs.append({"date":s["date"],"captured_at":ts(s["captured_at"],"captured_at"),"research_sha256":s["input_sha256"]["research"]})
    return sorted(refs,key=lambda r:r["captured_at"])

def wall_ref(refs,at):
    """Latest frozen weekly snapshot captured strictly before `at` (the wall)."""
    before=[r for r in refs if r["captured_at"]<at]
    if not before: raise ValueError("no frozen weekly Signal snapshot precedes this time: the methodological wall cannot be anchored")
    return before[-1]

def _url(u): return isinstance(u,str) and u.startswith(("https://","http://"))
def _num(v): return isinstance(v,(int,float)) and not isinstance(v,bool)

def validate_draft(d,definitions):
    """Content rules shared by drafts and stored observations."""
    if not isinstance(d,dict): raise ValueError("observation must be an object")
    kind=d.get("kind")
    if kind not in KINDS: raise ValueError(f"kind must be one of {KINDS}")
    src=d.get("source")
    if not isinstance(src,dict) or not _url(src.get("url")): raise ValueError("source.url must be an http(s) URL")
    if src.get("published_at") is not None: ts(src["published_at"],"source.published_at")
    if d.get("supersedes") is not None and not isinstance(d["supersedes"],str): raise ValueError("supersedes must be an observation_id or null")
    units=definitions["unit_conversions_to_canonical"]
    if kind=="project":
        for f in ("asset_id","name","asset_class","level_evidence"):
            if not isinstance(d.get(f),str) or not d[f].strip(): raise ValueError(f"project {f} is required")
        if d.get("ladder_level") not in LEVELS: raise ValueError(f"ladder_level must be one of {LEVELS}")
        cap=d.get("capacity")
        if not isinstance(cap,dict) or not _num(cap.get("value")) or cap["value"]<0 or not isinstance(cap.get("unit"),str): raise ValueError("capacity must be {value>=0, unit}")
        y=d.get("expected_operational_year")
        if y is not None and (not isinstance(y,int) or isinstance(y,bool)): raise ValueError("expected_operational_year must be an integer or null")
        for f in ("commitment_date","commissioned_at"):
            if d.get(f) is not None: date.fromisoformat(d[f])
        if d["ladder_level"]=="C5" and not d.get("commissioned_at"): raise ValueError("C5 requires commissioned_at")
        life=d.get("expected_useful_life_years")
        if life is not None and (not _num(life) or life<=0): raise ValueError("expected_useful_life_years must be > 0 or null")
        if d.get("dependencies_documented") not in (True,False): raise ValueError("dependencies_documented must be a boolean")
        if d["dependencies_documented"]:
            ev=d.get("dependency_evidence")
            if not isinstance(ev,list) or not ev or not all(_url(u) for u in ev): raise ValueError("documented dependencies require dependency_evidence URLs")
    elif kind=="demand":
        for f in ("series_id","method_note"):
            if not isinstance(d.get(f),str) or not d[f].strip(): raise ValueError(f"demand {f} is required")
        if d.get("scenario") not in definitions["absorption_stress"]["scenarios"]: raise ValueError("demand scenario must be bear/base/bull")
        if not isinstance(d.get("year"),int) or isinstance(d.get("year"),bool): raise ValueError("demand year must be an integer")
        if not _num(d.get("value")) or d["value"]<0: raise ValueError("demand value must be >= 0")
        if not isinstance(d.get("unit"),str): raise ValueError("demand unit is required")
    else:
        comp=definitions["components"].get(d.get("component"),{})
        if comp.get("type")!="qualitative": raise ValueError("assessments exist only for qualitative components (E, F)")
        if d.get("value") not in comp["scale"]: raise ValueError(f"{d['component']} value must be one of {comp['scale']}")
        for f in ("node","justification"):
            if not isinstance(d.get(f),str) or not d[f].strip(): raise ValueError(f"assessment {f} is required")
        if d["component"]=="F" and (not isinstance(d.get("relations"),list) or not d["relations"] or not all(isinstance(x,str) and x.strip() for x in d["relations"])):
            raise ValueError("F requires documented relations")
    return kind

def validate_observation(o,definitions,refs):
    validate_draft(o,definitions)
    if o.get("schema_version")!=OBS_SCHEMA or o.get("method_version")!=METHOD: raise ValueError(f"{o.get('observation_id')}: wrong schema/method version")
    if o.get("frozen") is not True or not isinstance(o.get("historical_seed"),bool): raise ValueError(f"{o.get('observation_id')}: frozen/historical_seed invalid")
    observed=ts(o["observed_at"],"observed_at")
    pub=o["source"].get("published_at")
    if pub is not None and ts(pub,"source.published_at")>observed: raise ValueError(f"{o['observation_id']}: source published after observed_at")
    ref=wall_ref(refs,observed)
    if o.get("weekly_snapshot_date")!=ref["date"]: raise ValueError(f"{o['observation_id']}: wall reference must be the weekly snapshot {ref['date']}")
    return observed

def validate_journal(observations,definitions,refs):
    seen={}; last=None
    for o in observations:
        observed=validate_observation(o,definitions,refs)
        if o["observation_id"] in seen: raise ValueError(f"duplicate observation_id {o['observation_id']}")
        if last is not None and observed<last: raise ValueError(f"{o['observation_id']}: journal must be appended in observed_at order")
        if o.get("supersedes") is not None:
            target=seen.get(o["supersedes"])
            if target is None: raise ValueError(f"{o['observation_id']}: supersedes an unknown or later observation")
            if target["kind"]!=o["kind"]: raise ValueError(f"{o['observation_id']}: supersedes an observation of another kind")
        seen[o["observation_id"]]=o; last=observed
    return len(observations)

def key(o):
    if o["kind"]=="project": return ("project",o["asset_id"])
    if o["kind"]=="demand": return ("demand",o["series_id"],o["scenario"],o["year"])
    return ("assessment",o["component"],o["node"])

def pit_state(observations,as_of):
    """What the monitor knew at as_of: latest non-superseded observation per key."""
    known=[o for o in observations if ts(o["observed_at"],"observed_at")<=as_of]
    superseded={o["supersedes"] for o in known if o.get("supersedes")}
    state={}
    for o in sorted(known,key=lambda o:(ts(o["observed_at"],"observed_at"),o["observation_id"])):
        if o["observation_id"] not in superseded: state[key(o)]=o
    return state,known

def _r(v): return None if v is None else round(v,6)

def compute(definitions,definitions_sha,observations,as_of,ref):
    """Pure, deterministic snapshot of the capacity state known at as_of."""
    as_of=ts(as_of,"as_of") if not isinstance(as_of,datetime) else as_of
    state,known=pit_state(observations,as_of)
    conv=definitions["unit_conversions_to_canonical"]; years=definitions["years"]
    projects=[o for k,o in state.items() if k[0]=="project"]
    def gw(p): return p["capacity"]["value"]*conv[p["capacity"]["unit"]] if p["capacity"]["unit"] in conv else None
    canonical=[p for p in projects if gw(p) is not None]
    def online(p): return date.fromisoformat(p["commissioned_at"]).year if p["ladder_level"]=="C5" else p.get("expected_operational_year")
    def alive(p,y):
        start=online(p); life=p.get("expected_useful_life_years")
        return start is not None and start<=y and (life is None or y<start+life)
    def effective(p): return p["ladder_level"] in definitions["operational_levels"] or (p["ladder_level"] in definitions["effective"]["eligible_future_levels"] and p["dependencies_documented"])
    sets={"announced_gw":lambda p:p["ladder_level"] in definitions["announced_levels"],
          "committed_gw":lambda p:p["ladder_level"] in definitions["committed_levels"],
          "operational_gw":lambda p:p["ladder_level"] in definitions["operational_levels"],
          "effective_gw":effective}
    buildout={}
    for y in years:
        buildout[str(y)]={name:(None if not canonical else _r(sum(gw(p) for p in canonical if test(p) and alive(p,y)))) for name,test in sets.items()}
    undated={name:_r(sum(gw(p) for p in canonical if test(p) and online(p) is None)) for name,test in sets.items()}
    demand={}; absorption={}
    series={}
    for k,o in state.items():
        if k[0]=="demand": series.setdefault((o["scenario"],o["year"]),[]).append(o)
    reference=definitions["absorption_stress"]["reference_demand_series"]
    for y in years:
        demand[str(y)]={}; absorption[str(y)]={}
        for s in definitions["absorption_stress"]["scenarios"]:
            cands=[o for o in series.get((s,y),[]) if reference is None or o["series_id"]==reference]
            value=reason=None
            if not cands: reason="no demand estimate"
            elif len(cands)>1: reason="several demand series without declared reference"
            elif cands[0]["unit"] not in conv: reason="demand unit not comparable"
            else: value=cands[0]["value"]*conv[cands[0]["unit"]]
            demand[str(y)][s]=_r(value)
            num=buildout[str(y)]["effective_gw"]
            if value is not None and num is None: reason="effective capacity unknown"
            elif value is not None and value<=0: reason="demand <= 0"
            ratio=None if reason else num/value
            absorption[str(y)][s]={"value":_r(ratio),"reason":reason}
    ladder={}
    for lvl in LEVELS:
        items=[p for p in projects if p["ladder_level"]==lvl]
        ladder[lvl]={"projects":len(items),"gw":_r(sum(gw(p) for p in items if gw(p) is not None)),"non_canonical_projects":sum(gw(p) is None for p in items)}
    delays=sorted((date.fromisoformat(p["commissioned_at"])-date.fromisoformat(p["commitment_date"])).days/30.4375
                  for p in projects if p["ladder_level"]=="C5" and p.get("commitment_date"))
    def q(v,f): return _r(statistics.quantiles(v,n=4)[f]) if len(v)>=2 else None
    assessments=lambda c:[{"node":o["node"],"value":o["value"],"justification":o["justification"],"relations":o.get("relations"),
                           "source":o["source"],"observation_id":o["observation_id"],"observed_at":o["observed_at"]}
                          for k,o in sorted(state.items()) if k[0]=="assessment" and k[1]==c]
    committed_total=_r(sum(gw(p) for p in canonical if p["ladder_level"] in definitions["committed_levels"])) if canonical else None
    operational_total=_r(sum(gw(p) for p in canonical if p["ladder_level"] in definitions["operational_levels"])) if canonical else None
    new=[o["observation_id"] for o in known if ts(o["observed_at"],"observed_at")>ref["captured_at"]]
    return {"schema_version":SNAP_SCHEMA,"snapshot_id":f"CAPSNAP-{ref['date']}-{METHOD}","method_version":METHOD,
            "status":definitions["status"],"scoring_use":"none","definitions_sha256":definitions_sha,
            "capacity_snapshot_captured_at":as_of.isoformat(),
            "weekly_snapshot_date":ref["date"],"weekly_snapshot_captured_at":ref["captured_at"].isoformat(),
            "weekly_research_sha256":ref["research_sha256"],
            "input_observation_ids":sorted(o["observation_id"] for o in known),"new_observation_ids":sorted(new),
            "counts":{"observations":len(known),"projects":len(projects),"historical_seed":sum(o["historical_seed"] for o in known)},
            "buildout":{"unit":definitions["canonical_unit"],"years":buildout,"undated":undated,
                        "depreciation_unknown_gw":_r(sum(gw(p) for p in canonical if p.get("expected_useful_life_years") is None and online(p) is not None)) if canonical else None},
            "demand":{"unit":definitions["canonical_unit"],"years":demand},"absorption_stress":absorption,"ladder":ladder,
            "system_risk":{"E":assessments("E"),
                           "C":{"committed_gw":committed_total,"operational_gw":operational_total,"by_level":{l:ladder[l]["gw"] for l in LEVELS}},
                           "T":{"realized_months":{"n":len(delays),"median":_r(statistics.median(delays)) if delays else None,"p25":q(delays,0),"p75":q(delays,2)},
                                "expected_committed_gw_by_year":{str(y):(None if not canonical else _r(sum(gw(p) for p in canonical if p["ladder_level"] in ("C3","C4") and p.get("expected_operational_year")==y))) for y in years}},
                           "D":{"from":"absorption_stress"},
                           "F":assessments("F")},
            "frozen":True}

def validate_snapshots(snapshots,definitions,definitions_sha,observations,refs):
    ids=set(); periods=set(); last=None
    by_date={r["date"]:r for r in refs}
    for s in snapshots:
        if s.get("schema_version")!=SNAP_SCHEMA or s.get("frozen") is not True or s.get("scoring_use")!="none": raise ValueError(f"{s.get('snapshot_id')}: invalid snapshot header")
        if s["snapshot_id"] in ids or (s["weekly_snapshot_date"],s["method_version"]) in periods: raise ValueError(f"{s['snapshot_id']}: one capacity snapshot per weekly period and method")
        ids.add(s["snapshot_id"]); periods.add((s["weekly_snapshot_date"],s["method_version"]))
        captured=ts(s["capacity_snapshot_captured_at"],"capacity_snapshot_captured_at")
        if last is not None and captured<=last: raise ValueError(f"{s['snapshot_id']}: snapshots must be appended in time order")
        last=captured
        ref=by_date.get(s["weekly_snapshot_date"])
        if ref is None or ref["research_sha256"]!=s["weekly_research_sha256"] or ref["captured_at"].isoformat()!=s["weekly_snapshot_captured_at"]:
            raise ValueError(f"{s['snapshot_id']}: wall reference does not match a frozen weekly snapshot")
        if wall_ref(refs,captured)["date"]!=ref["date"]: raise ValueError(f"{s['snapshot_id']}: must reference the latest weekly snapshot frozen before it")
        if s["method_version"]==METHOD:
            if s["definitions_sha256"]!=definitions_sha: raise ValueError(f"{s['snapshot_id']}: definitions changed after use")
            if compute(definitions,definitions_sha,observations,captured,ref)!=s: raise ValueError(f"{s['snapshot_id']}: not reproducible from the PIT journal")
    return len(snapshots)
