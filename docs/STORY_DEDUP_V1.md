# Story deduplication v1

Brief events remain the immutable source of truth. Story classification never edits a frozen event.

For each new event, compare it with frozen history before ingestion. `scripts/classify_story_relation.py` proposes a match using explainable lexical, ticker/company and theme overlap.

Relations:
- `NEW`: no sufficiently similar prior story.
- `REPEAT`: essentially the same information without material change.
- `CONFIRM`: new evidence supports an existing story.
- `ACCELERATE`: evidence materially increases the story's intensity/importance.
- `DETERIORATE`: evidence materially reduces the story's intensity/importance.
- `CONTRADICT`: evidence points in the opposite direction.
- `RESOLVE`: reserved for explicit closure; v1 does not infer it automatically.

A matched story reuses its permanent `story_id`. If the matched historical event predates story IDs, the deterministic ID `STORY-<first_event_id>` is used. This does not rewrite the historical event.

The classifier is intentionally conservative and is a proposal, not a black-box truth. Its `matched_event_id` and similarity make the decision auditable.

## Information-time integrity

Events already frozen remain untouched. Prospectively, `published_at` is mandatory, timezone-aware and cannot be later than `captured_at`. This gives future outcome analysis a defensible information timestamp T0.

A factual error discovered later must be represented by a new `CONTRADICT`/correction event linked to the story, never by editing the frozen original.


## Journal layout

Story matching uses the combined frozen history from every JSON journal under `data/brief_events/`. Legacy monthly journals and new daily journals are equivalent historical inputs; file boundaries never define story boundaries.


## Human override of classifier proposals

`scripts/classify_story_relation.py` is an auditable proposal engine, not an infallible oracle. A human/research-agent override is allowed when the proposed match or relation is factually incoherent.

Every override is mandatory-audit and must be recorded in the ingestion pull-request description with:

- new `event_id`;
- classifier proposed `story_id` and relation;
- classifier similarity score or other relevant proposal metadata;
- final chosen `story_id` and relation;
- concise factual justification for the deviation.

Overrides must be exceptional and evidence-based. They must not be used merely to obtain a preferred investment interpretation or stronger/weaker signal.

If there is no override, the PR description should state that classifier proposals were accepted as-is for all ingested events.

The event schema remains unchanged: override audit metadata belongs in the pull-request record, not in frozen event objects. This preserves schema stability while keeping deviations reviewable.
