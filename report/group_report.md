# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Khóa/Lớp         | K4-L3-DAY10              |
| Tên nhóm         | Đỗ Đình Hoàn Solo     |
| Repository         | https://github.com/dinhhoan-04/K4-L3A-Day10-Data-Pipeline-Data-Observability.git |
| Ngày hoàn thành | 2026-09-25               |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | Đỗ Đình Hoàn | 2A202602377 | Full Stack Pipeline Engineer | Toàn bộ dự án (`src/`, `script/`, `data/`, `report/`) |

---

## 2. Tóm tắt kết quả

Nhóm (cá nhân Đỗ Đình Hoàn) đã hoàn thành 100% các yêu cầu kỹ thuật và 7 Checkpoint (CP0 – CP6) của bài lab:

- **Baseline Pipeline (Phase 1):** Xây dựng thành công Data Pipeline tự động thu thập 24 bản ghi bài báo khoa học từ Crossref API (hỗ trợ cơ chế Fallback Offline), làm sạch dữ liệu, tính tuổi đời `age_days`, dựng Quality Gate theo chuẩn mới Great Expectations 1.x và Freshness SLA. Hệ thống nhúng vector `all-MiniLM-L6-v2` vào ChromaDB collection `papers-baseline`. Đánh giá baseline đạt kết quả tối ưu: **Retrieval Hit Rate = 100.0%**, **Mean Token F1 = 1.0000**, **LLM Judge Accuracy = 100.0%**, **Judge Mean Score = 5.00/5.00**.

- **Synthetic Corruption & Observability (Phase 2):** Giả lập thành công 6 dạng lỗi dữ liệu thực tế (bỏ rơi 20% bài báo mới nhất, xóa tóm tắt, chèn ký tự rác, cắt ngắn tiêu đề, lùi ngày xuất bản, nhân bản dòng). Chốt kiểm dịch Quality Gate ngay lập tức chuyển trạng thái `FAILED (success=False)` để cảnh báo. Đồng thời chứng minh hiện tượng **Silent Failure**: khi dữ liệu bẩn lọt vào Vector Store, Retrieval Hit Rate sụt giảm nghiêm trọng xuống **60.0%**, Token F1 giảm còn **0.6741**, LLM Judge Accuracy giảm còn **70.0%**.

- **Idempotent Repair:** Tự động kích hoạt cơ chế tự phục hồi (Self-healing) đọc lại từ nguồn lưu trữ thô ban đầu `data/raw/crossref_records.json`. Sau khi repair, 100% chỉ số chất lượng RAG khôi phục về trạng thái hoàn hảo ban đầu (Hit Rate = 100%, F1 = 1.0000).

---

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

```text
Nguồn Crossref API (hoặc Snapshot Offline data/raw/crossref_response.json)
    ├── 1. Ingestion & Raw Preservation -> data/raw/crossref_records.json
    ├── 2. Transformation & Cleaning   -> data/clean/papers_clean.csv
    ├── 3. Data Quality Gate (GX 1.x)   -> data/quality/baseline_quality_report.json & Freshness SLA
    ├── 4. Vector Embedding & Indexing  -> sentence-transformers + ChromaDB (collection: papers-baseline)
    ├── 5. Baseline Evaluation Benchmark -> Hit Rate: 100%, Token F1: 1.0000, Judge Accuracy: 100%
    ├── 6. Synthetic Data Corruption    -> Tiêm 6 dạng lỗi (data/results/corruption_log.json)
    ├── 7. Data Quality Alert           -> Quality Gate báo FAILED (False), Hit Rate sụt giảm còn 60%
    └── 8. Idempotent Repair            -> Tái tạo sạch từ Raw Preservation & Báo cáo đối chiếu 3 trạng thái
```

### Trách nhiệm của từng khối

| Khối             | Input          | Xử lý chính             | Output/artifact          | Owner          |
| ----------------- | -------------- | -------------------------- | ------------------------ | -------------- |
| Ingestion         | Crossref REST API / Snapshot JSON | Fetch API với retry, parse JSON payload, lưu raw snapshot | `data/raw/crossref_response.json`, `data/raw/crossref_records.json` | Đỗ Đình Hoàn |
| Cleaning          | `PaperRecord` raw objects | Normalize whitespace, tính `age_days`, ghép `text_for_embedding`, khử trùng lặp | `data/clean/papers_clean.csv`, `data/clean/papers_clean.json` | Đỗ Đình Hoàn |
| Embedding/index   | Cleaned DataFrame | Embed văn bản bằng `all-MiniLM-L6-v2`, đánh chỉ mục ChromaDB HNSW | `data/chroma/`, `data/embeddings/papers_embeddings.json` | Đỗ Đình Hoàn |
| Evaluation        | Cleaned DataFrame | Sinh 10 câu hỏi test set đa dạng, đo Hit Rate, Token F1, LLM Judge | `data/eval/test_set.json`, `data/results/baseline_metrics.json` | Đỗ Đình Hoàn |
| Observability     | Cleaned / Corrupted DataFrame | Chạy Great Expectations 1.x ephemeral suite & Freshness SLA check | `data/quality/baseline_quality_report.json`, `freshness_report.json` | Đỗ Đình Hoàn |
| Corruption/repair | Cleaned DataFrame / Raw snapshot | Tiêm 6 dạng lỗi synthetic; Re-ingest từ raw snapshot để repair | `data/results/corruption_log.json`, `corrupted_clean.csv`, `repaired_clean.csv` | Đỗ Đình Hoàn |
| Orchestration     | Toàn bộ các module | Điều phối luồng Phase 1 & Phase 2, xuất báo cáo đối chiếu Markdown | `script/run_phase1.py`, `script/run_corruption_flow.py`, `data/reports/` | Đỗ Đình Hoàn |

---

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình             | Giá trị sử dụng |
| ---------------------------- | ------------------- |
| `LLM_PROVIDER`             | `gemini` |
| `LLM_MODEL`                | `gemini-2.5-flash` |
| Embedding model              | `sentence-transformers/all-MiniLM-L6-v2` |
| Số lượng Crossref records | 24 records |
| Retrieval `top_k`           | 4 |
| Freshness threshold          | 180 days (Warning SLA nếu stale ratio > 25%) |

### Lệnh cài đặt

Kích hoạt virtual environment và cài đặt package dạng editable:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

### Lệnh chạy

Chạy Baseline Pipeline (Phase 1):

```powershell
$env:PYTHONIOENCODING="utf-8"; .\.venv\Scripts\python.exe script/run_phase1.py
```

Chạy Corruption, Quality Alert & Idempotent Repair Flow (Phase 2):

```powershell
$env:PYTHONIOENCODING="utf-8"; .\.venv\Scripts\python.exe script/run_corruption_flow.py
```

### Kết quả tái hiện

| Lệnh             | Trạng thái | Thời điểm chạy gần nhất | Bằng chứng |
| ----------------- | ------------------- | ----------------------------- | ------------------------------------ |
| Baseline pipeline | Thành công (100% Pass) | 2026-09-25 16:45:04 UTC | `data/reports/phase1_report.md`, `data/results/baseline_metrics.json` |
| Corruption flow   | Thành công (100% Pass) | 2026-09-25 16:46:03 UTC | `data/reports/corruption_report.md`, `data/results/corruption_log.json` |

---

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính                | Giá trị                             |
| --------------------------- | ------------------------------------- |
| Source                      | Crossref REST API (`https://api.crossref.org/works`) |
| Query/filter                | `query=agentic retrieval augmented generation large language model`, `filter=from-pub-date:2026-03-29,has-abstract:true` |
| Thời điểm lấy dữ liệu | 2026-09-25 |
| Số record nhận được    | 24 bài báo khoa học |
| Cơ chế retry/backoff      | Timeout 10s, tự động fallback sang `data/raw/crossref_response.json` khi API lỗi hoặc dính 429 |

### Raw và clean schema

| Trường        | Kiểu dữ liệu | Bắt buộc?  | Ý nghĩa   | Xử lý khi thiếu/sai |
| --------------- | --------------- | ------------ | ----------- | ---------------------- |
| `paper_id` | `str` | Có | Định danh DOI của bài báo | Bỏ qua record nếu thiếu paper_id |
| `title` | `str` | Có | Tiêu đề bài báo học thuật | Loại bỏ HTML tags, normalize whitespace |
| `summary` | `str` | Có | Tóm tắt nội dung nghiên cứu | Loại bỏ thẻ `<jats:p>`, mặc định chuỗi rỗng nếu thiếu |
| `authors` | `list[str]` | Có | Danh sách tác giả | Ghép họ tên (`given family`), nối bằng dấu phẩy |
| `categories` | `list[str]` | Có | Chuyên ngành / Lĩnh vực | Lấy từ `subject`, mặc định `General` nếu thiếu |
| `published` | `str` | Có | Ngày xuất bản (`YYYY-MM-DD`) | Parse date-parts, mặc định `2026-01-01` |
| `age_days` | `int` | Có | Tuổi đời tính theo số ngày | `(run_date - published_date).days` |
| `text_for_embedding` | `str` | Có | Đoạn văn bản hoàn chỉnh để nhúng vector | Tự động ghép từ Title, Authors, Published, Categories, Summary |

### Quy tắc cleaning

| Quy tắc | Quality dimension | Số record bị tác động | Cách xác minh |
| ---------------------------------------- | ---------------------------- | -------------------------: | -------------------- |
| Loại bỏ thẻ HTML/XML rác (`<jats:p>`) | Validity & Cleanliness | 24 | Chuỗi `summary` trong `papers_clean.csv` sạch hoàn toàn |
| Khử trùng lặp bản ghi trùng khóa `paper_id` | Uniqueness | 0 (sạch) / 2 (khi corrupt) | `ExpectColumnValuesToBeUnique` trong GX Quality Gate |
| Loại bỏ khoảng trắng thừa (Normalize whitespace) | Consistency | 24 | Regex `\s+` chuyển thành khoảng đơn |
| Kiểm tra độ dài summary >= 30 ký tự | Completeness | 0 (sạch) / 2 (khi corrupt) | `ExpectColumnValueLengthsToBeBetween` |

---

## 6. Evaluation setup

| Thành phần                             | Cấu hình thực tế          |
| ---------------------------------------- | ----------------------------- |
| Số câu hỏi                            | 10 câu hỏi benchmark |
| Các `question_type`                    | `summary`, `authors`, `date`, `categories` |
| Ground-truth document ID                 | DOI bài báo gốc tương ứng (`ground_truth_doc_ids`) |
| Embedding model                          | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector store/collection                  | ChromaDB PersistentClient (collections: `papers-baseline`, `papers-corrupted`, `papers-repaired`) |
| Retrieval `top_k`                       | 4 |
| LLM provider/model                       | Gemini (`gemini-2.5-flash`) / Fallback Heuristic Judge |
| Test set dùng chung cho ba trạng thái | `data/eval/test_set.json` |

**Tại sao test set được giữ nguyên qua 3 trạng thái?**  
Giữ nguyên duy nhất một bộ đề thi `test_set.json` là điều kiện bắt buộc để đảm bảo tính khách quan (Controlled Experiment). Việc này giúp cách ly biến số đánh giá: sự thay đổi chỉ số RAG hoàn toàn phản ánh tác động của chất lượng dữ liệu đầu vào (Clean vs Corrupted vs Repaired), không bị nhiễu do thay đổi câu hỏi.

---

## 7. Kết quả baseline

### Artifact checklist

| Artifact                 | Đường dẫn thực tế                | Trạng thái | Ghi chú   |
| ------------------------ | -------------------------------------- | ------------ | ---------- |
| Raw response/records     | `data/raw/crossref_response.json`, `crossref_records.json` | Có | Đã bảo toàn bản gốc nguyên vẹn |
| Cleaned dataset          | `data/clean/papers_clean.csv`, `papers_clean.json` | Có | 24 bản ghi sạch đã tiền xử lý |
| Embedding manifest/index | `data/embeddings/papers_embeddings.json` | Có | Lưu manifest cấu hình ChromaDB index |
| Evaluation set           | `data/eval/test_set.json` | Có | 10 câu hỏi test set chuẩn |
| Baseline metrics         | `data/results/baseline_metrics.json` | Có | Hit Rate = 1.0, Token F1 = 1.0000 |
| Quality/freshness        | `data/quality/baseline_quality_report.json`, `freshness_report.json` | Có | Quality Gate Pass = True, Fresh = True |
| Baseline report          | `data/reports/phase1_report.md` | Có | Báo cáo Markdown Pha 1 hoàn chỉnh |

### Baseline metrics

| Metric                 | Giá trị | Diễn giải |
| ---------------------- | --------------: | --------------------------------------- |
| `retrieval_hit_rate` | 100.0% (1.0) | Top-4 document truy vấn chứa 100% tài liệu đáp án chuẩn |
| `mean_token_f1`      | 1.0000 | Trích xuất chính xác 100% token đáp án trích đoạn |
| `judge_accuracy`     | 100.0% (1.0) | LLM Judge đánh giá 100% câu trả lời đạt yêu cầu |
| `mean_judge_score`   | 5.00 / 5.00 | Điểm trung bình tuyệt đối từ mô hình đánh giá |
| Ragas                | Skipped (N/A) | Mặc định bỏ qua Ragas để tối ưu tốc độ chạy lab |

---

## 8. Data quality và freshness

### Quality checks

| Check        | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline | Bằng chứng |
| ------------ | ----------------- | ------------------ | ----------------------- | ------------ |
| `ExpectTableRowCountToBeBetween` | Completeness | [5, 5000] | **PASS** (24 dòng) | `baseline_quality_report.json` |
| `ExpectColumnValuesToNotBeNull` | Completeness | `paper_id`, `title`, `text_for_embedding` không null | **PASS** (0 null) | `baseline_quality_report.json` |
| `ExpectColumnValuesToBeUnique` | Uniqueness | `paper_id` độc nhất | **PASS** (0 duplicate) | `baseline_quality_report.json` |
| `ExpectColumnValueLengthsToBeBetween` | Validity | `summary` length >= 30 | **PASS** (0 short) | `baseline_quality_report.json` |

### Freshness

| Thuộc tính               | Giá trị                           |
| -------------------------- | ----------------------------------- |
| Freshness được đo tại | `data/clean/papers_clean.json` |
| Timestamp mới nhất       | 2026-07-22 |
| Ngưỡng freshness         | 180 ngày (`freshness_threshold_days`) |
| Trạng thái baseline      | **FRESH (is_fresh = True)** |
| Lý do                     | Tỉ lệ bài báo quá 180 ngày là 0.0% (nhỏ hơn ngưỡng warning SLA 25%) |

---

## 9. Corruption scenarios và repair

| Corruption | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair |
| ------------------ | ---------- | ---------------------: | ------------------------ | --------------------- | -------------- |
| **Drop latest records** | Bỏ rơi 20% bài báo mới nhất | 5 bản ghi | Thiếu tài liệu mới nhất | Loss retrieval hit rate trên câu hỏi liên quan | Re-ingest lại từ `crossref_records.json` |
| **Blank summary** | Xóa rỗng trường summary | 2 bản ghi | Fail check `summary length >= 30` | Mất ngữ cảnh summary làm loãng vector search | Đọc lại summary nguyên bản từ raw snapshot |
| **Inject noise** | Chèn chuỗi rác `NOISE_GARBAGE_###` | 2 bản ghi | Biến đổi vector space | Sai lệch khoảng cách cosine trong ChromaDB | Khôi phục văn bản sạch từ raw snapshot |
| **Truncate title** | Cắt bớt tiêu đề còn 5 ký tự | 2 bản ghi | Không nhận diện được tiêu đề | Mất khả năng lookup exact match theo title | Tái tạo lại tiêu đề nguyên vẹn từ raw data |
| **Stale date** | Lùi ngày xuất bản về 365 ngày trước | 3 bản ghi | Tăng `age_days` | Gây sai lệch thời gian xuất bản khi QA hỏi ngày | Khôi phục mốc ngày gốc từ `published` field |
| **Duplicate rows** | Nhân bản 2 dòng đầu | 2 bản ghi | Fail check `ExpectColumnValuesToBeUnique` | Làm trùng lặp vector index, nhiễu top-k recall | Khử trùng lặp qua `drop_duplicates` trong cleaning |

---

## 10. So sánh baseline, corrupted và repaired

| Metric/signal            | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét |
| ------------------------ | -------: | --------: | -------: | -----------------------: | --------------: | ------------ |
| `retrieval_hit_rate`   | **100.0%** | **60.0%** | **100.0%** | -40.0% | +40.0% (100%) | Dữ liệu bẩn làm sụt giảm khả năng tìm kiếm chính xác |
| `mean_token_f1`        | **1.0000** | **0.6741** | **1.0000** | -0.3259 | +0.3259 (100%) | Độ trùng khớp câu trả lời bị suy giảm nghiêm trọng |
| `judge_accuracy`       | **100.0%** | **70.0%** | **100.0%** | -30.0% | +30.0% (100%) | AI Judge phát hiện câu trả lời sai sự thật (Hallucination) |
| `mean_judge_score`     | **5.00** | **3.60** | **5.00** | -1.40 | +1.40 (100%) | Điểm chất lượng giảm sút rõ rệt |
| Quality checks pass/fail | **PASSED** | **FAILED** | **PASSED** | Báo động đỏ (False) | Khôi phục PASSED | Quality Gate đánh chặn dữ liệu xấu thành công |
| Freshness status         | **FRESH** | **FRESH** | **FRESH** | Không đổi | Giữ vững FRESH | SLA theo dõi đúng tuổi đời bài báo |

### Hai kết luận nguyên nhân – kết quả:

1. **[Tiêm độc tố dữ liệu] → [GX Quality Gate báo FAILED & hit_rate giảm 40%] → [Agent trả lời sai sự thật (Silent Failure)]**: Khi dữ liệu bị cắt ngắn tiêu đề và xóa tóm tắt, Agent vẫn tự tin đưa ra câu trả lời nhưng câu trả lời không còn đúng với thực tế. Quality Gate là chốt chặn quan trọng duy nhất phát hiện ra lỗi trước khi dữ liệu được nhúng vào Vector DB.
2. **[Tự động kích hoạt Idempotent Repair từ Raw Preservation] → [Xóa sạch Vector Store lỗi & Re-ingest từ raw JSON] → [100% chỉ số RAG phục hồi phong độ ban đầu]**: Chứng minh tầm quan trọng của việc duy trì bản sao lưu gốc (Raw Layer), giúp hệ thống hồi phục an toàn mà không cần sửa thủ công.

---

## 11. Vấn đề tích hợp quan trọng

- **Triệu chứng:** Khi chạy script kiểm tra trên Windows PowerShell, lệnh in console bị lỗi `UnicodeEncodeError: 'charmap' codec can't encode characters` do các ký tự tiếng Việt có dấu.
- **Nguyên nhân:** Console codepage mặc định của Windows PowerShell (cp1252/cp936) không tự động hỗ trợ UTF-8 khi làm việc với Python `print()`.
- **Cách xử lý:** Đặt biến môi trường `$env:PYTHONIOENCODING="utf-8"` trước khi thực thi script Python.
- **Cách xác minh:** Chạy `$env:PYTHONIOENCODING="utf-8"; .\.venv\Scripts\python.exe script/run_phase1.py`, console in ra trơn tru `Môi trường sẵn sàng` và `Quality check status = True`.

---

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng | Hướng cải thiện có thể kiểm chứng |
| --------------------- | -------------- | ----------------------------------------- |
| Quy mô dữ liệu thử nghiệm nhỏ (24 bài báo) | Chưa kiểm thử được hiệu năng scale lên hàng triệu vector | Mở rộng nạp 10,000+ bản ghi từ Crossref API để đo latency của HNSW index |
| Đánh giá dựa trên trích đoạn exact matching | Chưa đo hết được khả năng suy luận đa bước (Multi-hop reasoning) | Tích hợp thêm bộ testset phức tạp yêu cầu tổng hợp thông tin từ 3-5 bài báo cùng lúc |

---

## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và repository chính xác.
- [x] Phân công khớp với module, artifact và kết quả thực tế.
- [x] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp.
- [x] Baseline, corrupted và repaired dùng cùng evaluation set.
- [x] Bảng metrics khớp với các file trong `data/results/`.
- [x] Quality/freshness conclusions khớp với `data/quality/`.
- [x] Các đường dẫn báo cáo và artifact truy cập được.
- [x] Đã hoàn thành báo cáo vai trò cá nhân.
- [x] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.
