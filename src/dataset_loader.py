"""
Load filtered Java-Python pair records from JSON files under data/.
"""

from __future__ import annotations

import json
import os
from typing import Any, Iterator, List

from src.constants import DATASET_FILE_MAP
from src.logger import get_logger

logger = get_logger(__name__)


class DatasetLoader:
    """
    Resolve dataset paths and load pre-normalized records for experiments.

    Required keys are pair_id, codeA, codeB, label, and dataset.
    Additional metadata fields are preserved and passed through unchanged.
    """

    def __init__(self, dataset_name: str) -> None:
        """
        Args:
            dataset_name: Logical dataset key (e.g., ``xlcost``, ``codenet``).
        """
        self.dataset_name = dataset_name
        if dataset_name not in DATASET_FILE_MAP:
            keys = ", ".join(sorted(DATASET_FILE_MAP))
            raise KeyError(f"Unknown dataset {dataset_name!r}. Expected one of: {keys}")
        self._path = DATASET_FILE_MAP[dataset_name]

    def load(self) -> List[dict[str, Any]]:
        """
        Read the JSON file and return pre-normalized record dicts.

        Returns:
            List of dataset records. Each row must already contain required keys.

        Raises:
            FileNotFoundError: If the expected file is missing (with guidance to run
                ``prepare_dataset.py`` when applicable).
            ValueError: If rows are malformed or not normalized.
        """
        if not os.path.isfile(self._path):
            hint = ""
            if self.dataset_name in ("xlcost", "codenet"):
                hint = " Run `python prepare_dataset.py` from the project root to build it."
            raise FileNotFoundError(
                f"Dataset file not found: {self._path}.{hint}"
            )

        with open(self._path, encoding="utf-8") as f:
            raw = json.load(f)

        if not isinstance(raw, list):
            raise ValueError(f"Expected a JSON array in {self._path}")

        required_keys = ("pair_id", "codeA", "codeB", "label", "dataset")
        records: List[dict[str, Any]] = []
        for index, item in enumerate(raw):
            if not isinstance(item, dict):
                raise ValueError(f"Expected object at index {index} in {self._path}")

            missing = [k for k in required_keys if k not in item]
            if missing:
                raise ValueError(
                    f"Record at index {index} in {self._path} is missing required "
                    f"keys: {missing}. Run `python prepare_dataset.py` from the project root."
                )

            try:
                label = int(item["label"])
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"Invalid label at index {index} in {self._path}: {exc}"
                ) from exc

            if label not in (0, 1):
                raise ValueError(
                    f"Invalid label value at index {index} in {self._path}: {label}. "
                    "Expected 0 or 1."
                )

            if not isinstance(item["codeA"], str) or not isinstance(item["codeB"], str):
                raise ValueError(
                    f"Invalid code field type at index {index} in {self._path}. "
                    "Expected codeA/codeB to be strings."
                )

            if str(item["dataset"]) != self.dataset_name:
                raise ValueError(
                    f"Dataset mismatch at index {index} in {self._path}: "
                    f"dataset={item['dataset']!r}, expected {self.dataset_name!r}."
                )

            records.append(item)

        clones = sum(1 for r in records if int(r["label"]) == 1)
        non_clones = sum(1 for r in records if int(r["label"]) == 0)
        logger.info(
            "Loaded %s pairs from %s (clones=%s, non-clones=%s)",
            len(records),
            self._path,
            clones,
            non_clones,
        )
        return records

    def iter_records(self) -> Iterator[dict[str, Any]]:
        """Yield records from :meth:`load` without caching (reloads file each call)."""
        yield from self.load()
