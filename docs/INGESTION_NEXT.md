# Post-merge activation

After this ingestion PR is validated and merged, update the existing ChatGPT daily brief automation so investment-relevant selected items are appended to the current `data/brief_events/YYYY-MM.json` journal using the `brief-event-v1` contract.

Do not enable automatic story relations beyond `NEW` until the deduplication layer is implemented and reviewed.
