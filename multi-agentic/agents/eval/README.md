# Retrieval evaluation

Add one row per evaluation question to `agents/tools/knowledge/dataset.csv`:

```csv
id,question,reference_answer,expected_keywords
case-1,What is credential stuffing?,An attack using leaked passwords.,credential stuffing|leaked passwords
```

Ingest the knowledge documents first:

```powershell
.\.venv\Scripts\python -m agents.eval.ingest agents/tools/knowledge/data.md
```

Run the local retrieval evaluation:

```powershell
.\.venv\Scripts\python -m agents.eval.ragas
```

The report is written to `.artifacts/retrieval-report.json`. This baseline measures expected-keyword recall in retrieved context. It is an independent quality signal and does not grant or deny Confluence publication permission. Model-based RAGAS metrics can be added after the dataset and retrieval baseline are stable.
