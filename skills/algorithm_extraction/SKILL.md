---
name: algorithm_extraction
description: Use this skill to convert a source code fragment into language-agnostic pseudocode. Required before using clone_detection_algo. Apply once per Java fragment and once per Python fragment.
---

# Algorithm Extraction
Follow these steps whenever you need a neutral plain-English description of what a code fragment does.

1. **Identify the language** of the fragment (Java, Python, etc.) and locate the entry point (e.g., `main`, top-level script, or the primary method under study).
2. **List every function or method** called directly or indirectly from the entry point, including helper functions.
3. For **each function**, write a block starting with `FUNCTION <name>` (use the real name or `main` / `anonymous` if unnamed).
4. Inside each block, use **numbered plain-English steps only**-no syntax from any programming language. Describe reads, writes, branches, loops, returns, and exceptions in prose.
5. **Preserve all logic exactly**: every condition, loop bound, edge case, null check, empty collection check, and early exit must appear. Do not simplify or omit anything.
6. Use **generic data structure names** only: `list`, `map`, `set`, `queue`, `stack` - never `ArrayList`, `HashMap`, `dict`, `vector`, etc.
7. **Output format** (plain text, not JSON):
   - Line 1: a single sentence summarizing the overall behavior.
   - Then one `FUNCTION` block per function, each with numbered plain-English steps.
