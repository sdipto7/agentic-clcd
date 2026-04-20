---
name: evaluation
description: Use when you are ready to finalize a clone decision and must persist it through the experiment tooling.
---

# Recording a clone detection result

Complete this checklist **before** calling the `write_result` tool.

## Steps

1. **Confirm you have**:
   - `pair_id` for the active pair (provided in the task text),
   - `ground_truth` label (1 = clone, 0 = non-clone — informational only),
   - your final `predicted` verdict (`CLONE` or `NOT_CLONE`),
   - a calibrated `confidence` between `0.0` and `1.0`,
   - `reasoning` (≤100 words) summarizing evidence.
2. **Validate the verdict string** is exactly `CLONE` or `NOT_CLONE` (underscore form for `NOT_CLONE` when using the tool).
3. **Call** `write_result` with arguments:
   - `predicted_label`
   - `confidence`
   - `reasoning`
4. After the tool returns success, **stop** further tool calls for that pair unless you must fix an earlier mistake (avoid duplicate writes).

The tool binds `pair_id`, dataset, and timing automatically; do not invent a different identifier.
