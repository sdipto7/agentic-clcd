---
name: clone_detection_algo
description: Use this skill to detect clones by comparing two extracted pseudocode algorithms. Best suited for longer or logically complex fragments where extracting the core algorithm first makes comparison clearer and more reliable. Requires algorithm_extraction to be applied to both code fragments first.
---

# Algorithm-Based Clone Detection
Apply this skill **after** both code fragments have been converted to language-agnostic pseudocode using the algorithm_extraction skill.

## Steps
1. **Read both algorithms carefully**: for each algorithm identify the entry point, the role of each function, data structures used, and how data flows through the logic.
2. **Compare semantic equivalence**: align loops, recursion, conditions, data structure operations, and return values conceptually — not by line count. They are clones only if
   no functional difference could be observed on any valid input. Minor wording differences are fine; missing branches, different operation orderings, or different return values are not.
3. **Decide**:
   - Semantically equivalent → `CLONE`
   - Any behavioral difference → `NOT_CLONE`
4. **Output strictly JSON — no markdown fences, no extra text:**
   {"verdict": "CLONE" or "NOT_CLONE", "confidence": 0.0-1.0, "reasoning": "max 100 words identifying the steps that matched or diverged"}