# Brief-event score semantics

All event scores are captured at T0 and frozen.

- `importance`: materiality of the event for the investment research universe, 0 = negligible, 100 = exceptionally material.
- `novelty`: how new the information is at capture time, 0 = fully known/repetitive, 100 = genuinely new.
- `confidence`: confidence that the event is correctly classified and supported by available evidence, 0 = very uncertain, 100 = very strong evidence.
- `execution_risk`: risk that the implied industrial/business development fails to materialize, 0 = low risk, 100 = high risk.
- `pricing_status`: categorical assessment; use `uncertain` when evidence is insufficient.

These event-level fields do not replace or retroactively alter the weekly-v1.0 company scores.
