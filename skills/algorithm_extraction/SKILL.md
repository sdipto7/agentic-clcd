---
name: algorithm_extraction
description: Use when you must turn a single source code fragment into language-agnostic pseudocode before comparison.
---

# Algorithm extraction

Follow these steps whenever you need a neutral description of what code does.

1. **Identify the language** of the fragment (Java, Python, etc.) and the apparent entry point (e.g., `main`, top-level script, or the method under study).
2. **List every function or method** that participates in the shown behavior, including helpers called from the entry fragment.
3. For **each function**, write a block starting with `FUNCTION <name>` (use the real name or `main` / `anonymous` if unnamed).
4. Inside each block, use **numbered plain-English steps only**—no syntax from any programming language. Describe reads, writes, branches, loops, returns, and exceptions in prose.
5. **Preserve logic exactly**: every condition, loop bound, edge case, and early exit must appear in the pseudocode. Do not simplify away null checks, empty collections, or error paths.
6. Use **generic data-structure words** (`list`, `map`, `set`, `queue`) instead of library-specific names (`ArrayList`, `HashMap`, `dict`, etc.).
7. **Output format** (plain text, not JSON):
   - Line 1: a **one-line summary** of overall behavior.
   - Then one `FUNCTION` block per function with numbered steps as described above.

After you produce the pseudocode, keep it available for later comparison steps; do not reintroduce source-language syntax.
