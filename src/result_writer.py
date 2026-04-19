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
        self._tp = 0
        self._tn = 0
        self._fp = 0
        self._fn = 0
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

        pos_pred = predicted == CLONE
        pos_truth = ground_truth == 1

        if predicted == ERROR:
            # Treat unresolved output as harming both precision and recall buckets.
            if pos_truth:
                self._fn += 1
            else:
                self._fp += 1
            return

        if pos_truth and pos_pred:
            self._tp += 1
        elif pos_truth and not pos_pred:
            self._fn += 1
        elif not pos_truth and pos_pred:
            self._fp += 1
        else:
            self._tn += 1

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
        total = self._total
        accuracy = self._correct / total if total else 0.0
        tp, fp, fn = self._tp, self._fp, self._fn
        prec_denom = tp + fp
        rec_denom = tp + fn
        precision = tp / prec_denom if prec_denom else 0.0
        recall = tp / rec_denom if rec_denom else 0.0
        f1_denom = precision + recall
        f1 = (2 * precision * recall / f1_denom) if f1_denom else 0.0

        return {
            "total": total,
            "correct": self._correct,
            "tp": tp,
            "tn": self._tn,
            "fp": fp,
            "fn": fn,
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }
