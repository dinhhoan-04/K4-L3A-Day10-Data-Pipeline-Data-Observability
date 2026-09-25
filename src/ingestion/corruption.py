from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import write_json


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path: Path | str) -> pd.DataFrame:
    """Inject 6 controlled data corruptions into clean DataFrame to test observability & resilience."""
    if df.empty:
        return df.copy()

    corrupted_df = df.copy()
    logs: list[dict[str, Any]] = []

    # 1. Drop latest records (20% of newest papers)
    corrupted_df = corrupted_df.sort_values(by="published", ascending=False).reset_index(drop=True)
    drop_count = max(1, int(len(corrupted_df) * 0.2))
    dropped_papers = corrupted_df.iloc[:drop_count]["paper_id"].tolist()
    corrupted_df = corrupted_df.iloc[drop_count:].reset_index(drop=True)
    logs.append({
        "corruption_type": "drop_latest_records",
        "affected_rows": drop_count,
        "affected_paper_ids": dropped_papers,
        "details": f"Dropped {drop_count} newest records to simulate missing ingestion stream."
    })

    if len(corrupted_df) == 0:
        write_json(Path(output_log_path), logs)
        return corrupted_df

    # 2. Blank summary (clear summary on 2 rows)
    blank_idx = [0, min(1, len(corrupted_df) - 1)]
    blank_ids = corrupted_df.iloc[blank_idx]["paper_id"].tolist()
    for idx in blank_idx:
        corrupted_df.at[idx, "summary"] = ""
        corrupted_df.at[idx, "summary_chars"] = 0
    logs.append({
        "corruption_type": "blank_summary",
        "affected_rows": len(blank_idx),
        "affected_paper_ids": blank_ids,
        "details": "Blanked out summary fields."
    })

    # 3. Inject noise into summary on 2 rows
    noise_idx = [min(2, len(corrupted_df) - 1), min(3, len(corrupted_df) - 1)]
    noise_ids = corrupted_df.iloc[noise_idx]["paper_id"].tolist()
    for idx in noise_idx:
        corrupted_df.at[idx, "summary"] = "NOISE_GARBAGE_### " * 5 + str(corrupted_df.at[idx, "summary"])
        corrupted_df.at[idx, "summary_chars"] = len(corrupted_df.at[idx, "summary"])
    logs.append({
        "corruption_type": "inject_noise",
        "affected_rows": len(noise_idx),
        "affected_paper_ids": noise_ids,
        "details": "Injected random text noise into summaries."
    })

    # 4. Truncate title on 2 rows (< 8 chars)
    trunc_idx = [min(4, len(corrupted_df) - 1), min(5, len(corrupted_df) - 1)]
    trunc_ids = corrupted_df.iloc[trunc_idx]["paper_id"].tolist()
    for idx in trunc_idx:
        corrupted_df.at[idx, "title"] = str(corrupted_df.at[idx, "title"])[:5]
    logs.append({
        "corruption_type": "truncate_title",
        "affected_rows": len(trunc_idx),
        "affected_paper_ids": trunc_ids,
        "details": "Truncated paper titles down to 5 characters."
    })

    # 5. Stale date (shift publication date 365 days back)
    stale_idx = [min(6, len(corrupted_df) - 1), min(7, len(corrupted_df) - 1), min(8, len(corrupted_df) - 1)]
    stale_ids = corrupted_df.iloc[stale_idx]["paper_id"].tolist()
    for idx in stale_idx:
        pub_str = str(corrupted_df.at[idx, "published"])
        try:
            pub_dt = datetime.strptime(pub_str[:10], "%Y-%m-%d") - timedelta(days=365)
            corrupted_df.at[idx, "published"] = pub_dt.strftime("%Y-%m-%d")
        except Exception:
            corrupted_df.at[idx, "published"] = "2024-01-01"
        corrupted_df.at[idx, "age_days"] = int(corrupted_df.at[idx, "age_days"]) + 365
    logs.append({
        "corruption_type": "stale_date",
        "affected_rows": len(stale_idx),
        "affected_paper_ids": stale_ids,
        "details": "Shifted publication dates back by 365 days to simulate stale data."
    })

    # 6. Duplicate rows (duplicate first 2 rows)
    dup_rows = corrupted_df.iloc[:2].copy()
    corrupted_df = pd.concat([corrupted_df, dup_rows], ignore_index=True)
    logs.append({
        "corruption_type": "duplicate_rows",
        "affected_rows": len(dup_rows),
        "affected_paper_ids": dup_rows["paper_id"].tolist(),
        "details": "Duplicated top rows to test uniqueness constraints."
    })

    # Rebuild text_for_embedding for all rows
    for idx in range(len(corrupted_df)):
        t = corrupted_df.at[idx, "title"]
        a = corrupted_df.at[idx, "authors_joined"]
        p = corrupted_df.at[idx, "published"]
        c = corrupted_df.at[idx, "categories_joined"]
        s = corrupted_df.at[idx, "summary"]
        corrupted_df.at[idx, "text_for_embedding"] = f"Title: {t}\nAuthors: {a}\nPublished: {p}\nCategories: {c}\nSummary: {s}"

    out_path = Path(output_log_path)
    write_json(out_path, logs)
    return corrupted_df

