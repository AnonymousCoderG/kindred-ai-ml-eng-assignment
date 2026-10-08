# Why did my retry delay setting have no effect?

## Prompt (summarised)
I changed LLM_BASE_DELAY_SECONDS in .env and the behaviour did not change.

## What the AI did
AI explained: uvicorn --reload watches .py files only, so .env changes need a full server restart.

## What I checked and how
Restarted the server and re-ran the batch; the delay applied.

## Mistakes or corrections
Earlier I had assumed reload covered .env. Corrected.

## Decision
Accepted. Also: API keys live only in .env, never in chat or git.
