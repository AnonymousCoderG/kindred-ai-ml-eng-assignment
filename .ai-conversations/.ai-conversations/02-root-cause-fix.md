# Fix the top issue at the root cause, not per endpoint

## Prompt (summarised)
Fix issue 1 with a change that covers the whole class, with tests that fail before and pass after.

## What the AI did
AI proposed one scoping layer (app/scoping.py: get_club_member_or_404, _matchable with club_id + restricted filter) used by knowledge, introductions and matching, plus tests/test_club_isolation.py.

## What I checked and how
Ran pytest before the fix (6 failed) and after (13 passed). Re-ran the curls; traces in TERMINAL_LOG.md.

## Mistakes or corrections
None in this step.

## Decision
Accepted. Chose 404 (not 403) for other clubs' members so existence is not confirmed. Rationale in DESIGN_NOTES.md.
