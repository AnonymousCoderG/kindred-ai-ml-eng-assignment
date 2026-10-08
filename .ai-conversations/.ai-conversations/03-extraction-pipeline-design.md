# Design the extract-attributes pipeline (Part 3)

## Prompt (summarised)
Extract member attributes from messages with a real LLM; idempotent, retry only transient errors, one failing message must not stop the batch.

## What the AI did
AI drafted llm_errors.py, llm_real.py, services/extraction.py and the router. Idempotency key is (club_id, source_message_id); concurrency via pg_advisory_xact_lock plus re-check; backoff with jitter honouring Retry-After; permanent errors (400/401/bad output) not retried; per-message rollback and a failed status.

## What I checked and how
tests/test_extraction.py (11 tests) and a live batch on demo messages 10-14.

## Mistakes or corrections
AI first wrote code assuming the config fields existed. app/config.py had no llm_* settings, so the server crashed with 'Extra inputs are not permitted'. I found it in the traceback; fix was to declare the llm_* fields in config.py.

## Decision
Accepted after the config fix.
