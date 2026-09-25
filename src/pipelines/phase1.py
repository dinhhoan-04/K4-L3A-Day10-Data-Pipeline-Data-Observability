from __future__ import annotations

from datetime import datetime, timezone

from core.config import load_settings
from core.utils import write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    """Run Phase 1 Baseline pipeline end-to-end."""
    settings = load_settings()
    print("=== Phase 1: Baseline Data Pipeline & Observability Start ===")

    records = fetch_source_records(settings)
    print(f"-> Ingested {len(records)} raw paper records.")

    current_time = datetime.now(timezone.utc)
    df_clean = build_clean_dataframe(records, current_time)
    print(f"-> Cleaned dataframe contains {len(df_clean)} records.")

    write_csv(df_clean, settings.paths.clean_csv)
    write_json(settings.paths.clean_json, df_clean.to_dict(orient="records"))
    print(f"-> Clean artifacts saved to {settings.paths.clean_csv} and {settings.paths.clean_json}.")

    quality_res = run_data_quality_checks(df_clean, settings, "baseline")
    freshness_res = build_freshness_report(df_clean, settings, settings.paths.freshness_report)
    print(f"-> Baseline Data Quality Gate Status: {quality_res['success']}")
    print(f"-> Freshness SLA Status: {freshness_res['is_fresh']}")

    index = LocalEmbeddingIndex.build(df_clean, settings, settings.paths.embeddings_json)
    print(f"-> ChromaDB index '{index.collection_name}' built with {len(index.documents)} documents.")

    test_set = build_test_set(df_clean, settings.paths.eval_testset)
    print(f"-> Evaluation test set generated with {len(test_set)} questions.")

    eval_bundle = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )
    print("-> Baseline Metrics:")
    print(f"   - Retrieval Hit Rate: {eval_bundle.summary['retrieval_hit_rate']*100:.1f}%")
    print(f"   - Mean Token F1:     {eval_bundle.summary['mean_token_f1']:.4f}")
    print(f"   - Judge Accuracy:    {eval_bundle.summary['judge_accuracy']*100:.1f}%")

    source_summary = {
        "source_api": settings.source_api,
        "total_records": len(records),
        "clean_rows": len(df_clean),
    }
    generate_phase1_report(
        report_path=settings.paths.baseline_report,
        source_summary=source_summary,
        metrics=eval_bundle.summary,
        quality=quality_res,
        freshness=freshness_res,
    )
    print(f"-> Phase 1 Report generated at {settings.paths.baseline_report}.")
    print("=== Phase 1 Baseline Pipeline Finished Successfully ===")


if __name__ == "__main__":
    main()

