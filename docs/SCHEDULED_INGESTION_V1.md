# Scheduled ingestion v1 (Claude Code)

Division of labour:

- **ChatGPT** keeps the editorial role: daily watch and selection of the five signals (`UNIFIED_DAILY_BRIEF_V1.md`).
- **A scheduled Claude Code routine** does the mechanical, auditable part: T0 retrieval/validation, event generation with the repository scripts, tests, append-only check, pull request, and merge only when everything is green.

This document is the contract between the two. `DAILY_BRIEF_INGESTION.md` and `STORY_DEDUP_V1.md` remain authoritative for event integrity.

## Handoff: the brief issue

After producing the brief, ChatGPT opens one GitHub issue in this repository:

- title: `Brief YYYY-MM-DD` (date of the brief, Europe/Paris);
- body: the brief as plain text, with for each selected item its title, its FACT / WEAK_SIGNAL / HYPOTHESIS lines and the source URL(s).

ChatGPT never writes journal files. The routine never invents an item that is not in the issue.

## Schedule

Daily at 09:30 Europe/Paris. If no open `Brief YYYY-MM-DD` issue exists for the day, the routine stops without writing anything and reports it.

## T0 (`published_at`) rules

1. **Never infer a T0.** No estimation from a URL slug, a syndication date, the brief time or "earlier than captured_at".
2. Accepted T0 sources, in order:
   1. the original article page's first-publication timestamp (`datePublished` metadata or the first timestamp under the headline, never "Updated"/`dateModified`);
   2. a primary source (company press release, central-bank page) showing an explicit time and time zone for the same announcement, added to `sources`.
3. **Google News RSS is discovery only.** Its `pubDate` may reflect Google's indexing time rather than the publisher's first-publication time. It is not a canonical T0 until it has been validated against human-read Reuters timestamps (for example the five 2026-10-05 events: 03:53, 05:33, 07:18, 08:01 and 08:10 GMT+2). That validation and the decision to promote it belong to a human; until then the routine may only report RSS values in the PR for comparison.
4. **T0 not found → that event alone is not ingested.** The others are still ingested. Every excluded item is listed in the PR and on the brief issue, with the exact reason and the raw tool error.

## Pipeline

1. Read the brief issue; read the protocol docs, schema, classifier and all journals under `data/brief_events/`.
2. Create branch `brief/YYYY-MM-DD` from `origin/main`. If that branch already carries commits not in `main`, stop and report.
3. Build `brief-event-v1` candidates only for investment-relevant items with a valid T0; `captured_at` is the actual ingestion time.
4. Run `scripts/classify_story_relation.py` for each candidate against `data/brief_events/`. Proposals are accepted as-is; the routine does not override them automatically, and doubts are flagged in the PR for a human.
5. `scripts/ingest_brief_events.py`, `scripts/validate_brief_events.py`, `python -m unittest discover -s scripts -p 'test_brief*.py'`, `scripts/check_append_only_git.py origin/main`.
6. Commit only `data/brief_events/YYYY-MM-DD.json`, push, open the PR to `main` with the classifier audit and the T0 provenance table.
7. **Merge only if** every local validation above passed **and** every CI check on the PR head is successful. Otherwise do not merge, and report.
8. After merging, close the brief issue with the PR link.

## Operational notes for the routine session

- The routine must be created from the claude.ai Routines page **with this repository attached** (push access). A routine created without an attached repository cannot clone it or call GitHub; it must stop at step 1 and report the raw error.
- GitHub GraphQL is refused in these sessions: use the `mcp__github__` tools or `gh api repos/...` (REST), never `gh issue list` / `gh pr ...`.
- Work on a fresh branch from `origin/main`; delete `scripts/__pycache__/` before committing; commit only `data/brief_events/YYYY-MM-DD.json`.
- Merge with method `merge` and `expectedHeadSha` set to the full head SHA. Never push an empty commit, disable a test or force-push.
- If there is no ingestible event: open no PR, comment the reasons on the brief issue and leave it open.

## Error reporting

On any failure, report the failed step and the raw tool response verbatim, without inferring a cause the message does not state. Nothing is presented as validated before CI is green.

## Network prerequisites

The routine's cloud environment must allow the hosts it reads T0s from (at least `www.reuters.com`; `news.google.com` for RSS comparison). A denied host is reported as such; it never becomes a guessed T0.
