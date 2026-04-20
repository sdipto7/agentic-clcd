---
name: clone_detection_direct
description: Use when you must decide if Java and Python source code fragments are cross-language clones without an intermediate algorithm write-up.
---

# Direct cross-language clone detection

Use this skill when comparing **raw source** (not extracted pseudocode).

## Steps

1. **Understand Java**: Summarize inputs, outputs, data structures, control flow, and important edge cases purely in terms of behavior.
2. **Understand Python**: Do the same independently, ignoring naming and library differences.
3. **Compare behavior**: Check that both fragments implement the same algorithm—same ordering of operations, equivalent conditions, matching handling of empty inputs, errors, and boundary values. Syntax differences are irrelevant; semantic differences are not.
4. **Decide** whether they are functionally the same (`CLONE`) or not (`NOT_CLONE`).
5. **Respond with JSON only** (no markdown fences, no extra prose) using exactly:
   ```json
   {"verdict": "CLONE" or "NOT_CLONE", "confidence": 0.0-1.0, "reasoning": "<=100 words"}
   ```

Keep `reasoning` under 100 words and cite the decisive behavioral evidence.
