---
name: algorithm_extraction
description: Use this skill to convert a source code fragment into language-agnostic pseudocode. Required before using clone_detection_algo. Apply once per Java fragment and once per Python fragment.
---

# Algorithm Extraction
Use this skill to convert a source code fragment into a precise, language-agnostic pseudocode algorithm. Follow these steps whenever you need a neutral plain-English description of what a code fragment does.

## Background
This algorithm will be used to compare the computational logic of two code fragments written in different programming languages to determine if they are clones. Accuracy and completeness are critical — every logical detail must be preserved.

## Extraction Rules - follow in this order
1. **Start with a single sentence** summarizing what the overall code does.
2. **Identify the entry point** (e.g., `main`, top-level script, or the primary method under study) and list every function or method called directly or indirectly from it, including helpers.
3. **Describe every function including the entry point** as a FUNCTION block starting with `FUNCTION <name>`.
4. **Inside each FUNCTION block**, use numbered plain-English steps only — no syntax from any programming language whatsoever.
5. **Preserve all logic exactly** — every condition, loop bound, branch, null check, empty collection check, early exit, and error path must appear. Do not simplify, merge, or omit anything.
6. **Use generic data structure names only**: list, map, set, queue, stack. Never use language-specific names like ArrayList, HashMap, dict, or vector.
7. **Do not include** comments, type annotations, import descriptions, or any language-specific observations in the output.
8. **After extracting algorithms from BOTH the Java and Python code fragments** 
   call `record_algorithms` exactly once with these exact arguments:
   - `java_algorithm`: the pseudocode you extracted from the Java fragment
   - `python_algorithm`: the pseudocode you extracted from the Python fragment
   - Do not call `record_algorithms` if you only extracted one algorithm.
   - Do not call `record_algorithms` more than once per pair.

## Output Format (plain text only - not JSON)
Summary: one sentence describing overall behavior.

FUNCTION: 'name'
  1. first step in plain English
  2. second step in plain English
  ...

FUNCTION: name
  1. ...
