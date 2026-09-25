from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import first_sentence, write_json


def build_test_set(df: pd.DataFrame, output_path: Path | str) -> list[dict[str, Any]]:
    """Build a benchmark test set containing 10 ground-truth questions across 4 categories."""
    if df.empty or len(df) < 3:
        raise ValueError("DataFrame is empty or has too few rows to build test set.")

    records = df.to_dict(orient="records")
    test_items: list[dict[str, Any]] = []

    types_cycle = ["summary", "authors", "date", "categories"]

    for i in range(10):
        paper = records[i % len(records)]
        q_type = types_cycle[i % len(types_cycle)]
        paper_id = paper["paper_id"]
        title = paper["title"]

        if q_type == "summary":
            question = f"What is the summary of the paper '{title}'?"
            ground_truth = first_sentence(paper["summary"])
        elif q_type == "authors":
            question = f"Who authored the paper '{title}'?"
            ground_truth = paper["authors_joined"]
        elif q_type == "date":
            question = f"When was the paper '{title}' published?"
            ground_truth = paper["published"]
        else:  # categories
            question = f"What categories does the paper '{title}' belong to?"
            ground_truth = paper["categories_joined"]

        test_items.append(
            {
                "id": f"eval_{i+1:03d}",
                "question_type": q_type,
                "question": question,
                "ground_truth": ground_truth,
                "ground_truth_doc_ids": [paper_id],
            }
        )

    out_path = Path(output_path)
    write_json(out_path, test_items)
    return test_items

