---
name: clone_detection_direct
description: Use this skill to detect clones by comparing the functional behavior of raw Java and Python source code directly. Best suited for short or logically simple code fragments where the intent is easy to read from the code itself.
---

# Direct Cross-Language Clone Detection

Use this skill when comparing **raw source code** fragments directly.

## Steps

1. **Analyze the Java fragment**: identify its inputs, outputs, data structures, control flow, and how it handles edge cases and errors — purely in terms of behavior, not syntax.
2. **Analyze the Python fragment**: do the same independently. Ignore naming conventions, library choices, and language idioms.
3. **Syntax is irrelevant. Semantics are not.** Two fragments can look completely different and still be clones. Two fragments can look similar and not be clones. Judge behavior only.
4. **Compare behavior**: do both fragments implement the same logic? Check operation ordering, equivalent conditions, and matching handling of empty inputs, errors, and boundary values.
5. **Decide**:
   - Functionally the same → `CLONE`
   - Functionally different → `NOT_CLONE`
6. **Output strictly JSON — no markdown fences, no extra text:**
   {"verdict": "CLONE" or "NOT_CLONE", "confidence": 0.0-1.0, "reasoning": "max 100 words citing the decisive behavioral evidence"}