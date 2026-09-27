from __future__ import annotations

from collections.abc import Callable
from typing import Any

from agents.eval.dataset import EvaluationCase


def evaluate_retrieval(
	cases: list[EvaluationCase],
	retrieve: Callable[..., dict[str, Any]],
	limit: int = 5,
) -> dict[str, Any]:
	"""Evaluate whether retrieved context contains each case's expected keywords."""
	results = []
	for case in cases:
		response = retrieve(case.question, limit=limit)
		context = " ".join(item.get("text", "") for item in response.get("results", [])).lower()
		matched = [keyword for keyword in case.expected_keywords if keyword in context]
		recall = len(matched) / len(case.expected_keywords) if case.expected_keywords else 0.0
		results.append(
			{
				"id": case.case_id,
				"question": case.question,
				"matched_keywords": matched,
				"keyword_recall": recall,
				"retrieved_count": len(response.get("results", [])),
			}
		)

	average = sum(item["keyword_recall"] for item in results) / len(results) if results else 0.0
	return {"case_count": len(results), "average_keyword_recall": average, "cases": results}
