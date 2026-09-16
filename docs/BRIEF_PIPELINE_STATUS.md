# Brief pipeline status

Current stage after PR #21:

`ChatGPT daily brief -> structured brief-event-v1 -> safe append helper -> immutable monthly journal`

This change intentionally stops before automatic story deduplication, thesis updates, criticality scoring, weekly score changes, or dashboard UI changes.

After this ingestion layer is validated in production, the next layer will compare new events with prior journal entries and assign story relations without mutating historical events.
