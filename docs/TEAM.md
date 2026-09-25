# Danh Sách Thành Viên & Báo Cáo Phân Công Nhóm

- **Tên Nhóm:** Đỗ Đình Hoàn Solo
- **Mã Nhóm / Lớp:** K4-L3-DAY10
- **Tên Repository Nộp Bài:** K4-L3-DAY10-DoDinhHoan-DataPipeline

---

## # Thành viên

| STT | Họ và tên | MSSV | Email | Vai trò & Phân công công việc | Báo cáo cá nhân |
|---:|---|---|---|---|---|
| 1 | Đỗ Đình Hoàn | 2A202602377 | hoan.dd.2a202602377@vlearn.edu.vn | Full Stack Pipeline Engineer (Ingestion, Cleaning, GX 1.x Observability, Vector Store, Corruption & Repair) | `report/2A202602377_DoDinhHoan.md` |

---

## # Cá nhân

### ## DoDinhHoan-2A202602377
- **Vai trò:** Full Stack Pipeline Engineer (Trưởng nhóm & Thực hiện toàn bộ công việc).
- **Công việc chi tiết đã hoàn thành:**
  - Thiết lập cấu hình hệ thống `src/core/config.py` và đường dẫn artifacts `src/core/utils.py`.
  - Xây dựng module thu thập Crossref API với cơ chế Fallback offline trong `src/ingestion/crossref.py`.
  - Chuẩn hóa schema, tính toán trường `age_days` và `text_for_embedding` trong `src/ingestion/cleaning.py`.
  - Thiết lập Quality Gate theo chuẩn mới **Great Expectations 1.x** và giám sát Freshness SLA trong `src/observability/quality.py`.
  - Quản lý mô hình embedding `sentence-transformers/all-MiniLM-L6-v2` và ChromaDB vector collection (`papers-baseline`, `papers-corrupted`, `papers-repaired`).
  - Triển khai 6 kịch bản tiêm lỗi dữ liệu synthetic trong `src/ingestion/corruption.py` và đo lường sự sụt giảm chỉ số.
  - Thực thi cơ chế Idempotent Repair phục hồi dữ liệu từ raw snapshot.
  - Kết nối luồng thực thi trong `src/pipelines/phase1.py` và `src/pipelines/corruption_flow.py`, xuất báo cáo đối chiếu 3 trạng thái.
- **Điều học được / Đóng góp chính:**
  - Hiểu sâu sắc về thiết kế Idempotent Pipeline, Data Lineage và cơ chế phát hiện Silent Failure bằng Great Expectations 1.x.

