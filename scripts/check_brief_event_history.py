"""CI guard: compare brief-event journals with the merge base and reject history edits."""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
from validate_brief_events import DATA_DIR, validate_append_only, validate_journal


def git_show(ref, path):
    proc=subprocess.run(["git","show",f"{ref}:{path.as_posix()}"],capture_output=True,text=True)
    if proc.returncode!=0: return []
    return json.loads(proc.stdout)


def main():
    base=sys.argv[1] if len(sys.argv)>1 else "HEAD^"
    for path in sorted(DATA_DIR.glob("????-??.json")):
        current=json.loads(path.read_text(encoding="utf-8")); validate_journal(current)
        previous=git_show(base,path); validate_append_only(previous,current)
    print(f"Brief-event history is append-only against {base}")

if __name__=="__main__": main()
