from __future__ import annotations

from datetime import datetime
import pandas as pd

from ingestion.crossref import PaperRecord
from core.utils import normalize_whitespace


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Clean raw records into a structured DataFrame ready for vector indexing."""
    if not records:
        return pd.DataFrame()

    run_dt_naive = run_date.replace(tzinfo=None) if run_date.tzinfo else run_date

    cleaned_rows = []
    for r in records:
        paper_id = r.paper_id.strip()
        title = normalize_whitespace(r.title)
        summary = normalize_whitespace(r.summary)

        if not paper_id or not title:
            continue

        authors = r.authors if isinstance(r.authors, list) else [r.authors]
        authors = [normalize_whitespace(str(a)) for a in authors if str(a).strip()]
        authors_joined = ", ".join(authors)

        categories = r.categories if isinstance(r.categories, list) else [r.categories]
        categories = [normalize_whitespace(str(c)) for c in categories if str(c).strip()]
        categories_joined = ", ".join(categories)

        primary_category = r.primary_category or (categories[0] if categories else "General")

        pub_str = r.published.strip()
        try:
            pub_dt = datetime.strptime(pub_str[:10], "%Y-%m-%d")
        except Exception:
            pub_dt = datetime(2026, 1, 1)
            pub_str = "2026-01-01"

        age_days = max(0, (run_dt_naive - pub_dt).days)
        summary_chars = len(summary)

        text_for_embedding = (
            f"Title: {title}\n"
            f"Authors: {authors_joined}\n"
            f"Published: {pub_str}\n"
            f"Categories: {categories_joined}\n"
            f"Summary: {summary}"
        )

        cleaned_rows.append(
            {
                "paper_id": paper_id,
                "title": title,
                "summary": summary,
                "authors": authors,
                "categories": categories,
                "primary_category": primary_category,
                "published": pub_str,
                "updated": r.updated,
                "abs_url": r.abs_url,
                "pdf_url": r.pdf_url,
                "comment": r.comment,
                "authors_joined": authors_joined,
                "categories_joined": categories_joined,
                "summary_chars": summary_chars,
                "age_days": age_days,
                "text_for_embedding": text_for_embedding,
            }
        )

    df = pd.DataFrame(cleaned_rows)
    if df.empty:
        return df

    df = df.drop_duplicates(subset=["paper_id"], keep="first")
    df = df.sort_values(by=["published", "paper_id"], ascending=[False, True]).reset_index(drop=True)
    return df

