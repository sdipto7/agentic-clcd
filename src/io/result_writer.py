"""
Append per-pair experiment rows to CSV and accumulate confusion-matrix counts.
"""

from __future__ import annotations

import csv
import os
from typing import Any

from src.core.constants import CLONE, ERROR, LABEL_TO_VERDICT, NOT_CLONE


class ResultWriter:
    """
    Write detection results for one pipeline/model/dataset run and track metrics.

    CSV schema matches downstream evaluation expectations.
    """

    def __init__(
        self,
        csv_path: str,
        pipeline: str,
        model_alias: str,
    ) -> None:
        """
        Args:
            csv_path: Absolute path to the CSV file to create or append.
            pipeline: Pipeline name constant.
            model_alias: Short model key (e.g., ``deepseek_v3``).
        """
        self.csv_path = csv_path
        self.pipeline = pipeline
        self.model_alias = model_alias

        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        self._file_exists = os.path.isfile(csv_path)
        self._fieldnames = [
            "pair_id",
            "dataset",
            "ground_truth",
            "predicted_label",
            "confidence",
            "reasoning",
            "pipeline",
            "model",
            "processing_time_seconds",
        ]


    def record_result(
        self,
        pair_id: str,
        dataset: str,
        ground_truth: int,
        predicted_label: str,
        confidence: float,
        reasoning: str,
        processing_time_seconds: float,
    ) -> None:
        """
        Append one row and refresh internal counters.

        Args:
            pair_id: Stable identifier for the pair.
            dataset: Dataset name.
            ground_truth: 1 clone, 0 non-clone.
            predicted_label: CLONE, NOT_CLONE, or ERROR.
            confidence: Model confidence in [0, 1].
            reasoning: Short textual rationale.
            processing_time_seconds: Wall time spent on this pair.
        """
        row = {
            "pair_id": pair_id,
            "dataset": dataset,
            "ground_truth": ground_truth,
            "predicted_label": predicted_label,
            "confidence": f"{confidence:.6f}",
            "reasoning": reasoning.replace("\n", " ").strip(),
            "pipeline": self.pipeline,
            "model": self.model_alias,
            "processing_time_seconds": f"{processing_time_seconds:.6f}",
        }

        write_header = not self._file_exists
        with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self._fieldnames)

            if write_header:
                writer.writeheader()
                self._file_exists = True

            writer.writerow(row)
