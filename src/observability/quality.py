from __future__ import annotations

from typing import Any
import pandas as pd
import great_expectations as gx

from core.config import Settings
from core.utils import write_json


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Execute Great Expectations 1.x suite and data quality checks on the DataFrame."""
    success = True
    expectations_results = []

    # 1. Table row count between 5 and 5000
    row_count = len(df)
    row_count_ok = 5 <= row_count <= 5000
    if not row_count_ok:
        success = False
    expectations_results.append({
        "expectation": "ExpectTableRowCountToBeBetween",
        "kwargs": {"min_value": 5, "max_value": 5000},
        "success": row_count_ok,
        "observed_value": row_count,
    })

    # 2. Non-null checks for critical columns
    for col in ["paper_id", "title", "text_for_embedding"]:
        has_col = col in df.columns
        null_count = int(df[col].isnull().sum()) if has_col else row_count
        not_null_ok = has_col and (null_count == 0)
        if not not_null_ok:
            success = False
        expectations_results.append({
            "expectation": "ExpectColumnValuesToNotBeNull",
            "kwargs": {"column": col},
            "success": not_null_ok,
            "null_count": null_count,
        })

    # 3. Unique paper_id check
    has_paper_id = "paper_id" in df.columns
    unique_count = df["paper_id"].nunique() if has_paper_id else 0
    unique_ok = has_paper_id and (unique_count == row_count)
    if not unique_ok:
        success = False
    expectations_results.append({
        "expectation": "ExpectColumnValuesToBeUnique",
        "kwargs": {"column": "paper_id"},
        "success": unique_ok,
        "duplicate_count": row_count - unique_count if has_paper_id else row_count,
    })

    # 4. Summary length check >= 30
    has_summary = "summary" in df.columns
    if has_summary:
        short_summaries = int((df["summary"].astype(str).str.len() < 30).sum())
        len_ok = short_summaries == 0
    else:
        len_ok = False
        short_summaries = row_count
    if not len_ok:
        success = False
    expectations_results.append({
        "expectation": "ExpectColumnValueLengthsToBeBetween",
        "kwargs": {"column": "summary", "min_value": 30},
        "success": len_ok,
        "unexpected_count": short_summaries,
    })

    gx_report = None
    try:
        context = gx.get_context(mode="ephemeral")
        data_source = context.data_sources.add_pandas(name=f"papers_source_{report_name}")
        data_asset = data_source.add_dataframe_asset(name=f"papers_asset_{report_name}")
        batch_def = data_asset.add_batch_definition_whole_dataframe(f"papers_batch_{report_name}")

        suite = context.suites.add(gx.ExpectationSuite(name=f"papers_suite_{report_name}"))
        suite.add_expectation(gx.expectations.ExpectTableRowCountToBeBetween(min_value=5, max_value=5000))
        suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="paper_id"))
        suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="title"))
        suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="text_for_embedding"))
        suite.add_expectation(gx.expectations.ExpectColumnValuesToBeUnique(column="paper_id"))
        suite.add_expectation(gx.expectations.ExpectColumnValueLengthsToBeBetween(column="summary", min_value=30))

        validation_def = context.validation_definitions.add(
            gx.ValidationDefinition(name=f"val_def_{report_name}", data=batch_def, suite=suite)
        )
        val_result = validation_def.run(batch_parameters={"dataframe": df})
        success = val_result.success
        gx_report = val_result.to_json_dict() if hasattr(val_result, "to_json_dict") else str(val_result)
    except Exception:
        pass

    report = {
        "report_name": report_name,
        "success": success,
        "expectations": expectations_results,
        "gx_report": gx_report,
    }

    if "baseline" in report_name:
        out_file = settings.paths.baseline_quality_report
    elif "corrupted" in report_name:
        out_file = settings.paths.corrupted_quality_report
    else:
        out_file = settings.paths.quality_dir / f"{report_name}_quality_report.json"

    write_json(out_file, report)
    return report


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path=None) -> dict[str, Any]:
    """Calculate freshness metrics and check SLA thresholds."""
    output_path = report_path or settings.paths.freshness_report
    if df.empty:
        report = {
            "latest_published": None,
            "oldest_published": None,
            "stale_rows": 0,
            "total_rows": 0,
            "stale_ratio": 0.0,
            "threshold_days": settings.freshness_threshold_days,
            "is_fresh": False,
        }
    else:
        published_dates = df["published"].tolist()
        latest_published = max(published_dates)
        oldest_published = min(published_dates)

        threshold_days = settings.freshness_threshold_days
        stale_mask = df["age_days"] > threshold_days if "age_days" in df.columns else [False] * len(df)
        stale_rows = int(stale_mask.sum()) if "age_days" in df.columns else 0
        total_rows = len(df)
        stale_ratio = stale_rows / total_rows if total_rows > 0 else 0.0
        is_fresh = stale_ratio <= 0.25

        report = {
            "latest_published": latest_published,
            "oldest_published": oldest_published,
            "stale_rows": stale_rows,
            "total_rows": total_rows,
            "stale_ratio": stale_ratio,
            "threshold_days": threshold_days,
            "is_fresh": is_fresh,
        }

    write_json(output_path, report)
    return report

