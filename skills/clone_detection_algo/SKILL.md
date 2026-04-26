---
name: clone_detection_algo
description: Use this skill to detect clones by comparing two extracted pseudocode algorithms. Best suited for longer or logically complex fragments where extracting the core algorithm first makes comparison clearer and more reliable. Requires algorithm_extraction to be applied to both code fragments first.
---

# Algorithm-Based Clone Detection
Apply this skill **after** both code fragments have been converted to language-agnostic pseudocode using the algorithm_extraction skill.

## Background
You are comparing two pseudocode algorithms - Algorithm A extracted from Java and Algorithm B extracted from Python. Your task is to determine whether both algorithms implement the same computational logic, meaning they are cross-language code clones. This comparison is purely at the logical level — language, syntax, and naming differences are already eliminated in the pseudocode.

## Reasoning Approach — follow this order
1. **Read Algorithm A and Algorithm B independently**: identify the entry point, the role of each function, data flow, and how each algorithm handles edge cases and errors.
2. **Compare step by step**: align loops, conditions, data structure operations, and return values conceptually — not by line count.
3. **Apply these rules during comparison**:
   - Minor wording differences in the pseudocode are acceptable.
   - Missing branches, different operation orderings, or different return values are not acceptable — treat these as behavioral differences.
   - If any behavioral difference exists on any valid input, the verdict is `NOT_CLONE`.
4. **Decide**:
   - Semantically equivalent on all valid inputs → `CLONE`
   - Any behavioral difference exists → `NOT_CLONE`

## Important Rule
This comparison is purely logical. Do not reintroduce any language-specific reasoning - the pseudocode has already eliminated syntax and naming differences. Judge computational logic only.

## Output
Once you have reached your verdict, you should have all three values needed to call write_result:
"verdict"    : "CLONE" if functionally identical, "NOT_CLONE" otherwise
"confidence" : a float between 0.0 and 1.0 representing how certain you are of your verdict based on the evidence
"reasoning"  : max 100 words citing the specific behavioral evidence that determined your verdict

Pass these values directly as arguments to the write_result tool.
