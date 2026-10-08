# AI conversation index

Honest note: these entries were written up at the end from my working sessions with Claude (chat + Claude Code), summarised, not raw transcripts. The mistakes listed really happened.

| # | File | What I asked | What I accepted | What I corrected or rejected |
|---|---|---|---|---|
| 01 | 01-code-review-and-isolation-bugs.md | Review the repo for multi-tenant isolation bugs | Accepted the findings that reproduced | none |
| 02 | 02-root-cause-fix.md | Fix the top issue at the root cause, not per endpoint | Accepted | none |
| 03 | 03-extraction-pipeline-design.md | Design the extract-attributes pipeline (Part 3) | Accepted after the config fix | AI first wrote code assuming the config fields existed |
| 04 | 04-model-provider-choice.md | Pick a model provider that works | Rejected Gemini and Gemma | AI suggested Gemini model names that returned 404 (not available to new users) and 402 for others, and Gemma returned 429 repeatedly |
| 05 | 05-eval-and-outage-handling.md | Write an evaluation for the extraction | Accepted the fix | The eval scored an API outage as wrong answers |
| 06 | 06-env-and-restart-lessons.md | Why did my retry delay setting have no effect? | Accepted | Earlier I had assumed reload covered  |
| 07 | 07-design-notes-and-closing-question.md | Write DESIGN_NOTES.md | Accepted after editing | none |
