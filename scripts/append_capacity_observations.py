"""Append Capacity Monitor observations (Session B only, after the weekly freeze).

Two mandatory steps, see docs/CAPACITY_MONITOR.md:

  1. --check  validates the drafts, prints a project-by-project report and the
              simulated snapshot, writes nothing, and prints a digest;
              exit 1 on any blocking error, 0 when only warnings remain.
  2. --checked DIGEST  performs the real append; refused unless the digest
              matches the exact drafts, seed flag and journal state checked.

The script sets observed_at (now, never backdated), the wall reference, ids and
versions. Drafts may not carry them.
"""
from __future__ import annotations
import argparse, hashlib, json, sys
sys.dont_write_bytecode=True   # --check must leave the repository byte-identical
from datetime import datetime, timezone
from pathlib import Path
import capacity_common as cc

STATUS={"C0":"announced","C1":"announced","C2":"announced","C3":"committed","C4":"committed","C5":"operational","X":"cancelled","UNKNOWN":"unknown"}

def digest(drafts,historical_seed,existing):
    state={"drafts":drafts,"historical_seed":bool(historical_seed),"journal":[o["observation_id"] for o in existing]}
    return hashlib.sha256(json.dumps(state,sort_keys=True,ensure_ascii=False).encode()).hexdigest()[:16]

def prepare(drafts,root=cc.ROOT,now=None,historical_seed=False):
    """Build the rows the append would write, collecting every blocking error."""
    if not isinstance(drafts,list) or not drafts: raise ValueError("expected a non-empty JSON array of observation drafts")
    definitions,sha=cc.load_definitions(root); refs=cc.weekly_refs(root)
    now=(now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    ref=cc.wall_ref(refs,now)
    existing=cc.load_observations(root)
    errors=[]
    if existing and cc.ts(existing[-1]["observed_at"],"observed_at")>now: errors.append("journal already holds a later observation")
    day=now.strftime("%Y%m%d"); n=sum(o["observation_id"].startswith(f"CAP-{day}-") for o in existing)
    rows=[]
    for i,d in enumerate(drafts,1):
        try:
            if not isinstance(d,dict): raise ValueError("each draft must be an object")
            forbidden=cc.SCRIPT_FIELDS&set(d)
            if forbidden: raise ValueError(f"drafts may not set {sorted(forbidden)}")
            cc.validate_draft(d,definitions)
            pub=d["source"].get("published_at")
            if pub is not None and cc.ts(pub,"source.published_at")>now: raise ValueError("source.published_at is in the future")
        except (ValueError,TypeError,KeyError,AttributeError) as exc:
            errors.append(f"draft #{i}: {exc}"); continue
        n+=1
        rows.append({"schema_version":cc.OBS_SCHEMA,"observation_id":f"CAP-{day}-{n:04d}","method_version":cc.METHOD,
                     **d,"observed_at":now.isoformat(),"weekly_snapshot_date":ref["date"],
                     "historical_seed":bool(historical_seed),"frozen":True})
    if not errors:
        try: cc.validate_journal(existing+rows,definitions,refs)
        except ValueError as exc: errors.append(str(exc))
    return {"definitions":definitions,"sha":sha,"refs":refs,"ref":ref,"now":now,"existing":existing,"rows":rows,"errors":errors,
            "digest":digest(drafts,historical_seed,existing)}

def warnings_for(rows,existing,definitions):
    """Non-blocking: information legitimately UNKNOWN/null, or excluded from sums."""
    conv=definitions["unit_conversions_to_canonical"]; out={}
    def warn(r,msg): out.setdefault(r["observation_id"],[]).append(msg)
    seen={}
    for r in rows:
        if r["kind"]=="project":
            lvl=r["ladder_level"]
            if r["capacity"]["unit"] not in conv: warn(r,f"unité {r['capacity']['unit']} hors GW_IT/MW_IT : exclue des sommes (null si seule)")
            if lvl=="UNKNOWN": warn(r,"niveau UNKNOWN : compté dans l'échelle, exclu d'announced/committed/effective")
            if lvl=="X": warn(r,"projet annulé (X) : conservé dans l'historique, exclu des capacités")
            if lvl not in ("C5","X","UNKNOWN") and r.get("expected_operational_year") is None: warn(r,"pas d'expected_operational_year : capacité non datée, absente des millésimes")
            if lvl in ("C3","C4") and not r["dependencies_documented"]: warn(r,"dépendances non documentées : committed mais pas effective")
            if lvl=="C5" and r.get("expected_useful_life_years") is None: warn(r,"durée de vie inconnue : jamais retirée (depreciation_unknown_gw)")
            if lvl=="C5" and not r.get("commitment_date"): warn(r,"C5 sans commitment_date : exclu du délai T réalisé")
            if r["asset_id"] in seen: warn(r,f"asset_id déjà présent dans ce lot (#{seen[r['asset_id']]}) : la dernière ligne l'emporte")
            seen[r["asset_id"]]=r["observation_id"]
        elif r["kind"]=="demand" and r["unit"] not in conv: warn(r,f"unité {r['unit']} hors GW_IT/MW_IT : AS null")
        if r["source"].get("published_at") is None: warn(r,"source.published_at absent (date de publication inconnue)")
    state,_=cc.pit_state(existing+rows,max(cc.ts(r["observed_at"],"observed_at") for r in rows))
    series={}
    for k,o in state.items():
        if k[0]=="demand": series.setdefault((o["scenario"],o["year"]),set()).add(o["series_id"])
    for (s,y),ids in sorted(series.items()):
        if len(ids)>1 and definitions["absorption_stress"]["reference_demand_series"] is None:
            for r in rows:
                if r["kind"]=="demand" and (r["scenario"],r["year"])==(s,y): warn(r,f"{len(ids)} séries de demande pour {s} {y} sans référence déclarée : AS null")
    return out

def _v(x,d=3): return "null" if x is None else f"{x:.{d}f}".rstrip("0").rstrip(".")

def check(drafts,root=cc.ROOT,now=None,historical_seed=False):
    """Validate and simulate without writing anything. Returns (exit_code, report)."""
    p=prepare(drafts,root,now,historical_seed)
    lines=[f"CAPACITY CHECK · {cc.METHOD} · aucun fichier écrit",
           f"Mur : freeze Signal {p['ref']['date']} (captured_at {p['ref']['captured_at'].isoformat()})",
           f"Brouillons : {len(drafts)} · journal existant : {len(p['existing'])} · historical_seed={bool(historical_seed)}"]
    if p["errors"]:
        lines+=["","ERREURS BLOQUANTES :"]+[f"  ✗ {e}" for e in p["errors"]]+["","Aucune écriture possible : corriger les brouillons puis relancer --check."]
        return 1,"\n".join(lines)
    conv=p["definitions"]["unit_conversions_to_canonical"]; warns=warnings_for(p["rows"],p["existing"],p["definitions"])
    lines+=["","PROJETS"]
    for r in [r for r in p["rows"] if r["kind"]=="project"]:
        gw=r["capacity"]["value"]*conv[r["capacity"]["unit"]] if r["capacity"]["unit"] in conv else None
        vint=r["commissioned_at"][:4] if r["ladder_level"]=="C5" else (r.get("expected_operational_year") or "non daté")
        lines.append(f"  {r['observation_id']} {r['asset_id']} · {r['ladder_level']} ({STATUS[r['ladder_level']]}) · "
                     f"{r['capacity']['value']} {r['capacity']['unit']} = {_v(gw)} GW_IT / {_v(None if gw is None else gw*1000,1)} MW_IT · millésime {vint}"
                     + (" · dépendances documentées" if r["dependencies_documented"] else ""))
        lines.append(f"      preuve : {r['level_evidence']}")
        lines.append(f"      source : {r['source']['url']} (publiée {r['source'].get('published_at') or 'inconnue'})")
    others=[r for r in p["rows"] if r["kind"]!="project"]
    if others: lines+=["","DEMANDE / ÉVALUATIONS"]
    for r in others:
        if r["kind"]=="demand": lines.append(f"  {r['observation_id']} demande {r['scenario']} {r['year']} · {r['value']} {r['unit']} · série {r['series_id']} · {r['source']['url']}")
        else: lines.append(f"  {r['observation_id']} {r['component']} {r['node']} = {r['value']} · {r['source']['url']}")
    nwarn=sum(len(v) for v in warns.values())
    lines+=["",f"AVERTISSEMENTS ({nwarn}, non bloquants)"]+[f"  ! {oid} : {m}" for oid,ms in warns.items() for m in ms]
    snap=cc.compute(p["definitions"],p["sha"],p["existing"]+p["rows"],p["now"],p["ref"])
    lines+=["","SNAPSHOT SIMULÉ (rien n'est figé ; null = inconnu, jamais estimé)","  Échelle : "+" · ".join(
        f"{l} {v['projects']}p/{_v(v['gw'])}GW"+(f" (+{v['non_canonical_projects']} hors unité)" if v["non_canonical_projects"] else "") for l,v in snap["ladder"].items())]
    lines.append("  Millésime   announced  committed  operational  effective")
    for y,b in snap["buildout"]["years"].items():
        lines.append(f"  {y}        {_v(b['announced_gw']):>9}  {_v(b['committed_gw']):>9}  {_v(b['operational_gw']):>11}  {_v(b['effective_gw']):>9}")
    lines.append("  AS (bear / base / bull)")
    for y,a in snap["absorption_stress"].items():
        lines.append(f"  {y}  "+" / ".join(f"{_v(a[s]['value'])}" + (f" [{a[s]['reason']}]" if a[s]["reason"] else "") for s in ("bear","base","bull")))
    lines+=["",f"OK : aucune erreur bloquante. Écriture réelle :",
            f"  python scripts/append_capacity_observations.py <drafts.json>{' --historical-seed' if historical_seed else ''} --checked {p['digest']}"]
    return 0,"\n".join(lines)

def append(drafts,root=cc.ROOT,now=None,historical_seed=False,checked=None):
    p=prepare(drafts,root,now,historical_seed)
    if checked!=p["digest"]: raise ValueError("run --check first: the --checked digest does not match these drafts, seed flag and journal state")
    if p["errors"]: raise ValueError("; ".join(p["errors"]))
    rows=p["rows"]
    path=cc.paths(root)["observations"]/f"{p['now'].strftime('%Y-%m')}.json"
    previous=json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    tmp=path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(previous+rows,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8"); tmp.replace(path)
    saved=json.loads(path.read_text(encoding="utf-8"))
    if saved[:len(previous)]!=previous or saved[len(previous):]!=rows: raise ValueError("post-write verification failed")
    return rows

def main():
    p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("drafts",type=Path,help="JSON array of observation drafts")
    p.add_argument("--historical-seed",action="store_true",help="bootstrap data collected before the module existed; observed_at stays the ingestion time")
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check",action="store_true",help="validate, report and simulate; writes nothing")
    mode.add_argument("--checked",metavar="DIGEST",help="digest printed by a clean --check; performs the real append")
    p.add_argument("--root",type=Path,default=cc.ROOT,help=argparse.SUPPRESS)
    a=p.parse_args()
    drafts=json.loads(a.drafts.read_text(encoding="utf-8"))
    if a.check:
        code,report=check(drafts,a.root,historical_seed=a.historical_seed); print(report); raise SystemExit(code)
    rows=append(drafts,a.root,historical_seed=a.historical_seed,checked=a.checked)
    print(f"Appended {len(rows)} capacity observation(s) behind weekly snapshot {rows[0]['weekly_snapshot_date']}")
if __name__=="__main__":
    try: main()
    except (ValueError,json.JSONDecodeError) as exc:
        print(f"capacity append failed: {exc}",file=sys.stderr); raise SystemExit(1)
