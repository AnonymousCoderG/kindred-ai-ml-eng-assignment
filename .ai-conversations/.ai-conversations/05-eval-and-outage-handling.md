# Write an evaluation for the extraction

## Prompt (summarised)
Golden set of 4 records, 3 checks each (12), pass at 0.9 and zero wrong restricted flags. Few-shot examples must come from seeded messages, not the golden set.

## What the AI did
AI wrote eval/run_eval.py.

## What I checked and how
First run printed 0/12 during a provider 429 outage.

## Mistakes or corrections
The eval scored an API outage as wrong answers. I pointed out 0/12 meant the provider was down, not that the model was bad. Fix: outages are reported INCONCLUSIVE with exit code 2, only real wrong answers fail (exit 1).

## Decision
Accepted the fix. After switching model, eval gave 12/12 PASS.
