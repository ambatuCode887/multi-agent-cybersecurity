"""Run the local retrieval evaluation suite against Qdrant."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agents.eval.dataset import load_cases
from agents.eval.ragas_runner import evaluate_retrieval
from agents.tools.functions.retrieve.credential_stuffing import retrieve_knowledge


def main() -> int:
	parser = argparse.ArgumentParser(description="Evaluate retrieval quality")
	parser.add_argument("--dataset", help="Path to an evaluation CSV")
	parser.add_argument("--output", default=".artifacts/retrieval-report.json")
	args = parser.parse_args()

	cases = load_cases(args.dataset)
	if not cases:
		print("No evaluation cases found. Add rows to agents/tools/knowledge/dataset.csv.")
		return 1

	report = evaluate_retrieval(cases, retrieve_knowledge)
	output = Path(args.output)
	output.parent.mkdir(parents=True, exist_ok=True)
	output.write_text(json.dumps(report, indent=2), encoding="utf-8")
	print(json.dumps(report, indent=2))
	return 0


if __name__ == "__main__":
	raise SystemExit(main())

