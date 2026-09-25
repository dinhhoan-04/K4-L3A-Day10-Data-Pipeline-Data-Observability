# Data Observability & Resilience Report: 3-State Comparison

## 📊 Performance Matrix (Baseline vs Corrupted vs Repaired)

| Metric | Baseline Clean Data | Corrupted Data | Repaired (Self-Healed) Data |
| :--- | :---: | :---: | :---: |
| **Retrieval Hit Rate** | **100.0%** | 60.0% | **100.0%** |
| **Mean Token F1 Score** | **1.0000** | 0.6741 | **1.0000** |
| **LLM Judge Accuracy** | **100.0%** | 70.0% | **100.0%** |
| **LLM Judge Mean Score** | **5.00** | 3.60 | **5.00** |
| **GX Quality Gate** | **PASSED** | **FAILED** | **PASSED** |
| **Freshness SLA Status** | **FRESH** | **FRESH** | **FRESH** |

---

## 🔍 Key Findings & Analysis

1. **Silent Failure Demonstration:** When 6 synthetic corruptions (dropped latest records, blank summaries, title truncations, noise injection, stale dates, and duplicates) were introduced, retrieval hit rate dropped significantly.
2. **Quality Gate Alert:** Great Expectations 1.x Quality Gate correctly flagged `success = False` on the corrupted data batch due to nulls/short summaries/duplicate IDs, preventing toxic data from serving production undetected.
3. **Idempotent Self-Healing Verification:** Re-running the pipeline from raw snapshot source (`data/raw/crossref_records.json`) restored 100% of baseline performance across all metrics.
