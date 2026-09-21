#!/usr/bin/env python3
"""Fail CI when a frozen/append-only research file rewrites its git-base history."""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def git_bytes(ref: str, path: str) -> bytes | None:
    proc=subprocess.run(['git','show',f'{ref}:{path}'],cwd=ROOT,capture_output=True,check=False)
    return proc.stdout if proc.returncode==0 else None

def load(raw: bytes,path: str):
    try: return json.loads(raw)
    except json.JSONDecodeError as exc: raise ValueError(f'{path}: invalid JSON: {exc}') from exc

def assert_list_prefix(previous,current,path):
    if not isinstance(previous,list) or not isinstance(current,list): raise ValueError(f'{path}: append-only journal must be a JSON array')
    if len(current)<len(previous) or current[:len(previous)]!=previous: raise ValueError(f'{path}: historical entries were changed or removed')

def check_file(base_ref,path):
    current_path=ROOT/path
    if not current_path.exists():
        if git_bytes(base_ref,path) is not None: raise ValueError(f'{path}: append-only file was deleted')
        return
    previous_raw=git_bytes(base_ref,path)
    if previous_raw is None: return
    assert_list_prefix(load(previous_raw,path),load(current_path.read_bytes(),path),path)

def journal_paths(base_ref,directory):
    paths=set()
    proc=subprocess.run(['git','ls-tree','-r','--name-only',base_ref,directory],cwd=ROOT,capture_output=True,text=True,check=False)
    if proc.returncode==0: paths.update(p for p in proc.stdout.splitlines() if p.endswith('.json'))
    current=ROOT/directory
    if current.exists(): paths.update(str(p.relative_to(ROOT)).replace('\\','/') for p in current.glob('*.json'))
    return paths

def tracked_paths(base_ref):
    paths={'data/weekly_signals.json','data/outcomes_v1.json'}
    paths.update(journal_paths(base_ref,'data/brief_events'))
    paths.update(journal_paths(base_ref,'data/fundamentals_pit'))
    paths.update(journal_paths(base_ref,'data/market_pit'))
    return sorted(paths)

def main():
    if len(sys.argv)!=2: raise SystemExit('usage: check_append_only_git.py BASE_REF')
    for path in tracked_paths(sys.argv[1]): check_file(sys.argv[1],path)
    print(f'Append-only history verified against {sys.argv[1]}')
if __name__=='__main__':
    try: main()
    except ValueError as exc:
        print(f'append-only integrity failed: {exc}',file=sys.stderr); raise SystemExit(1)
