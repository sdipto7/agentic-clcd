import os
import csv
from typing import Any, List

from src.constants import ERROR, OUTPUT_DIR_BY_PIPELINE, RESULTS_CSV_PREFIX


def results_csv_path(pipeline: str, model_alias: str, dataset: str) -> str:
    """
    Build the output path for the results CSV of a single run.

    The file is placed under the pipeline-specific output directory and follows
    the naming pattern: ``{RESULTS_CSV_PREFIX}_{model_alias}_{dataset}.csv``.

    Args:
        pipeline: Pipeline name (key into ``OUTPUT_DIR_BY_PIPELINE``).
        model_alias: Short model identifier used in the filename.
        dataset: Dataset name used in the filename.

    Returns:
        Absolute path to the results CSV file for this run.
    """
    out_dir = OUTPUT_DIR_BY_PIPELINE[pipeline]
    fname = f"{RESULTS_CSV_PREFIX}_{model_alias}_{dataset}.csv"

    return os.path.join(out_dir, fname)


def _load_success_and_error_pair_ids(csv_path: str) -> tuple[set[str], set[str]]:
    """
    Load existing completion status from a results CSV.

    Reads ``csv_path`` (if it exists) and partitions ``pair_id`` values into:
    - successful: rows whose ``predicted_label`` is not ERROR
    - errors: rows whose ``predicted_label`` is ERROR

    If a ``pair_id`` appears multiple times with mixed outcomes, it is treated as
    successful (i.e., it will not be retried).

    Args:
        csv_path: Path to an existing results CSV.

    Returns:
        A tuple ``(successful_pair_ids, error_pair_ids)``.
        If the file does not exist, both sets are empty.
    """
    successful: set[str] = set()
    errors: set[str] = set()

    if not os.path.isfile(csv_path):
        return successful, errors

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            pair_id = str(row.get("pair_id", "")).strip()
            if not pair_id:
                continue

            pred = str(row.get("predicted_label", "")).strip().upper()
            if pred == ERROR:
                errors.add(pair_id)
            else:
                successful.add(pair_id)

    # If a pair_id appears as both ERROR and non-ERROR (duplicates), treat it as successful and do not retry it.
    errors -= successful
 
    return successful, errors


def _drop_pairs_from_results_csv(csv_path: str, drop_pair_ids: set[str]) -> None:
    """
    Remove selected pair rows from an existing results CSV (in-place).

    This rewrites the CSV at ``csv_path`` and drops any row whose ``pair_id`` is in
    ``drop_pair_ids``. It is used to delete stale ERROR rows before retrying those pairs.

    No-op if the file does not exist, if ``drop_pair_ids`` is empty, or if the CSV
    has no header/fieldnames.

    Args:
        csv_path: Path to the results CSV to rewrite.
        drop_pair_ids: Set of ``pair_id`` values to remove from the CSV.

    Returns:
        None.
    """
    if not os.path.isfile(csv_path) or not drop_pair_ids:
        return

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        fieldnames = reader.fieldnames
        if not fieldnames:
            return

        kept_rows = [
            row
            for row in reader
            if str(row.get("pair_id", "")).strip() not in drop_pair_ids
        ]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(kept_rows)


def prepare_records_to_run(records: List[dict[str, Any]], csv_path: str) -> List[dict[str, Any]]:
    """
    Determine which records still need processing based on an existing results CSV.

    - Skips records whose ``pair_id`` already has a non-ERROR result.
    - If any ``pair_id`` previously resulted in ERROR, removes those rows from the
      CSV so reruns will replace them with fresh outputs.

    Args:
        records: Input records to consider. Each record must contain a ``pair_id`` key.
        csv_path: Path to the results CSV for this pipeline/model/dataset run.

    Returns:
        A list of records that should be processed in this run.
    """
    successful_pair_ids, error_pair_ids = _load_success_and_error_pair_ids(csv_path)
    records_to_run = [r for r in records if r["pair_id"] not in successful_pair_ids]

    if error_pair_ids:
        _drop_pairs_from_results_csv(csv_path, error_pair_ids)

    return records_to_run