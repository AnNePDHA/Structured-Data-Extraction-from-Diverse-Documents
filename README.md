# Luận văn tốt nghiệp Thạc sĩ

**Đề tài:** Xây dựng hệ thống trích xuất dữ liệu có cấu trúc từ đa dạng tài liệu và đánh giá hiệu năng các mô hình VLM và OCR-LLM

| Mục | Nội dung |
|---|---|
| Học viên | Phạm Đại Hoàng An (2470281) |
| GVHD | TS. Trần Tuấn Anh |
| Trường | Đại học Bách Khoa, ĐHQG TP.HCM, Khoa Khoa học và Kỹ thuật Máy tính |
| Giai đoạn | **Giai đoạn 2, thực hiện luận văn** (đề cương đã bảo vệ xong tháng 06/2026) |
| Hạn nộp | Tháng 12/2026 |

## Trạng thái

Đã xong ở giai đoạn đề cương:

- Benchmark 60 mẫu / 5 tập con trong `data-processed/`.
- Hai pipeline (VLM Direct, OCR-LLM) và bộ chỉ số đánh giá trong `pipelines/`, `evaluation/`.
- 540 lượt trích xuất trên 5 mô hình, kết quả trong `results/`.
- Báo cáo đề cương đủ 5 chương trong `paper/thesis.tex` (giữ nguyên, không sửa). Bản PDF đã nộp và slide bảo vệ nằm ở `archive/de_cuong/`.

Yêu cầu của hội đồng cho giai đoạn 2: không đổi scope, **hiện thực hệ thống thật**, tập trung vào xây dựng hệ thống.

## Cấu trúc thư mục

```
LVTN/
├── outline/            THESIS_CONTEXT.md, WRITING_STYLE.md, DATASOURCE_CONTEXT.md
├── paper/              luan_van.tex (luận văn giai đoạn 2, nguồn duy nhất của nội dung chương), thesis.tex (đề cương, không sửa), references.bib, Images/
├── archive/de_cuong/   PDF báo cáo và slide bảo vệ đề cương
├── config/             fields/ (schema trường), prompts/ (prompt template)
├── pipelines/          Pipeline A, Pipeline B, model client, OCR engine
├── evaluation/         metrics.py
├── scripts/            chuẩn bị dữ liệu, run_benchmark.py, run_eda.py
├── notebooks/          eda_dataset.ipynb, results_comparison.ipynb
├── data/               dữ liệu thô (public + data/VN/DataV3 tự thu thập)
├── data-processed/     benchmark 60 mẫu
├── results/            kết quả theo mô hình, bảng tổng hợp, figures/
└── references/         PDF tài liệu tham khảo
```

Mã nguồn hệ thống của giai đoạn 2 sẽ đặt ở `system/`, tái dùng `pipelines/` và `evaluation/`.

## Lộ trình giai đoạn 2

| Tuần | Ngày | Việc |
|---|---|---|
| 1 | 12–18/10 | Chốt yêu cầu chức năng, kiến trúc và tech stack của hệ thống. Chốt với GVHD việc tách chương hệ thống riêng. |
| 2–3 | 19/10–01/11 | Backend: API bọc `VLMDirectPipeline` và `OCRLLMPipeline` (upload, khai báo schema, chạy job, lấy kết quả), lưu lịch sử, nhận PDF và ảnh. |
| 4–5 | 02–15/11 | Frontend 5 bước theo mockup mục 4.6: upload, schema, chọn pipeline và model, tiến trình, kết quả kèm sửa trường và xuất file. |
| 6 | 16–22/11 | Gợi ý pipeline theo kết quả benchmark, đánh dấu trường cần review. Kiểm thử đầu cuối trên 60 mẫu, đo độ trễ và chi phí của hệ thống. |
| 7 | 23–29/11 | Viết chương hệ thống (yêu cầu, kiến trúc, hiện thực, kiểm thử), thay hình mockup bằng ảnh chụp hệ thống thật, cập nhật chương 1 và chương kết luận. |
| 8 | 30/11–06/12 | Trang phụ đầu và phụ lục. Gửi GVHD đọc. |
| 9 | 07–13/12 | Sửa theo GVHD, nộp, làm slide bảo vệ. |

Đề xuất tech stack, chốt ở tuần 1: FastAPI + SQLite cho backend, giao diện web dựng theo mockup. Phương án dự phòng nếu thiếu thời gian: Streamlit.

## Việc còn thiếu

Hệ thống:

- [ ] Chốt yêu cầu chức năng và kiến trúc
- [ ] Backend bọc 2 pipeline
- [ ] Giao diện 5 bước
- [ ] Kiểm thử đầu cuối trên 60 mẫu

Luận văn (`paper/luan_van.tex`, đã dựng khung 6 chương, các mục mới còn `% TODO`):

- [ ] Mục 4.6 khuyến nghị lựa chọn pipeline
- [ ] Chương 5 hệ thống, thay cho mục 4.6 mockup của đề cương
- [ ] Nhiệm vụ luận văn thạc sĩ
- [ ] Lời cảm ơn
- [ ] Tóm tắt và Abstract
- [ ] Lời cam đoan
- [ ] Danh sách từ viết tắt
- [ ] Phụ lục A: danh sách mô hình và cấu hình thực nghiệm
- [ ] Phụ lục B: prompt template chi tiết
- [ ] Phụ lục C: kết quả thực nghiệm đầy đủ
- [ ] Slide bảo vệ luận văn

## Chạy lại thực nghiệm

```bash
.venv\Scripts\activate
python scripts/run_benchmark.py --help
```

Khóa API đặt trong `.env`, mẫu ở `.env.example`.
