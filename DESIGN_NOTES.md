# Design Notes

## Part 2: session-flow issue

In `advance_turn` (`app/services/session_flow.py:31-55`), the `affirm` branch calls `payment_mock_client.charge` at line 36 before anything is persisted, and its only guard is `session.awaiting_confirmation`, which is not cleared until line 53. A crash between lines 36 and 54, or a client retry, therefore charges the member again while the session still looks unpaid (my trace showed `charges: [500, 500]` with `booking_id: null`). I would create the `Booking` and a `PaymentAttempt` carrying an `idempotency_key` derived from the session id, commit that before calling the provider, look up an existing attempt on retry instead of charging again, and only allow `affirm` while `session.status == "active"` so an escalated `refund_dispute` can never be charged.

## Part 2: root-cause fix for the cross-club leaks

The knowledge query and the introductions endpoint leaked for the same reason: the caller's club was checked against the URL, but the data query was not limited to that club. The fix is one shared module, `app/scoping.py` (`get_club_member_or_404`, `matchable_attributes`), used by both endpoints, rather than a patch in each handler. A member of another club and a missing member both return 404, so the response never confirms that a member exists in another club.

## Part 3: structured extraction pipeline

### What key decides that a message has already been processed?

In `_already_processed` (`app/services/extraction.py`) a message counts as processed when a `member_attributes` row exists with:

```
MemberAttribute.club_id == message.club_id,
MemberAttribute.source_message_id == message.id,
```

That is the idempotency key: `(club_id, source_message_id)`. Idempotency matters because re-running a batch must not create duplicate rows or spend LLM calls again. Two simultaneous requests for the same message are serialised with `pg_advisory_xact_lock(4242, message.id)` and the key is checked again after the lock is taken, because the table has no unique constraint and I may not add one. All of a message's rows are committed in one transaction. Within one message, items with the same (kind, normalised text) are written once.

I have not run a true parallel-request test of the lock; the idempotency tests run requests one after another.

### How is a restricted attribute kept out of matching?

Restricted attributes are written to `member_attributes` with `restricted = true`. The check that keeps them out is `MemberAttribute.restricted.is_(False)` inside `_matchable()` in `app/scoping.py`. It runs in the data-access layer, at query time, and it is the only place that defines what is matchable. `matchable_attributes` (used by introductions and by `build_member_profile_text`) and `matchable_profile_texts` (used by `rank_candidates`) both go through it, so a restricted row never reaches the text that is embedded for ranking. Ranking no longer reads the stored `profile_embedding`, because rows created before the fix were built from every attribute, restricted ones included. Tests: `tests/test_matching_restricted.py` spies on the embedder and asserts it never receives restricted text; `tests/test_extraction.py` checks a restricted row is stored but not returned by `matchable_attributes`.

### Retry strategy

The retry strategy lives in `extract_with_retry` (`app/services/extraction.py`). Only transient errors are retried: 429, 5xx, timeouts and network errors. Up to `LLM_MAX_ATTEMPTS` attempts, with exponential backoff (`base * 2^(attempt-1)`, capped at `LLM_MAX_DELAY_SECONDS`), jitter between 50% and 100% of that wait, and never less than a `Retry-After` the provider sends. A permanent error (400, 401, unparseable output) is not retried, because repeating the request cannot succeed. After the last attempt the message is recorded as `failed` with the reason, nothing is written for it, and the batch continues. The next run retries only the messages that have no rows yet. This was exercised for real: the free model returned 429 repeatedly, and the batch returned a mix of `processed` and `failed` and was completed over several runs.

### Failure isolation

`run_extraction` wraps each message in its own `try/except`, rolls back that message, records `failed`, and moves on. In a batch of 5 where message 3 fails permanently and message 4 succeeds, message 3 is reported `failed` with no rows, message 4 is `processed`, and the response still lists all five. `test_one_permanent_failure_does_not_fail_the_batch` covers exactly this and checks that a re-run retries only message 3.

### Prompt and validation

The prompt defines the four kinds, the 0-1 confidence scale and the restricted category, and includes few-shot examples taken from the seeded messages, not from `eval/golden_set.json`, so the eval measures behaviour on messages the prompt has not seen. Member messages are wrapped in tags and the model is told to treat them as data, as a basic defence against prompt injection. Every item is validated with pydantic (kind in the four values, confidence between 0 and 1, non-empty text); invalid items are dropped and counted.

### Eval and threshold

`eval/run_eval.py` runs the real pipeline path (real API, real retries and validation) over `eval/golden_set.json`. Per record it scores `kind`, `restricted` (exact) and keyword presence. Threshold: **0.9 overall, and zero wrong `restricted` flags**. With 4 records there are 12 checks, so 0.9 allows at most one missed check (11/12 = 91.7%); two misses (83.3%) fail. A wrong `restricted` flag fails the eval on its own, because that error would put health information into matching. An API outage is reported as INCONCLUSIVE (exit code 2) instead of a 0% score, because an outage says nothing about the model. Result with `nvidia/nemotron-3-super-120b-a12b:free`: **12/12 = 100%, 0 restricted errors**. Caveat: 4 records is a small sample, so 100% is weak evidence of general quality.

### Model choice

I wanted Claude, but the card form blocked the credit purchase. Gemini's free key returned 402 for every model, and the free Gemma models were rate-limited upstream (429) during the eval. I ended up on a free OpenRouter model. The client is provider-neutral (`LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY`), so switching is a `.env` change. Free models are shared and rate-limited, which would not be acceptable in production.

### Schema note (not changed)

A message the LLM extracts nothing from leaves no `member_attributes` row, so it cannot be marked processed and is sent to the LLM again on every run. I would ask the schema owner for a processed marker (for example a `processed_at` column on `conversation_messages`, or a small extraction-log table keyed by message id) instead of adding it myself.

### Other notes

The demo messages come from `scripts/demo_messages.py`, which inserts extra messages without touching the seed script, because every seeded message already has an attribute and would be skipped. A pre-existing setup issue: `tests/conftest.py` pointed at the `psycopg2` driver, which is not in `requirements.txt`.

## Closing question: what I did not do, and what I would build next

I deliberately did not do Part 4, and I did not fix review issues 3 to 8. I wrote them up with traces and fixed the two cross-club leaks, because those expose another club's data. The unfixed ones are the double charge in `advance_turn`, the escalation bypass, the client-controlled amount in `confirm-payment`, and the global charge log. I also did not race-test the advisory lock with truly parallel requests.

With one more day I would first fix the payment and session flow, because it moves real money: persist the booking and a `PaymentAttempt` with an `idempotency_key` before charging, charge `booking.amount_cents` instead of the client's number, reject a second confirmation, allow `affirm` only while the session is `active`, and scope the charge log by club. Then I would add a test that fires parallel extraction requests at the same message to prove the lock, and put the extraction batch behind a job queue with a status endpoint, so a long batch with retries does not hold an HTTP request open.
