from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EvaluationCase:
	case_id: str
	question: str
	reference_answer: str
	expected_keywords: tuple[str, ...]


def default_dataset_path() -> Path:
	return Path(__file__).resolve().parents[1] / "tools" / "knowledge" / "dataset.csv"


def load_cases(path: str | Path | None = None) -> list[EvaluationCase]:
	"""Load retrieval evaluation cases from a CSV file."""
	dataset_path = Path(path) if path else default_dataset_path()
	if not dataset_path.exists():
		raise FileNotFoundError(f"Evaluation dataset not found: {dataset_path}")

	with dataset_path.open(newline="", encoding="utf-8-sig") as handle:
		reader = csv.DictReader(handle)
		required = {"id", "question", "reference_answer", "expected_keywords"}
		missing = required - set(reader.fieldnames or [])
		if missing:
			raise ValueError(f"Dataset is missing columns: {', '.join(sorted(missing))}")

		cases = []
		for row in reader:
			question = (row.get("question") or "").strip()
			if not question:
				continue
			keywords = tuple(
				item.strip().lower()
				for item in (row.get("expected_keywords") or "").split("|")
				if item.strip()
			)
			cases.append(
				EvaluationCase(
					case_id=(row.get("id") or str(len(cases) + 1)).strip(),
					question=question,
					reference_answer=(row.get("reference_answer") or "").strip(),
					expected_keywords=keywords,
				)
			)
		return cases
