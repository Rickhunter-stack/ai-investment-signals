# Scheduled daily brief v2 (single actor: Claude Code routine)

**Status:** adopted 2026-10-19. Supersedes `SCHEDULED_INGESTION_V1.md` from the first brief produced by the routine (see "Author change" below).
**Routine prompt (versioned):** `config/routine_daily_brief_v2.md`.
**Unchanged and still authoritative for integrity:** `DAILY_BRIEF_INGESTION.md`, `STORY_DEDUP_V1.md`, `UNIFIED_DAILY_BRIEF_V1.md`, the `brief-event-v1` schema.

## Why v2

Under v1, ChatGPT selected the five signals and was supposed to hand them over through a `Brief YYYY-MM-DD` issue; in practice it tried to write the journal itself and its writes were refused (`This tool call was blocked by OpenAI's safety checks.`). No handoff issue was ever opened and no scheduled routine existed, so the briefs of 2026-10-12 to 2026-10-18 were not ingested on time. v2 removes the handoff: one scheduled Claude Code routine produces the brief and ingests it.

## Division of labour

One scheduled Claude Code routine, once a day:

1. **Editorial pass:** daily watch and selection of exactly five signals, following `UNIFIED_DAILY_BRIEF_V1.md`.
2. **Mechanical pass:** T0 verification, `brief-event-v1` construction for the investment-relevant items, story classification, validation, pull request, merge when green.

The project owner reads the brief and reviews the pull requests; no human relay is required.

## Author change and selection bias

Changing the author of the brief changes the editorial selection mechanism described in `PREREGISTRATION.md` §22. It does not change any v1 confirmatory rule, the weekly Signal Score or `signal_research.json`.

To keep the two periods separable:

- events captured up to and including 2026-10-19 were selected by ChatGPT (the 2026-10-19 journal holds the relayed 13 and 14 October briefs);
- events selected by the routine start with the first brief archived under `data/daily_briefs/`; that file's date and its merge commit are the dated record of the change, and every routine brief has its own archived file;
- any later analysis of event frequency, novelty or relevance reports the two periods separately.

## Selection independence

When selecting the five signals, the routine does not consult this project's outcome journals, monthly reports, dashboards or post-T0 performance. Selection must not be steered by what has or has not worked in the experiment so far. Public market information remains admissible as context.

## Outputs

For brief date `YYYY-MM-DD` (Europe/Paris), on branch `brief/YYYY-MM-DD` created from `origin/main`:

1. `data/daily_briefs/YYYY-MM-DD.md` — the full human brief, all five items, including those not investment-relevant. It archives the selection itself, which is needed to audit selection bias. It is never edited after merge; a correction is a new note in a later brief.
2. `data/brief_events/YYYY-MM-DD.json` — only the investment-relevant items with a verified T0, under the unchanged v1 rules.

These two files are the only files committed. If no item is investment-relevant or has a verified T0, the brief file is still committed and the pull request says that no event was ingested.

## T0 rules

Unchanged principles from `SCHEDULED_INGESTION_V1.md`: never infer a T0; Google News RSS is discovery only; an item without a verified T0 is not ingested and is listed in the pull request with the raw error or reason.

Network findings of 2026-10-20 (routine environment): Reuters, CNBC, AP, GlobeNewswire and BusinessWire refuse automated access (anti-bot 401/403); `www.prnewswire.com`, `www.sec.gov` (with a declared User-Agent) and `news.google.com` are readable. Comparing Google News RSS times with ten relayed Reuters T0s gave only 2 matches within 2 minutes, so RSS stays discovery-only.

Accepted T0 sources since prompt v2.1, all instances of the existing "original page or primary source with explicit time and time zone" rule:

1. SEC EDGAR acceptance date-time of the company's filing on the same fact (New York time, converted to UTC);
2. the release time printed on the official press release at PR Newswire (`ET`, converted from America/New_York to UTC);
3. any other page actually read that shows an explicit first-publication time and time zone.

## Routine loader

The claude.ai routine carries only a short loader prompt that reads `config/routine_daily_brief_v2.md` from `main` and executes its block. A merged change to that file applies from the next run; the PR of each run reports the SHA-256 of the file it executed.

## Pipeline

1. Read the protocol documents, schema, classifier and all journals under `data/brief_events/`.
2. Create `brief/YYYY-MM-DD` from `origin/main`. If it already carries commits not in `main`, stop and report.
3. Editorial pass: produce the five-item brief.
4. Build `brief-event-v1` candidates for investment-relevant items with a verified T0; `captured_at` is the actual ingestion time.
5. Classify each candidate with `scripts/classify_story_relation.py` against the history plus earlier candidates of the same batch. Proposals are accepted as-is; doubts are flagged in the pull request for the owner, who may override them under `STORY_DEDUP_V1.md`.
6. Run `scripts/ingest_brief_events.py`, `scripts/validate_brief_events.py`, `python -m unittest discover -s scripts -p 'test_brief*.py'`, `scripts/check_append_only_git.py origin/main`.
7. Commit the two output files only, push, open the pull request with: the brief, the T0 provenance table, the classifier audit, the excluded items with their reasons, and the SHA-256 of `config/routine_daily_brief_v2.md`.
8. Merge only if every local validation passed and every CI check on the head is successful (method `merge`, `expectedHeadSha` = full head SHA). Otherwise do not merge and report.

## Prerequisites (owner, on claude.ai)

- Routine created from the Routines page with `Rickhunter-stack/ai-investment-signals` attached with push access.
- Environment network policy allowing at least `www.reuters.com` and the news sources used for the watch.
- Web search available in the routine; without it there is no watch and the routine stops and reports.

## Error reporting

On any failure, report the failed step and the raw tool response verbatim, without inferring a cause. Nothing is presented as validated before CI is green.
