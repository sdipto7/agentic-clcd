---
name: result-record
description: Use when you have reached a final clone detection verdict and need to record it using the write_result tool.
---

# Recording a Clone Detection Result
Use this skill after you have completed your analysis and formed a final verdict. This is the last step for every pair.

## Before Calling write_result - Confirm You Have
1. `pair_id` for the active pair (provided in the task text),
2. Your final **verdict**: exactly `CLONE` or `NOT_CLONE`. Use underscore form - `NOT_CLONE`, never `NOT CLONE`.
3. A **confidence** score between 0.0 and 1.0 representing how certain you are of your verdict based on the evidence.
4. A **reasoning** string of max 100 words citing the specific behavioral evidence that determined your verdict.

## Calling write_result
Pass a single JSON string as the data argument:
{"verdict": "your verdict", "confidence": "your confidence score", "reasoning": "your reasoning here"}

The tool automatically binds the pair_id, dataset, and timing - do not pass these yourself.

## Important Rules
- Do not call `write_result` before completing your full analysis.
- Call `write_result` exactly once per pair.
