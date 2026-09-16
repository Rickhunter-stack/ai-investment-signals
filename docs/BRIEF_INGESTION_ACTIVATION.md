# Activation sequence

1. Merge ingestion code after checks pass.
2. Update the existing ChatGPT daily brief automation to emit and append brief-event-v1 records.
3. Start only with briefs generated after activation; do not backfill earlier briefs.
4. Observe several days of real events before implementing story deduplication.
