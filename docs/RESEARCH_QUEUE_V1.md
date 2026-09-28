# Research Queue v1

The Research Queue identifies companies whose latest frozen weekly snapshot lacks one or more sourced qualitative components: `novelty`, `pricing_headroom`, or `execution_risk`.

It is an advisory prioritization layer. It never invents a score and never edits `signal_research.json` or a frozen weekly snapshot.

## Priority

Missing components drive priority. Recent investment-relevant brief events are used only as a tie-break / urgency boost. This makes companies such as META visible for research without allowing a news item to become a score automatically.

## Flow

```text
latest frozen weekly snapshot
 + prospective brief-event evidence
 -> research_queue.json
 -> sourced DEEP_DIVE
 -> reviewed signal_research.json inputs
 -> next scheduled weekly snapshot
```

The research step remains responsible for dated rationales and valid source URLs. Existing weekly-v1 freshness and fail-closed rules remain authoritative.
