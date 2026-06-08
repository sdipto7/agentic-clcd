from __future__ import annotations

import csv
import os
from datetime import datetime
from typing import Any, Dict

from src.core.constants import OUTPUT_DIR_BY_PIPELINE


def save_token_usage_data(
    pipeline: str,
    model_alias: str,
    dataset: str,
    pairs: int,
    elapsed_seconds: float,
    token_usage: Dict[str, Any],
    run_status: str = "success",
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
            successful_requests, prompt_tokens, completion_tokens, total_tokens.
        run_status: Status of the run (e.g., "success", "failed").
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
        "run_status",
        "successful_requests",
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
    ]

    row = {
        "timestamp_utc": datetime.utcnow().isoformat(timespec="seconds"),
        "pipeline": pipeline,
        "model": model_alias,
        "dataset": dataset,
        "pairs": pairs,
        "elapsed_seconds": f"{elapsed_seconds:.6f}",
        "run_status": run_status,
        "successful_requests": int(token_usage.get("successful_requests", 0) or 0),
        "prompt_tokens": int(token_usage.get("prompt_tokens", 0) or 0),
        "completion_tokens": int(token_usage.get("completion_tokens", 0) or 0),
        "total_tokens": int(token_usage.get("total_tokens", 0) or 0),
    }

    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()

        writer.writerow(row)
