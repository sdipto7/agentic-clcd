"""
LLM prompt templates for Pipeline 1 (direct) and Pipeline 2 (algorithm-based).

All user-facing model instructions for those pipelines live here exclusively.
"""

from __future__ import annotations

# Pipeline 1: single-call cross-language clone decision from raw source.
DIRECT_DETECTION_PROMPT: str = """You are an expert in program analysis and cross-language code equivalence.

Decide whether the two code fragments below implement the **same functionality**.
Ignore syntax, naming style, and library differences; focus on behavior, control flow, data transformations, and edge cases.

Java code:
```java
{codeA}
```

Python code:
```python
{codeB}
```

Respond with **only** a single JSON object and nothing else (no markdown fences, no commentary).
The JSON must have exactly these keys:
- "verdict": either "CLONE" if they are functionally the same, or "NOT_CLONE" otherwise
- "confidence": a number between 0.0 and 1.0
- "reasoning": at most 100 words explaining your decision

Example shape (content is illustrative):
{{"verdict": "CLONE", "confidence": 0.92, "reasoning": "Both iterate and aggregate the same way."}}
"""

# Pipeline 2 step 1 & 2: extract language-agnostic algorithm from one fragment.
ALGO_EXTRACTION_PROMPT: str = """You extract precise, language-agnostic algorithms from source code.

Language: {language}

Source code:
```
{source_code}
```

Produce a **plain-text** pseudocode description (not JSON):
1. Start with **one line** summarizing what the program or entry fragment does.
2. Then describe each function (including the entry point) as a **FUNCTION** block.
3. Inside each block use **numbered plain-English steps** only — no programming language syntax.
4. Preserve all logic, branches, loops, and edge cases exactly.
5. Use generic data-structure names (e.g., list, map, set) instead of library-specific types.

Format example (structure only):
Summary: ...
FUNCTION main
  1. ...
  2. ...
FUNCTION helper_name
  1. ...
"""

# Pipeline 2 step 3: compare two extracted algorithms for semantic equivalence.
ALGO_DETECTION_PROMPT: str = """You compare two language-agnostic algorithm descriptions written in plain English.

Algorithm A (from Java extraction):
---
{algorithm_a}
---

Algorithm B (from Python extraction):
---
{algorithm_b}
---

Decide whether they describe the **same functionality** (same logic and behavior, including edge cases).

Respond with **only** a single JSON object and nothing else (no markdown fences, no commentary).
The JSON must have exactly these keys:
- "verdict": "CLONE" if the algorithms are semantically equivalent, otherwise "NOT_CLONE"
- "confidence": a number between 0.0 and 1.0
- "reasoning": at most 100 words explaining your decision
"""
