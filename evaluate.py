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
from typing import Dict, Iterable, List, Optional, Tuple

_PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.constants import CLONE, NOT_CLONE, PROJECT_ROOT  # noqa: E402

_KNOWN_DATASETS: Tuple[str, ...] = ("codenet", "xlcost")


def _iter_csv_files(results_dir: str) -> List[str]:
    """Recursively collect CSV paths."""
    found: List[str] = []
    for dirpath, _dirnames, filenames in os.walk(results_dir):
        for name in filenames:
            if name.lower().endswith(".csv"):
                found.append(os.path.join(dirpath, name))
    return sorted(found)


def _parse_pipeline_model_dataset(path: str) -> Tuple[str, str, str]:
    """
    Infer (pipeline, model, dataset) from path segments and filename.

    Expected layout: ``.../output/<pipeline>/results_<model_alias>_<dataset>.csv`` where
    ``dataset`` is one of the known single-token dataset keys.
    """
    basename = os.path.basename(path)
    parent = os.path.basename(os.path.dirname(path))
    pipeline = parent
    model = "unknown"
    dataset = "unknown"
    if basename.startswith("results_") and basename.endswith(".csv"):
        core = basename[len("results_") : -len(".csv")]
        for ds in _KNOWN_DATASETS:
            suffix = "_" + ds
            if core.endswith(suffix):
                model = core[: -len(suffix)]
                dataset = ds
                break
    return pipeline, model, dataset


def _row_metrics(rows: Iterable[dict[str, str]]) -> Dict[str, Any]:
    """Compute confusion counts and derived metrics."""
    tp = tn = fp = fn = 0
    total = 0
    clones = 0
    non_clones = 0
    for row in rows:
        total += 1
        try:
            gt = int(row.get("ground_truth", -1))
        except ValueError:
            gt = -1
        pred_raw = str(row.get("predicted_label", "")).strip().upper()
        if pred_raw in ("NOT CLONE", "NON_CLONE"):
            pred_raw = NOT_CLONE
        if pred_raw == CLONE:
            pred = 1
        elif pred_raw == NOT_CLONE:
            pred = 0
        else:
            pred = -1  # ERROR or unknown

        if gt == 1:
            clones += 1
        elif gt == 0:
            non_clones += 1

        if pred == -1:
            if gt == 1:
                fn += 1
            elif gt == 0:
                fp += 1
            continue

        if gt == 1 and pred == 1:
            tp += 1
        elif gt == 1 and pred == 0:
            fn += 1
        elif gt == 0 and pred == 1:
            fp += 1
        elif gt == 0 and pred == 0:
            tn += 1

    correct = tp + tn
    accuracy = correct / total if total else 0.0
    prec_denom = tp + fp
    rec_denom = tp + fn
    precision = tp / prec_denom if prec_denom else 0.0
    recall = tp / rec_denom if rec_denom else 0.0
    f1_denom = precision + recall
    f1 = (2 * precision * recall / f1_denom) if f1_denom else 0.0

    return {
        "total": total,
        "clones": clones,
        "non_clones": non_clones,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def _evaluate_file(path: str) -> Dict[str, Any]:
    """Load one CSV and compute metrics plus inferred metadata."""
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    pipeline, model, dataset = _parse_pipeline_model_dataset(path)
    meta = _row_metrics(rows)
    return {
        "file": path,
        "pipeline": pipeline,
        "model": model,
        "dataset": dataset,
        **meta,
    }


def _filter_by_pipeline(rows: List[Dict[str, Any]], pipeline: Optional[str]) -> List[Dict[str, Any]]:
    if not pipeline:
        return rows
    return [r for r in rows if r["pipeline"] == pipeline]


def _print_table(rows: List[Dict[str, Any]]) -> None:
    """Pretty-print comparison table."""
    header = (
        f"{'pipeline':10} | {'model':14} | {'dataset':8} | "
        f"{'acc':>7} | {'prec':>7} | {'rec':>7} | {'f1':>7} | "
        f"{'tot':>5} | {'tp':>3} | {'tn':>3} | {'fp':>3} | {'fn':>3}"
    )
    print(header)
    print("-" * len(header))
    for r in rows:
        print(
            f"{r['pipeline']:10} | {r['model']:14} | {r['dataset']:8} | "
            f"{r['accuracy']:7.4f} | {r['precision']:7.4f} | {r['recall']:7.4f} | {r['f1']:7.4f} | "
            f"{r['total']:5d} | {r['tp']:3d} | {r['tn']:3d} | {r['fp']:3d} | {r['fn']:3d}"
        )


def _write_report_csv(path: str, rows: List[Dict[str, Any]]) -> None:
    """Persist aggregated metrics."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fieldnames = [
        "pipeline",
        "model",
        "dataset",
        "accuracy",
        "precision",
        "recall",
        "f1",
        "total",
        "tp",
        "tn",
        "fp",
        "fn",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r[k] for k in fieldnames})


def _write_markdown_summary(path: str, rows: List[Dict[str, Any]]) -> None:
    """Optional markdown table for quick reading."""
    lines = [
        "# Evaluation summary",
        "",
        "| pipeline | model | dataset | accuracy | precision | recall | f1 | total |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        lines.append(
            f"| {r['pipeline']} | {r['model']} | {r['dataset']} | "
            f"{r['accuracy']:.4f} | {r['precision']:.4f} | {r['recall']:.4f} | "
            f"{r['f1']:.4f} | {r['total']} |"
        )
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main() -> None:
    """CLI for scanning CSV outputs and writing reports."""
    parser = argparse.ArgumentParser(description="Evaluate experiment CSV outputs.")
    parser.add_argument(
        "--results_dir",
        default=os.path.join(PROJECT_ROOT, "output"),
        help="Directory to scan recursively for result CSV files.",
    )
    parser.add_argument(
        "--pipeline",
        default=None,
        help="If set, only include CSVs stored under this pipeline subfolder name.",
    )
    parser.add_argument(
        "--file",
        default=None,
        help="Evaluate a single CSV instead of scanning a directory.",
    )
    parser.add_argument(
        "--write_markdown",
        action="store_true",
        help="Also write reports/evaluation_summary_<timestamp>.md",
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

    reports = _filter_by_pipeline(reports, args.pipeline)
    if not reports:
        print("No matching results after filtering.")
        sys.exit(1)

    _print_table(reports)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    reports_dir = os.path.join(PROJECT_ROOT, "reports")
    csv_out = os.path.join(reports_dir, f"evaluation_report_{stamp}.csv")
    _write_report_csv(csv_out, reports)
    print(f"\nWrote detailed report CSV: {csv_out}")

    if args.write_markdown:
        md_out = os.path.join(reports_dir, f"evaluation_summary_{stamp}.md")
        _write_markdown_summary(md_out, reports)
        print(f"Wrote markdown summary: {md_out}")


if __name__ == "__main__":
    main()
