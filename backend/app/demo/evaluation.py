"""Detector evaluation against ground-truth labels.

Ground truth maps test unique_key -> "stable" | "flaky" | "consistently_failing".
A prediction is positive when the detector flags the test (flaky
classification or newly-flaky flag); only "flaky" labels count as actual
positives. Labels are used exclusively for evaluation, never for scoring.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvalResult:
    total: int
    true_positives: int
    true_negatives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float


def evaluate(
    predicted_flaky: dict[str, bool],
    ground_truth: dict[str, str],
) -> EvalResult:
    keys = [k for k in ground_truth if k in predicted_flaky]
    tp = tn = fp = fn = 0
    for key in keys:
        actual = ground_truth[key] == "flaky"
        predicted = predicted_flaky[key]
        if actual and predicted:
            tp += 1
        elif not actual and not predicted:
            tn += 1
        elif not actual and predicted:
            fp += 1
        else:
            fn += 1
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    return EvalResult(
        total=len(keys),
        true_positives=tp,
        true_negatives=tn,
        false_positives=fp,
        false_negatives=fn,
        precision=precision,
        recall=recall,
    )
