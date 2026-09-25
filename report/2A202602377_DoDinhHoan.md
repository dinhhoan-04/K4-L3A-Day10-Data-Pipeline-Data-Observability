# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Đỗ Đình Hoàn             |
| MSSV               | 2A202602377                |
| Khóa/Lớp         | K4-L3-DAY10              |
| Tên nhóm         | Đỗ Đình Hoàn Solo     |
| Vai trò chính    | Full Stack Pipeline Engineer |
| Repository         | https://github.com/dinhhoan-04/K4-L3A-Day10-Data-Pipeline-Data-Observability.git |
| Ngày hoàn thành | 2026-09-25               |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Raw Ingestion & Preservation | `src/ingestion/crossref.py` | Crossref REST API / Snapshot JSON | `data/raw/crossref_records.json` | Hoàn thành |
| Cleaning & Data Modeling | `src/ingestion/cleaning.py` | `PaperRecord` objects | `data/clean/papers_clean.csv` | Hoàn thành |
| Data Observability & Quality Gate | `src/observability/quality.py` | Cleaned / Corrupted DataFrame | `data/quality/baseline_quality_report.json` | Hoàn thành |
| Benchmark Test Set Generator | `src/evaluation/testset.py` | Cleaned DataFrame | `data/eval/test_set.json` | Hoàn thành |
| Synthetic Data Corruption Suite | `src/ingestion/corruption.py` | Cleaned DataFrame | `data/results/corruption_log.json` | Hoàn thành |
| Idempotent Repair & Orchestration | `src/pipelines/phase1.py`, `corruption_flow.py` | Raw snapshot / Clean / Corrupted Data | `data/reports/corruption_report.md` | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

Thực hiện trọn gói toàn bộ công việc của dự án từ thiết lập môi trường, triển khai module, viết test set, đánh giá metrics RAG và viết báo cáo Markdown.

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Ingestion & Offline Fallback | `src/ingestion/crossref.py` | Tải đủ 24 bài báo khoa học từ Crossref API / Snapshot | `python -c "from ingestion.crossref import fetch_source_records..."` |
| Data Cleaning & Feature Engineering | `src/ingestion/cleaning.py` | DataFrame 24 dòng sạch có `age_days` và `text_for_embedding` | `python -c "from ingestion.cleaning import build_clean_dataframe..."` |
| GX 1.x Quality Gate & Freshness SLA | `src/observability/quality.py` | Trạm kiểm dịch Great Expectations 1.x trả về `success=True` | `python -c "from observability.quality import run_data_quality_checks..."` |
| Benchmark Evaluation & Vector Store | `src/evaluation/testset.py`, `retrieval/index.py` | Bộ test set 10 câu hỏi & ChromaDB index Hit Rate 100% | `python script/run_phase1.py` |
| Synthetic Corruption & Self-Healing Repair | `src/ingestion/corruption.py`, `pipelines/corruption_flow.py` | Tiêm 6 dạng lỗi (Hit Rate giảm 60%) & Repair khôi phục 100% | `python script/run_corruption_flow.py` |

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Trong các hệ thống RAG Agent thực tế, khi dữ liệu đầu vào bị lỗi (dữ liệu mốc meo, mất tóm tắt, nhiễu ký tự, tiêu đề bị cắt ngắn), Agent **không báo lỗi đỏ** mà vẫn tự tin trả lời sai sự thật (Silent Failure / Hallucination). Cần xây dựng Data Pipeline chuẩn hóa tích hợp "chốt kiểm dịch" Great Expectations 1.x và cơ chế tự phục hồi Idempotent Repair từ bản sao lưu thô (Raw Preservation).

### Cách triển khai

1. **Ingestion & Raw Preservation:** Bóc tách metadata từ Crossref REST API, làm sạch thẻ HTML `<jats:p>` và lưu trữ bản gốc tại `data/raw/crossref_records.json`.
2. **Cleaning & Transformation:** Loại bỏ trùng lặp theo `paper_id`, tính toán số ngày ra đời `age_days = (run_date - published).days` và xây dựng cấu trúc `text_for_embedding`.
3. **Great Expectations 1.x Quality Gate:** Khởi tạo `gx.get_context(mode="ephemeral")`, kiểm tra 4 nhóm quy tắc (Row count 5-5000, Non-null, Unique `paper_id`, Summary length >= 30) và Freshness SLA (< 25% bài báo cũ hơn 180 ngày).
4. **Vector Database:** Nhúng vector bằng `sentence-transformers/all-MiniLM-L6-v2` nạp vào ChromaDB collection `papers-baseline`.
5. **Synthetic Data Corruption:** Chủ động tiêm 6 kịch bản lỗi (Drop latest 20%, Blank summary, Inject noise, Truncate title, Stale date, Duplicate rows).
6. **Idempotent Repair:** Tự động đọc lại từ `data/raw/crossref_records.json`, chạy lại pipeline làm sạch và ghi đè Vector DB để khôi phục 100% phong độ ban đầu.

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | Crossref JSON Payload / Snapshot `data/raw/crossref_response.json` |
| Output                         | Cleaned CSV/JSON, ChromaDB index, Quality Reports, Baseline & Corruption Metrics |
| Module phụ thuộc             | `core/config.py`, `core/utils.py`, `retrieval/index.py`, `retrieval/qa.py` |
| Module sử dụng output        | `script/run_phase1.py`, `script/run_corruption_flow.py` |
| Điều kiện lỗi cần xử lý | Mất kết nối mạng, API dính 429 Too Many Requests, dữ liệu bẩn có null/duplicate |

### Cách xác minh

```powershell
$env:PYTHONIOENCODING="utf-8"; .\.venv\Scripts\python.exe script/run_phase1.py
$env:PYTHONIOENCODING="utf-8"; .\.venv\Scripts\python.exe script/run_corruption_flow.py
```

- **Kết quả mong đợi:** 
  - Phase 1: Ingest 24 bài báo, Quality Gate Pass = True, Baseline Hit Rate = 100.0%, Token F1 = 1.0000.
  - Phase 2: Corrupted Quality Gate Pass = False, Hit Rate sụt giảm còn 60.0%, Repaired Hit Rate khôi phục 100.0%.
- **Kết quả thực tế:** 100% khớp với mong đợi.
- **Artifact/log:** `data/reports/phase1_report.md`, `data/reports/corruption_report.md`.

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Cần chọn phương pháp thiết lập Great Expectations 1.x phù hợp với ứng dụng RAG trong bài lab.
- **Các phương án đã cân nhắc:**
  1. *Phương án A:* Khởi tạo GX CLI file-system context (`gx init`) đẻ ra các thư mục cấu hình `great_expectations/` cồng kềnh.
  2. *Phương án B:* Khởi tạo Ephemeral Context (`gx.get_context(mode="ephemeral")`) chạy hoàn toàn trên RAM.
- **Phương án đã chọn:** Phương án B (Ephemeral Context).
- **Lý do:** Tốc độ thực thi cực nhanh, nhẹ nhàng, không đẻ file cấu hình rác gây nhiễu môi trường Git, hoàn toàn tương thích với chuẩn mã nguồn GX 1.x hiện đại.
- **Bằng chứng quyết định phù hợp:** Quality check chạy trong 0.05 giây và ghi nhận đúng trạng thái `success=True` trên dữ liệu sạch và `success=False` trên dữ liệu bẩn.

---

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `UnicodeEncodeError: 'charmap' codec can't encode characters in position 6-7: character maps to <undefined>` khi chạy script trên Windows PowerShell.
- **Lệnh hoặc bước tái hiện:** Chạy `.venv\Scripts\python.exe -c "print('Môi trường sẵn sàng')"` trực tiếp trên Windows PowerShell.
- **Nguyên nhân gốc:** Codepage mặc định của Windows PowerShell Console là `cp1252`, không mã hóa được các ký tự tiếng Việt UTF-8 khi xuất qua stdout.
- **Cách xử lý:** Đặt biến môi trường `$env:PYTHONIOENCODING="utf-8"` trước khi gọi lệnh python.
- **Cách xác minh sau khi sửa:** Chạy `$env:PYTHONIOENCODING="utf-8"; .\.venv\Scripts\python.exe script/run_phase1.py` in ra tiếng Việt mượt mà không còn lỗi charmap.
- **Điều học được:** Luôn quản lý mã hóa I/O UTF-8 chuẩn hóa trên các môi trường cross-platform (Windows / Linux / macOS).

---

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?**  
   Dữ liệu được kéo từ Crossref API -> Lưu bản thô `data/raw/` -> Chuẩn hóa tiêu đề/tóm tắt, tính `age_days` -> Ghép `text_for_embedding` -> Đưa qua Quality Gate kiểm định -> Tạo vector nhúng qua `sentence-transformers/all-MiniLM-L6-v2` -> Nạp vào ChromaDB vector collection.

2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**  
   Bộ test set chứa 10 câu hỏi chuẩn hóa kèm đáp án gốc (`ground_truth`) và mã bài báo gốc (`ground_truth_doc_ids`). Khi Agent truy vấn, hệ thống đo xem tài liệu trả về từ ChromaDB có chứa ID chuẩn không (`retrieval_hit_rate`) và đo mức trùng khớp câu chữ (`mean_token_f1`).

3. **Quality checks khác freshness monitoring ở điểm nào trong bài lab?**  
   Quality checks (Great Expectations) kiểm tra tính hợp lệ về mặt cấu trúc (Null, Duplicate, Summary Length, Row Count). Freshness monitoring kiểm tra mốc thời gian xuất bản (`age_days > 180`) để đảm bảo AI không dùng kiến thức đã mốc meo/lỗi thời.

4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**  
   Để đảm bảo nguyên tắc thí nghiệm kiểm soát (Controlled Experiment), giúp so sánh chính xác 100% sự ảnh hưởng của chất lượng dữ liệu lên hiệu năng AI RAG.

5. **Repair được xem là thành công dựa trên artifact và metric nào?**  
   Repair thành công khi Quality Gate báo `PASSED (True)` và các chỉ số RAG (`retrieval_hit_rate = 100%`, `mean_token_f1 = 1.0000`, `judge_accuracy = 100%`) khôi phục tương đương với trạng thái Baseline ban đầu.

---

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` | **100.0%** | **60.0%** | **100.0%** | Dữ liệu bị lỗi làm sụt giảm 40% khả năng tìm kiếm |
| `mean_token_f1`      | **1.0000** | **0.6741** | **1.0000** | Độ trích xuất thông tin bị suy giảm nghiêm trọng |
| `judge_accuracy`     | **100.0%** | **70.0%** | **100.0%** | AI Judge phát hiện câu trả lời bị sai sự thật |
| `mean_judge_score`   | **5.00** | **3.60** | **5.00** | Điểm đánh giá chất lượng RAG giảm rõ rệt |
| Quality checks         | **PASSED** | **FAILED** | **PASSED** | Quality Gate chặn đứng dữ liệu xấu thành công |
| Freshness status       | **FRESH** | **FRESH** | **FRESH** | Đảm bảo mốc thời gian SLA |

### Kết luận từ số liệu

1. **[Data corruption (bỏ rơi 20% bản ghi & xóa summary)] → [GX Quality Gate báo FAILED & hit_rate giảm còn 60%] → [RAG Agent trả lời sai sự thật (Silent Failure)]**.  
2. **[Idempotent Repair từ Raw snapshot] → [GX Quality Gate khôi phục PASSED] → [RAG Agent lấy lại 100% Hit Rate & Token F1]**.

---

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Garbage In -> Garbage Out:** Chất lượng dữ liệu quyết định 80% thành bại của RAG Agent.
2. **Tầm quan trọng của Data Observability:** Great Expectations 1.x là "chốt kiểm dịch" bắt buộc phải có để ngăn ngừa Silent Failure trong sản xuất.
3. **Nguyên tắc Raw Preservation & Idempotence:** Bảo toàn dữ liệu gốc thô giúp hệ thống có khả năng tự phục hồi (Self-healing) an toàn và tin cậy.

### Nếu có thêm thời gian

Tôi sẽ tích hợp thêm công cụ Airflow/Prefect để tự động hóa lịch chạy pipeline định kỳ và xây dựng Dashboard quan sát theo thời gian thực (Grafana / Streamlit).

---

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Đỗ Đình Hoàn  
**Ngày xác nhận:** 2026-09-25  
