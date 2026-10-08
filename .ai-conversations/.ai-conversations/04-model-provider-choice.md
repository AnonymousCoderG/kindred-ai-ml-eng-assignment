# Pick a model provider that works

## Prompt (summarised)
Which LLM API can I use for free for the pipeline?

## What the AI did
AI suggested Gemini first. Later suggested OpenRouter free models.

## What I checked and how
Checked with real curl calls against each model.

## Mistakes or corrections
AI suggested Gemini model names that returned 404 (not available to new users) and 402 for others, and Gemma returned 429 repeatedly. I ran a loop over candidate models and picked by actual status codes.

## Decision
Rejected Gemini and Gemma. Used OpenRouter with nvidia/nemotron-3-super-120b-a12b:free because it returned 200 consistently. Client stays provider-neutral (OpenAI-compatible).
