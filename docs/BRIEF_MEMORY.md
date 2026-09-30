# Weekly brief memory

`data/brief_memory.json` is the archive read by the dashboard "Ouvrir archives" panel (`fundamentals.js`) and by chart markers (`markers.js`). It is an append-only JSON array of weekly briefs. It is separate from `data/brief_events/`, which holds the structured daily events.

## Write path

A brief is archived only after the user has **explicitly validated it**. Nothing is archived when a brief is generated, and entries are never typed in by hand.

1. The session that wrote the brief presents it to the user.
2. The user explicitly approves it.
3. That same session writes the entry to a JSON file and runs:

   ```
   python scripts/append_brief_memory.py entry.json --user-validated-at <ISO timestamp of the approval>
   ```

4. It commits `data/brief_memory.json` through a pull request. The `research-integrity` check validates the file and enforces append-only history.

The entry contains `date`, `summary`, `stance`, `themes`, `tickers`, `watch_next`, `invalidation` and `frozen: true`. The script adds the provenance fields `validation: "explicit_user_approval"`, `validated_at` and `archived_at` (the time of writing); the entry itself may not set them.

## Rules

Enforced by `scripts/validate_brief_memory.py`, `scripts/append_brief_memory.py` and `scripts/check_append_only_git.py`:

- Existing entries are never edited, deleted or reordered.
- One entry per brief date. Dates are strictly increasing, so no brief is inserted before an existing one.
- **No backfill.** Only briefs dated on or after 2026-09-30 can be archived.
- The two entries archived by hand before this protocol (2026-09-11 and 2026-09-20) stay frozen as they are. They are the only entries allowed without validation provenance.
- `validated_at` must be timezone-aware, not earlier than the brief date and not in the future. `archived_at` must not precede `validated_at`.
- After writing, the script re-reads the file and checks that the earlier entries are unchanged and the new entry is present.

This layer does not modify `weekly_signals.json`, `signal_research.json`, the market journal or the outcomes.
