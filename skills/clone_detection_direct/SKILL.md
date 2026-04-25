---
name: clone_detection_direct
description: Use this skill to detect clones by comparing the functional behavior of raw Java and Python source code directly. Best suited for short or logically simple code fragments where the intent is easy to read from the code itself.
---

# Direct Cross-Language Clone Detection

Use this skill when comparing **raw source code** fragments directly without extracting algorithms first.

## Background
Two code fragments are cross-language clones if they implement the same computational logic and produce the same output for the same input, regardless of programming language, syntax, naming conventions, or library choices used.

## Reasoning Approach — follow this order
1. **Analyze the Java and Python code fragments independently**: identify their inputs, outputs, data structures, control flow, and how they handle edge cases and errors — purely in terms of behavior, not syntax.
2. **Compare behavior**: check operation ordering, equivalent conditions, and matching handling of empty inputs, boundary values, and errors.
3. **Decide**:
   - Behaviorally identical on all inputs → `CLONE`
   - Any behavioral difference exists → `NOT_CLONE`

## Important Rules
- Syntax is irrelevant. Semantics are not. Two fragments can look completely different and still be clones. Two fragments can look similar and not be clones. Judge behavior only.
- If any behavioral difference exists on any valid input, the verdict
  is `NOT_CLONE` — even if the overall structure looks similar.

## Output
Respond with a single JSON object only. No markdown fences, no text before or after the JSON.
Use exactly these keys:
"verdict"    : "CLONE" if functionally identical, "NOT_CLONE" otherwise
"confidence" : a float between 0.0 and 1.0 representing how certain you are of your verdict based on the evidence
"reasoning"  : max 100 words citing the specific behavioral evidence that determined your verdict

Example output shape:
{{"verdict": "CLONE", "confidence": 0.92, "reasoning": "Both iterate and aggregate the same way."}}
