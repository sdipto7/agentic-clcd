---
name: algorithm-extraction
description: Use this skill to convert a source code fragment into language-agnostic algorithm. Required before using clone-detection-algo skill. Apply once per Java fragment and once per Python fragment.
---

# Algorithm Extraction
Use this skill to convert a source code fragment into a precise, language-agnostic algorithm. Follow these steps whenever you need a neutral plain-English description of a code fragment.

## Background
This algorithm will be used to compare the computational logic of two code fragments written in different programming languages to determine if they are clones. Accuracy and completeness are critical — every logical detail must be preserved.

## Extraction Rules - follow this order
1. Start with a single sentence summarizing what the overall code does.
2. Describe every function including the entry point as a FUNCTION block.
3. Inside each FUNCTION block, use numbered plain-English steps only. No syntax from any programming language whatsoever.
4. Preserve all logic exactly - every condition, loop bound, branch, validation check, early exit, and error path must appear.
5. Use generic data structure names only: list, map, set, queue, stack.
6. Do not include comments, type annotations, import descriptions, or any language-specific observations in the algorithm.

## After extracting algorithms from BOTH the Java and Python code fragments
You MUST call record_algorithms tool exactly once per pair, only after extracting both algorithms. Never call it after a single algorithm extraction.

Pass a JSON string to record_algorithms tool with exactly these keys:

**"java_algorithm"** : the algorithm you extracted from the Java fragment

**"python_algorithm"** : the algorithm you extracted from the Python fragment

## Algorithm Format (plain text only)
Summary: one sentence describing overall behavior.

FUNCTION: 'name'

  1. first step in plain English

  2. second step in plain English
  ...

FUNCTION: 'name'

  1. first step in plain English

  2. second step in plain English
  ...
