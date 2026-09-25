from __future__ import annotations

from datetime import datetime, timezone
import pandas as pd

from core.config import load_settings
from core.utils import read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    """Run Phase 2 Corruption -> Evaluate -> Repair -> Compare flow."""
    settings = load_settings()
    print("=== Phase 2: Data Corruption, Quality Alerts & Self-Healing Repair Start ===")

    if not settings.paths.clean_json.exists() or not settings.paths.baseline_metrics.exists():
        print("Baseline dataset/metrics not found. Running Phase 1 pipeline first...")
        from pipelines.phase1 import main as run_phase1
        run_phase1()

    baseline_metrics = read_json(settings.paths.baseline_metrics)
    df_clean = pd.read_json(settings.paths.clean_json)

    print("-> Injecting 6 controlled corruptions into clean data...")
    df_corrupted = corrupt_clean_dataframe(df_clean, settings.paths.corruption_log)
    print(f"-> Corrupted dataframe created with {len(df_corrupted)} rows.")

    write_csv(df_corrupted, settings.paths.corrupted_clean_csv)
    write_json(settings.paths.corrupted_clean_json, df_corrupted.to_dict(orient="records"))

    corrupted_quality = run_data_quality_checks(df_corrupted, settings, "corrupted")
    corrupted_freshness = build_freshness_report(
        df_corrupted, settings, settings.paths.quality_dir / "corrupted_freshness_report.json"
    )
    print(f"-> Corrupted Data Quality Gate Status: {corrupted_quality['success']} (Detected Failure!)")
    print(f"-> Corrupted Freshness SLA Status: {corrupted_freshness['is_fresh']}")

    index_corrupted = LocalEmbeddingIndex.build(df_corrupted, settings, settings.paths.corrupted_embeddings_json)
    corrupted_eval = evaluate_pipeline(
        settings=settings,
        index=index_corrupted,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers,
    )
    print("-> Corrupted Metrics (Degraded RAG Performance):")
    print(f"   - Retrieval Hit Rate: {corrupted_eval.summary['retrieval_hit_rate']*100:.1f}%")
    print(f"   - Mean Token F1:     {corrupted_eval.summary['mean_token_f1']:.4f}")
    print(f"   - Judge Accuracy:    {corrupted_eval.summary['judge_accuracy']*100:.1f}%")

    print("-> Kicking off Idempotent Self-Healing Repair from Raw snapshot...")
    raw_records = load_raw_records(settings.paths.raw_records_json)
    current_time = datetime.now(timezone.utc)
    df_repaired = build_clean_dataframe(raw_records, current_time)

    write_csv(df_repaired, settings.paths.repaired_clean_csv)
    write_json(settings.paths.repaired_clean_json, df_repaired.to_dict(orient="records"))

    repaired_quality = run_data_quality_checks(df_repaired, settings, "repaired")
    repaired_freshness = build_freshness_report(
        df_repaired, settings, settings.paths.quality_dir / "repaired_freshness_report.json"
    )

    index_repaired = LocalEmbeddingIndex.build(df_repaired, settings, settings.paths.repaired_embeddings_json)
    repaired_eval = evaluate_pipeline(
        settings=settings,
        index=index_repaired,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers,
    )
    print("-> Repaired Metrics (Restored RAG Performance):")
    print(f"   - Retrieval Hit Rate: {repaired_eval.summary['retrieval_hit_rate']*100:.1f}%")
    print(f"   - Mean Token F1:     {repaired_eval.summary['mean_token_f1']:.4f}")
    print(f"   - Judge Accuracy:    {repaired_eval.summary['judge_accuracy']*100:.1f}%")

    generate_corruption_report(
        report_path=settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_eval.summary,
        repaired_metrics=repaired_eval.summary,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
    )
    print(f"-> 3-State Comparison Report generated at {settings.paths.comparison_report}.")
    print("=== Phase 2 Corruption & Self-Healing Pipeline Finished Successfully ===")


if __name__ == "__main__":
    main()

