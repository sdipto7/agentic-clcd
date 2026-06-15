#!/usr/bin/env python3
"""
Offline evaluation of pipeline CSV outputs under output/ (or a custom directory).
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from datetime import datetime
from typing import Dict, Iterable, List, Tuple

_PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.core.constants import CLONE, NOT_CLONE, PROJECT_ROOT  # noqa: E402


def _iter_csv_files(results_dir: str) -> List[str]:
    """
    Recursively find output CSV files under a directory.

    This scanner is intentionally strict: it only return CSV files whose filename
    matches `results_*.csv` (case-insensitive). This avoids accidentally
    including non-result artifacts such as `token_usage.csv`.

    Args:
        results_dir: Root directory to walk recursively (e.g., `output/`).

    Returns:
        A sorted list of absolute file paths to matching `results_*.csv` files.
    """
    csv_files: List[str] = []

    for dirpath, _dirnames, filenames in os.walk(results_dir):
        for name in filenames:
            if name.lower().startswith("results_") and name.lower().endswith(".csv"):
                csv_files.append(os.path.join(dirpath, name))

    return sorted(csv_files)


def _extract_pipeline_model_dataset_from_path(path: str) -> Tuple[str, str, str]:
    """
    Extract (pipeline, model, dataset) from a results CSV file path.

    Parsing rules:
    - `pipeline` is the name of the parent directory containing the CSV.
      Example: `.../output/agentic/results_x_y.csv` -> pipeline = `agentic`.
    - `model` and `dataset` are extracted from the filename if it follows the pattern
      `results_<model_alias>_<dataset>.csv`.

    If the filename does not match the expected pattern (missing prefix/suffix or
    missing underscore in the stem), `model` and `dataset` default to `"unknown"`.

    Args:
        path: Path to a CSV file.

    Returns:
        A tuple (pipeline, model, dataset) where each element is a string.
    """
    basename = os.path.basename(path)
    parent = os.path.basename(os.path.dirname(path))
    pipeline = parent
    model = "unknown"
    dataset = "unknown"

    if basename.startswith("results_") and basename.endswith(".csv"):
        model_dataset_part = basename[len("results_") : -len(".csv")]
        if "_" in model_dataset_part:
            model, dataset = model_dataset_part.rsplit("_", 1)

    return pipeline, model, dataset


def _compute_classification_metrics(rows: Iterable[dict[str, str]]) -> Dict[str, Any]:
    """
    Compute classification counts and standard metrics from CSV rows.

    Each row is expected to contain:
    - ground_truth: integer label (1 for clone, 0 for not-clone). Missing/invalid
      values are treated as -1 (unknown) and won't match TP/TN/FP/FN conditions.
    - predicted_label: a string label. It is normalized by uppercasing and mapping
      common variants:
        - CLONE constant -> positive class
        - NOT_CLONE constant -> negative class

    Confusion counting behavior:
    - true_positive, true_negative, false_positive, and false_negative are
      accumulated for recognized predictions (clone / not-clone).

    Metrics:
    - accuracy = (true_positive + true_negative) / total
    - precision = true_positive / (true_positive + false_positive)
    - recall = true_positive / (true_positive + false_negative)
    - f1_score = 2 * precision * recall / (precision + recall)

    Args:
        rows: Iterable of dict-like CSV rows.

    Returns:
        A dict containing confusion counts and derived metrics:
        total, clones, non_clones, true_positive, true_negative,
        false_positive, false_negative, accuracy, precision, recall,
        f1_score.
    """
    true_positive = 0
    true_negative = 0
    false_positive = 0
    false_negative = 0
    total = 0
    clones = 0
    non_clones = 0
    
    for row in rows:
        total += 1

        try:
            ground_truth = int(row.get("ground_truth", -1))
        except ValueError:
            ground_truth = -1

        pred_raw = str(row.get("predicted_label", "")).strip().upper()
        if pred_raw in ("NOT CLONE", "NON_CLONE"):
            pred_raw = NOT_CLONE

        if pred_raw == CLONE:
            predicted_label = 1
        elif pred_raw == NOT_CLONE:
            predicted_label = 0

        else:
            predicted_label = -1  # ERROR or unknown

        if ground_truth == 1:
            clones += 1
        elif ground_truth == 0:
            non_clones += 1

        if predicted_label == -1:
            if ground_truth == 1:
                false_negative += 1
            elif ground_truth == 0:
                false_positive += 1
            continue

        if ground_truth == 1 and predicted_label == 1:
            true_positive += 1
        elif ground_truth == 1 and predicted_label == 0:
            false_negative += 1
        elif ground_truth == 0 and predicted_label == 1:
            false_positive += 1
        elif ground_truth == 0 and predicted_label == 0:
            true_negative += 1

    correct = true_positive + true_negative
    accuracy = correct / total if total else 0.0
    precision_denom = true_positive + false_positive
    recall_denom = true_positive + false_negative
    precision = true_positive / precision_denom if precision_denom else 0.0
    recall = true_positive / recall_denom if recall_denom else 0.0
    f1_denom = precision + recall
    f1_score = (2 * precision * recall / f1_denom) if f1_denom else 0.0

    return {
        "total": total,
        "clones": clones,
        "non_clones": non_clones,
        "true_positive": true_positive,
        "true_negative": true_negative,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "accuracy": f"{accuracy:.2f}",
        "precision": f"{precision:.2f}",
        "recall": f"{recall:.2f}",
        "f1_score": f"{f1_score:.2f}",
    }


def _evaluate_file(path: str) -> Dict[str, Any]:
    """
    Evaluate one results CSV file and return a single aggregated report row.

    This function:
    - reads the CSV at path using csv.DictReader
    - infers pipeline, model, and dataset from the file path
    - computes classification counts and metrics across all rows
    - returns a dict that merges the inferred metadata with the computed metrics

    Expected CSV columns:
    - ground_truth: 1 for clone, 0 for not-clone
    - predicted_label: label string that will be normalized by the metrics function

    Args:
        path: Path to a single results CSV file.

    Returns:
        A dictionary with keys:
        file, pipeline, model, dataset,
        total, clones, non_clones,
        true_positive, true_negative, false_positive, false_negative,
        accuracy, precision, recall, f1_score.
    """
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    pipeline, model, dataset = _extract_pipeline_model_dataset_from_path(path)

    metrics = _compute_classification_metrics(rows)

    return {
        "file": path,
        "pipeline": pipeline,
        "model": model,
        "dataset": dataset,
        **metrics,
    }


def _get_report_csv_path(prefix: str = "evaluation_report") -> str:
    """
    Build a timestamped report CSV path under the reports directory.

    Args:
        prefix: Filename prefix to use before the timestamp.

    Returns:
        Full path to a CSV file under PROJECT_ROOT/reports named like
        prefix_YYYYMMDD_HHMMSS.csv.
    """
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    reports_dir = os.path.join(PROJECT_ROOT, "reports")

    return os.path.join(reports_dir, f"{prefix}_{stamp}.csv")


def _write_report_csv(path: str, rows: List[Dict[str, Any]]) -> None:
    """
    Write an aggregated evaluation report CSV to disk.

    The output CSV contains one row per evaluated input file (or per evaluated
    result set), with metadata fields (pipeline, model, dataset) and the computed
    classification metrics and confusion counts.

    The destination directory is created if it does not already exist. The file is
    written with a header row followed by one row per element in rows.

    Args:
        path: Output CSV file path to write (typically under the reports directory).
        rows: List of dictionaries containing the report fields to write. Each dict
            must provide values for the predefined report columns written by this
            function.

    Returns:
        None.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fieldnames = [
        "pipeline",
        "model",
        "dataset",
        "accuracy",
        "precision",
        "recall",
        "f1_score",
        "total",
        "true_positive",
        "true_negative",
        "false_positive",
        "false_negative",
    ]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r[k] for k in fieldnames})


def main() -> None:
    """CLI for scanning CSV outputs and writing reports."""
    parser = argparse.ArgumentParser(description="Evaluate experiment CSV outputs.")
    parser.add_argument(
        "--results_dir",
        required=False,
        default=os.path.join(PROJECT_ROOT, "output"),
        help="Directory to scan recursively for result CSV files.",
    )
    parser.add_argument(
        "--file",
        required=False,
        default=None,
        help="Evaluate a single CSV instead of scanning a directory.",
    )
    args = parser.parse_args()

    if args.file:
        targets = [args.file]
    else:
        targets = _iter_csv_files(args.results_dir)

    if not targets:
        print(f"No CSV files found under {args.results_dir}")
        sys.exit(1)

    reports: List[Dict[str, Any]] = []
    for path in targets:
        reports.append(_evaluate_file(path))

    csv_path = _get_report_csv_path()

    _write_report_csv(csv_path, reports)

    print(f"Detailed CSV report: {csv_path}")


if __name__ == "__main__":
    main()
