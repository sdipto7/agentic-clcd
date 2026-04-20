---
name: clone_detection_algo
description: Use when you already have two plain-English algorithm descriptions and must judge if they are semantically equivalent.
---

# Algorithm-based clone detection

Apply this skill **after** both sides have been expressed as language-agnostic pseudocode (see `algorithm_extraction`).

## Steps

1. **Read Algorithm A** (from Java) and **Algorithm B** (from Python) carefully, including every numbered step and edge-case branch.
2. **Align logical structure**: match loops, recursion, data-structure operations, and return values conceptually (not by line count).
3. **Check semantic equivalence**: they are clones only if a user could not observe a behavioral difference on any input allowed by both descriptions. Minor wording differences are fine; missing branches or different orderings are not.
4. **Choose a verdict**: `CLONE` if equivalent, otherwise `NOT_CLONE`.
5. **Emit JSON only** (no markdown fences) with exactly:
   ```json
   {"verdict": "CLONE" or "NOT_CLONE", "confidence": 0.0-1.0, "reasoning": "<=100 words"}
   ```

Keep reasoning concise (≤100 words) and point to the steps that matched or diverged.
