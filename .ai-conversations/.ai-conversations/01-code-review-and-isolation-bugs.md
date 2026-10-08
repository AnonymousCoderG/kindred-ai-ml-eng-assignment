# Review the repo for multi-tenant isolation bugs

## Prompt (summarised)
Read the routers (knowledge, bookings, introductions, sessions) and find where club boundaries or restricted data leak; prove each with a real request.

## What the AI did
AI pointed at the routers and suggested probes. I ran them (curl with seeded tokens) and saved traces to TERMINAL_LOG.md.

## What I checked and how
Ran the requests myself. Knowledge returned another club's chunks; introductions leaked across clubs; matching used restricted data.

## Mistakes or corrections
None in this step.

## Decision
Accepted the findings that reproduced. Ranked cross-club exposure first, because it breaks the core promise of the product. Written to REVIEW.md.
