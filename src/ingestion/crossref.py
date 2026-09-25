from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re

import requests

from core.config import Settings
from core.utils import normalize_whitespace, read_json, write_json


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse Crossref API payload or response dict into list of PaperRecord objects."""
    items = []
    if "message" in payload and isinstance(payload["message"], dict):
        items = payload["message"].get("items", [])
    elif "items" in payload:
        items = payload.get("items", [])

    records: list[PaperRecord] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        paper_id = str(item.get("DOI", "")).strip()

        raw_titles = item.get("title", [])
        if isinstance(raw_titles, list) and raw_titles:
            title = str(raw_titles[0]).strip()
        else:
            title = str(raw_titles).strip() if raw_titles else ""
        title = normalize_whitespace(re.sub(r"<[^>]+>", "", title))

        if not paper_id and not title:
            continue

        raw_abstract = str(item.get("abstract", "")).strip()
        summary = normalize_whitespace(re.sub(r"<[^>]+>", "", raw_abstract))

        raw_authors = item.get("author", [])
        authors = []
        if isinstance(raw_authors, list):
            for a in raw_authors:
                if isinstance(a, dict):
                    given = str(a.get("given", "")).strip()
                    family = str(a.get("family", "")).strip()
                    name = f"{given} {family}".strip()
                    if name:
                        authors.append(name)
                elif isinstance(a, str) and a.strip():
                    authors.append(a.strip())

        raw_subjects = item.get("subject", [])
        if isinstance(raw_subjects, list):
            categories = [str(s).strip() for s in raw_subjects if str(s).strip()]
        else:
            categories = [str(raw_subjects).strip()] if raw_subjects else []

        primary_category = categories[0] if categories else "General"

        published = "2026-01-01"
        pub_dict = item.get("published", {})
        if isinstance(pub_dict, dict) and "date-parts" in pub_dict:
            date_parts = pub_dict.get("date-parts", [[]])[0]
            if date_parts:
                year = int(date_parts[0])
                month = int(date_parts[1]) if len(date_parts) > 1 else 1
                day = int(date_parts[2]) if len(date_parts) > 2 else 1
                published = f"{year:04d}-{month:02d}-{day:02d}"

        updated = published
        created_dict = item.get("created", {})
        if isinstance(created_dict, dict) and "date-time" in created_dict:
            updated = str(created_dict["date-time"])[:10]

        abs_url = str(item.get("URL", f"https://doi.org/{paper_id}")).strip()
        pdf_url = abs_url
        comment = f"Crossref record {paper_id}"

        records.append(
            PaperRecord(
                paper_id=paper_id,
                title=title,
                summary=summary,
                authors=authors,
                categories=categories,
                primary_category=primary_category,
                published=published,
                updated=updated,
                abs_url=abs_url,
                pdf_url=pdf_url,
                comment=comment,
            )
        )
    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Fetch records from Crossref REST API or fallback to local raw snapshot files."""
    if not settings.refresh_source and settings.paths.raw_records_json.exists():
        return load_raw_records(settings.paths.raw_records_json)

    try:
        url = "https://api.crossref.org/works"
        params = {
            "query": settings.source_query,
            "filter": settings.source_filter,
            "rows": settings.max_results,
        }
        headers = {"User-Agent": "DataObservabilityLab/1.0 (mailto:lab@example.com)"}
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        payload = resp.json()
        write_json(settings.paths.raw_api_response, payload)
        records = parse_crossref_payload(payload)
        write_json(settings.paths.raw_records_json, [asdict(r) for r in records])
        return records
    except Exception:
        if settings.paths.raw_api_response.exists():
            records = parse_crossref_payload(read_json(settings.paths.raw_api_response))
            write_json(settings.paths.raw_records_json, [asdict(r) for r in records])
            return records
        if settings.paths.raw_records_json.exists():
            return load_raw_records(settings.paths.raw_records_json)
        raise RuntimeError("Failed to fetch records from Crossref API and no local raw snapshots exist.")


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Read JSON snapshot file and map contents to PaperRecord instances."""
    data = read_json(path)
    if isinstance(data, dict):
        return parse_crossref_payload(data)
    elif isinstance(data, list):
        records = []
        for item in data:
            if isinstance(item, dict):
                records.append(PaperRecord(**item))
        return records
    return []

