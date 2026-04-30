from __future__ import annotations

import csv
import os
from datetime import datetime
from typing import Any, Dict

from src.constants import OUTPUT_DIR_BY_PIPELINE


def save_token_usage_data(
    pipeline: str,
    model_alias: str,
    dataset: str,
    pairs: int,
    elapsed_seconds: float,
    token_usage: Dict[str, Any],
    metrics: Dict[str, Any],
) -> None:
    """
    Append one run-level token-usage row to a CSV file.

    Intended to be called once per workflow run. Appends a single
    row to a csv file and writes the header only if the file does not exist.

    Args:
        pipeline: Pipeline name (e.g., direct/algo_based/agentic).
        model_alias: Model alias for the run.
        dataset: Dataset name for the run.
        pairs: Number of pairs processed.
        elapsed_seconds: Total run time in seconds.
        token_usage: Aggregated usage counters (missing keys default to 0):
            successful_requests, prompt_tokens, completion_tokens, total_tokens, total_cost.
        metrics: Run summary metrics (missing keys default to 0.0):
            accuracy, precision, recall, f1.
    Returns:
        None.
    """
    csv_path = os.path.join(OUTPUT_DIR_BY_PIPELINE[pipeline], "token_usage.csv")
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    file_exists = os.path.isfile(csv_path)

    fieldnames = [
        "timestamp_utc",
        "pipeline",
        "model",
        "dataset",
        "pairs",
        "elapsed_seconds",
        "successful_requests",
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
        "total_cost_usd",
        "accuracy",
        "precision",
        "recall",
        "f1",
    ]

    row = {
        "timestamp_utc": datetime.utcnow().isoformat(timespec="seconds"),
        "pipeline": pipeline,
        "model": model_alias,
        "dataset": dataset,
        "pairs": pairs,
        "elapsed_seconds": f"{elapsed_seconds:.6f}",
        "successful_requests": int(token_usage.get("successful_requests", 0) or 0),
        "prompt_tokens": int(token_usage.get("prompt_tokens", 0) or 0),
        "completion_tokens": int(token_usage.get("completion_tokens", 0) or 0),
        "total_tokens": int(token_usage.get("total_tokens", 0) or 0),
        "total_cost_usd": f"{float(token_usage.get('total_cost', 0.0) or 0.0):.6f}",
        "accuracy": f"{float(metrics.get('accuracy', 0.0) or 0.0):.6f}",
        "precision": f"{float(metrics.get('precision', 0.0) or 0.0):.6f}",
        "recall": f"{float(metrics.get('recall', 0.0) or 0.0):.6f}",
        "f1": f"{float(metrics.get('f1', 0.0) or 0.0):.6f}",
    }

    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()

        writer.writerow(row)
