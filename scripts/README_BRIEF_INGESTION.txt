Brief ingestion smoke tests

python -m unittest scripts/test_brief_events.py scripts/test_brief_ingestion.py
python scripts/validate_brief_events.py

The daily ChatGPT automation should append only validated brief-event-v1 records. It must not modify weekly_signals.json directly.
