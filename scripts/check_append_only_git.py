#!/usr/bin/env python3
"""Fail CI when a frozen/append-only research file rewrites its git-base history."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def git_bytes(ref: str, path: str) -> bytes | None:
    proc = subprocess.run(
        ["git", "show", f"{ref}:{path}"], cwd=ROOT, capture_output=True, check=False
    )
    return proc.stdout if proc.returncode == 0 else None


def load(raw: bytes, path: str):
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON: {exc}") from exc


def assert_list_prefix(previous, current, path):
    if not isinstance(previous, list) or not isinstance(current, list):
        raise ValueError(f"{path}: append-only journal must be a JSON array")
    if len(current) < len(previous) or current[: len(previous)] != previous:
        raise ValueError(f"{path}: historical entries were changed or removed")


def check_file(base_ref: str, path: str):
    current_path = ROOT / path
    if not current_path.exists():
        previous = git_bytes(base_ref, path)
        if previous is not None:
            raise ValueError(f"{path}: append-only file was deleted")
        return
    previous_raw = git_bytes(base_ref, path)
    if previous_raw is None:
        return  # New journal is allowed.
    previous = load(previous_raw, path)
    current = load(current_path.read_bytes(), path)
    assert_list_prefix(previous, current, path)


def tracked_paths(base_ref: str):
    paths = {"data/weekly_signals.json"}
    proc = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", base_ref, "data/brief_events"],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    if proc.returncode == 0:
        paths.update(p for p in proc.stdout.splitlines() if p.endswith(".json"))
    current_dir = ROOT / "data/brief_events"
    if current_dir.exists():
        paths.update(str(p.relative_to(ROOT)).replace("\\", "/") for p in current_dir.glob("*.json"))
    # brief_memory is only protected if it is actually an append-only array. Current
    # object-shaped operational memory is intentionally excluded until migrated.
    return sorted(paths)


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: check_append_only_git.py BASE_REF")
    base_ref = sys.argv[1]
    for path in tracked_paths(base_ref):
        check_file(base_ref, path)
    print(f"Append-only history verified against {base_ref}")


if __name__ == "__main__":
    try:
        main()
    except ValueError as exc:
        print(f"append-only integrity failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
