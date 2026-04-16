#!/usr/bin/env python3
"""
Filter raw XLCoST and CodeNet JSON dumps to Java–Python pairs and add numeric labels.

Run once from the project root before experiments that use ``data/*.json``.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, List, Tuple

# Allow `python prepare_dataset.py` without installing as a package.
_PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.constants import (  # noqa: E402
    JAVA_LANGUAGE_IDENTIFIER,
    PYTHON_LANGUAGE_IDENTIFIER,
    RAW_JAVA_CN_PATH,
    RAW_JAVA_XL_PATH,
    DATA_JAVA_PYTHON_CN_PATH,
    DATA_JAVA_PYTHON_XL_PATH,
)


def _load_json_array(path: str) -> List[dict[str, Any]]:
    """Load a JSON array from disk or raise a clear error."""
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Missing raw file: {path}")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Expected top-level JSON array in {path}")
    return data


def _keep_record(row: dict[str, Any]) -> bool:
    """Return True if the row is Java (codeA) paired with Python (codeB)."""
    ll1 = str(row.get("ll1", "")).strip()
    ll2 = str(row.get("ll2", "")).strip()
    return ll1 == JAVA_LANGUAGE_IDENTIFIER and ll2 == PYTHON_LANGUAGE_IDENTIFIER


def _add_label(row: dict[str, Any]) -> dict[str, Any]:
    """Return a shallow copy with ``label`` 1 for clone and 0 for nonclone."""
    out = dict(row)
    t = str(out.get("type", "")).strip().lower()
    if t == "clone":
        out["label"] = 1
    elif t == "nonclone":
        out["label"] = 0
    else:
        raise ValueError(f"Unknown type field: {out.get('type')!r}")
    return out


def _filter_dataset(records: List[dict[str, Any]]) -> Tuple[List[dict[str, Any]], int]:
    """
    Filter to Java–Python rows with valid labels.

    Returns:
        Tuple of (kept records with label, discarded count).
    """
    kept: List[dict[str, Any]] = []
    discarded = 0
    for row in records:
        if not isinstance(row, dict):
            discarded += 1
            continue
        if not _keep_record(row):
            discarded += 1
            continue
        try:
            kept.append(_add_label(row))
        except ValueError:
            discarded += 1
    return kept, discarded


def _write_output(path: str, rows: List[dict[str, Any]]) -> None:
    """Write pretty-printed JSON array."""
    parent = os.path.dirname(path)
    os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)
        f.write("\n")


def _summarize(name: str, path: str, rows: List[dict[str, Any]], discarded: int) -> None:
    """Print human-readable statistics."""
    clones = sum(1 for r in rows if r.get("label") == 1)
    non_clones = sum(1 for r in rows if r.get("label") == 0)
    print(f"=== {name} ===")
    print(f"Output file: {path}")
    print(f"Records kept: {len(rows)} (clones={clones}, non-clones={non_clones})")
    print(f"Records discarded: {discarded}")


def main() -> None:
    """CLI entry: filter both corpora."""
    parser = argparse.ArgumentParser(description="Build Java–Python filtered datasets.")
    parser.parse_args()

    for label, raw_path, out_path in (
        ("XLCoST (java_xl.json)", RAW_JAVA_XL_PATH, DATA_JAVA_PYTHON_XL_PATH),
        ("CodeNet (java_cn.json)", RAW_JAVA_CN_PATH, DATA_JAVA_PYTHON_CN_PATH),
    ):
        records = _load_json_array(raw_path)
        kept, discarded = _filter_dataset(records)
        _write_output(out_path, kept)
        _summarize(label, out_path, kept, discarded)
        print()


if __name__ == "__main__":
    main()
