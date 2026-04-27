"""
Append per-pair experiment rows to CSV and accumulate confusion-matrix counts.
"""

from __future__ import annotations

import csv
import os
from typing import Any

from src.constants import CLONE, ERROR, LABEL_TO_VERDICT, NOT_CLONE


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
        self._true_positive = 0
        self._true_negative = 0
        self._false_positive = 0
        self._false_negative = 0
        self._total = 0
        self._correct = 0

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

    def _update_counts(self, ground_truth: int, predicted: str) -> None:
        """Update running confusion counts from label and verdict."""
        self._total += 1
        expected = LABEL_TO_VERDICT.get(ground_truth, NOT_CLONE)
        if predicted == expected:
            self._correct += 1

        is_predicted_clone = predicted == CLONE
        is_ground_truth_positive = ground_truth == 1

        if predicted == ERROR:
            # Treat unresolved output as harming both precision and recall buckets.
            if is_ground_truth_positive:
                self._false_negative += 1
            else:
                self._false_positive += 1
            return

        if is_ground_truth_positive and is_predicted_clone:
            self._true_positive += 1
        elif is_ground_truth_positive and not is_predicted_clone:
            self._false_negative += 1
        elif not is_ground_truth_positive and is_predicted_clone:
            self._false_positive += 1
        else:
            self._true_negative += 1


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

        self._update_counts(ground_truth, predicted_label)


    def get_summary(self) -> dict[str, Any]:
        """
        Return aggregate metrics for everything recorded by this writer instance.

        Returns:
            Dict with total, correct, tp, tn, fp, fn, accuracy, precision, recall, f1.
        """
        accuracy = self._correct / self._total if self._total else 0.0

        precision_denominator = self._true_positive + self._false_positive
        precision = self._true_positive / precision_denominator if precision_denominator else 0.0

        recall_denominator = self._true_positive + self._false_negative
        recall = self._true_positive / recall_denominator if recall_denominator else 0.0
 
        f1_denominator = precision + recall
        f1 = (2 * precision * recall / f1_denominator) if f1_denominator else 0.0

        return {
            "total": self._total,
            "correct": self._correct,
            "tp": self._true_positive,
            "tn": self._true_negative,
            "fp": self._false_positive,
            "fn": self._false_negative,
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }
