# THESIS CONTEXT — Luận Văn Thạc Sĩ

> File này dùng để cung cấp context cho Claude Code khi thực hiện các task liên quan đến luận văn.
>
> Cập nhật lần cuối: 2026-10-11 — xem **Mục 15. Changelog** để biết lịch sử thay đổi.

---

## 1. Thông tin cơ bản

| Mục | Nội dung |
|---|---|
| **Tên đề tài** | Xây dựng hệ thống trích xuất dữ liệu có cấu trúc từ đa dạng tài liệu và đánh giá hiệu năng các mô hình VLM và OCR-LLM |
| **Học viên** | Phạm Đại Hoàng An |
| **Trường** | Đại học Bách Khoa — ĐHQG TP.HCM |
| **Hướng** | Khoa học Dữ liệu (Data Science) |
| **GVHD** | TS. Trần Tuấn Anh |
| **Giai đoạn hiện tại** | Giai đoạn 2 — Thực hiện luận văn (đề cương đã bảo vệ xong, 06/2026) |
| **Hạn nộp luận văn** | Tháng 12/2026 |
| **Trọng tâm giai đoạn 2** | Hiện thực hệ thống trích xuất chạy thật (yêu cầu của hội đồng), không đổi scope |

---

## 2. Mục tiêu đề tài

Đề tài có **2 mục tiêu song song**:

### Mục tiêu 1 — Đánh giá & So sánh
So sánh hai hướng tiếp cận trích xuất dữ liệu có cấu trúc từ tài liệu:

- **VLM Direct Extraction**: Đưa ảnh tài liệu trực tiếp vào Vision Language Model → JSON output
- **OCR-LLM Pipeline**: OCR engine trích xuất text → LLM parse text → JSON output

### Mục tiêu 2 — Xây dựng hệ thống
Thiết kế và hiện thực hệ thống trích xuất dữ liệu có cấu trúc thực tế dựa trên kết quả đánh giá từ Mục tiêu 1.

> Trạng thái: Mục tiêu 1 đã xong ở giai đoạn đề cương (540 lượt trích xuất). Mục tiêu 2 mới có mockup giao diện 5 bước (mục 4.6 của `thesis.tex`), **đây là phần việc chính của giai đoạn 2**.

---

## 3. Scope đã xác định

```
Loại tài liệu : Invoice / CCCD (ID card) / Hợp đồng (Contract)
Ngôn ngữ      : Tiếng Anh (EN) + Tiếng Việt (VI)
Dạng văn bản  : Typed (đánh máy) + Handwritten (viết tay)
Dataset       : Public datasets (EN) + tài liệu thực tế tự thu thập (VN)
Output format : Structured JSON theo schema định sẵn
```

---

## 4. Research Gap — Novelty

Qua khảo sát tài liệu, **chưa có nghiên cứu nào** đồng thời thỏa mãn cả 3 điều kiện:
1. Tài liệu **tiếng Việt** (invoice, ID card, contract)
2. So sánh **VLM vs OCR-LLM** trên cùng framework đánh giá chuẩn hóa
3. Phân tích riêng **typed vs handwritten**

---

## 5. Mục lục đề cương (đã thống nhất)

```
1  Giới thiệu
   1.1  Đặt vấn đề
   1.2  Mục tiêu nghiên cứu
   1.3  Phạm vi và giới hạn nghiên cứu
   1.4  Đóng góp của luận văn
   1.5  Tổng quan về báo cáo

2  Công trình liên quan
   (Các nghiên cứu liên quan — liệt kê từng paper, không chia subsection theo chủ đề,
    mỗi công trình trình bày theo cấu trúc: Giới thiệu → Phương pháp → Nhận xét)
   2.X  Tổng hợp và xác định khoảng trống nghiên cứu

3  Cơ sở lý thuyết
   3.1  Tổng quan về trích xuất dữ liệu từ tài liệu thông minh (IDP)
   3.2  Optical Character Recognition (OCR)
   3.3  Large Language Model (LLM)
   3.4  Vision Language Model (VLM)
   3.5  Structured Data Extraction
   3.6  Các chỉ số đánh giá

4  Phương pháp đề xuất
   4.1  Tổng quan kiến trúc hệ thống
   4.2  Dữ liệu thực nghiệm
   4.3  VLM Extraction Approach & Pipeline
   4.4  OCR-LLM Extraction Approach & Pipeline
   4.5  Kết quả thực nghiệm
   4.6  Thiết kế hệ thống trích xuất dữ liệu (Mockup)

5  Kết luận
   5.1  Nhận xét và tổng kết
   5.2  Hạn chế của nghiên cứu
   5.3  Hướng phát triển trong tương lai

Tài liệu tham khảo
```

---

## 6. Kiến trúc hệ thống

```
Input Document (ảnh PNG, trang đầu)
        │
        ▼
Field config (config/fields/*.json) + Prompt template (config/prompts/*.md)
        │
    ┌───┴───────────────┐
    ▼                   ▼
┌──────────────┐  ┌─────────────────────────────────┐
│ Pipeline A   │  │ Pipeline B                      │
│ VLM Direct   │  │ OCR → LLM                       │
│ ảnh + prompt │  │ OCR: EasyOCR (EN)               │
│ → 1 lần gọi  │  │      Azure Doc Intelligence (VN)│
│              │  │ LLM: chỉ nhận text OCR          │
└──────┬───────┘  └───────────────┬─────────────────┘
       └────────────┬─────────────┘
                    ▼
        JSON theo schema → evaluation/metrics.py
```

Code: `pipelines/vlm_direct.py`, `pipelines/ocr_llm.py`, lớp chung `pipelines/base.py` (retry + pacing), client theo nhà cung cấp trong `pipelines/model_clients.py`, OCR engine trong `pipelines/ocr_engines.py`.

---

## 7. Mô hình đã benchmark

5 mô hình, 9 cấu hình, 60 mẫu mỗi cấu hình = **540 lượt trích xuất** (chạy 24–25/05/2026).

| Mô hình | Model ID | Nhà cung cấp | Pipeline |
|---|---|---|---|
| GPT-5.2 | `gpt-5.2-chat` | Azure OpenAI | A + B |
| GPT-4o | `gpt-4o` | Azure OpenAI | A + B |
| Llama-4-Maverick | `Llama-4-Maverick-17B-128E-Instruct-FP8` | Azure AI Foundry | A + B |
| Phi-4-MM | `Phi-4-multimodal-instruct` | Azure AI Foundry | A + B |
| DeepSeek-V4 | `DeepSeek-V4-Flash` | Azure AI Foundry | chỉ B (thuần văn bản) |

OCR engine của Pipeline B: EasyOCR cho tập tiếng Anh, Azure Document Intelligence cho tập tiếng Việt.

Kết quả đầy đủ: `results/summary_table.csv`, `results/accuracy_table.csv`, hình trong `results/figures/`.

| Kết quả chính | Giá trị |
|---|---|
| Dẫn đầu tổng thể | Llama-4-Maverick, VLM Direct: EM 83,6%, Token-F1 92,3%, 1,76 s/tài liệu, 0,91 USD/1000 tài liệu |
| Dẫn đầu nhóm OCR-LLM | DeepSeek-V4: EM 78,6%, tiếng Việt EM 82,0% (cao hơn tiếng Anh 77,0%) |
| Sụt giảm EN → VN lớn nhất | Phi-4-MM, VLM Direct: EM 88,8% → 39,4%, hallucination 26,8% |
| Rẻ nhất / đắt nhất | Phi-4-MM OCR-LLM 0,08 USD / GPT-5.2 VLM Direct 6,66 USD mỗi 1000 tài liệu |

---

## 8. Dataset thực nghiệm

**Tổng benchmark: 60 mẫu / 5 subset** — đã xây dựng xong trong `data-processed/`.

| Subset | Lang | Doc Type | Subtype | Mẫu | Nguồn |
|---|---|---|---|---|---|
| EN/Typed-Invoice | EN | invoice | typed | 20 | SROIE (7) + Kaggle rubabq66 invoice (7) + receipt (6) |
| EN/Typed-Contract | EN | contract | typed | 20 | Kaggle rubabq66 synthetic contracts |
| VN/Typed-IdCard | VN | id_card | typed | 10 | Roboflow CCCD diop (5) + CCCD thực tự thu thập (5) |
| VN/Typed-Contract | VN | contract | typed | 5 | HĐ cho vay ngân hàng (tự thu thập) |
| VN/Handwritten-Contract | VN | contract | handwritten | 5 | HĐ mở tài khoản ngân hàng (tự thu thập, KH6–KH10) |

Chi tiết nguồn và schema: xem `outline/DATASOURCE_CONTEXT.md`.

---

## 9. Evaluation Framework

### 4 chiều đánh giá

| Chiều | Metrics |
|---|---|
| **Accuracy** | Field-level Exact Match, Token-level F1 |
| **Robustness** | Typed vs Handwritten drop, EN vs VI drop, low-quality image |
| **Efficiency** | Latency (ms/doc), Cost (USD/1000 docs) |
| **Reliability** | Hallucination Rate, Schema Compliance Rate |

### Điều kiện chuẩn hóa khi so sánh
- Cùng prompt template cho tất cả model
- Cùng input resolution
- Cùng JSON schema yêu cầu
- Temperature = 0 (deterministic)
- Phân tích theo 3 chiều: loại tài liệu / ngôn ngữ / typed vs handwritten

---

## 10. Tài liệu tham khảo đã xác định (40 tài liệu)

### Nhóm 1 — Công trình liên quan

| # | Paper | arXiv / Nguồn | Năm |
|---|---|---|---|
| 1 | LLM-centric Pipeline for Invoice IE | hal-04772570 | 2024 |
| 2 | Automated Invoice Data Extraction: LLM + OCR | arXiv:2511.05547 | 2025 |
| 3 | BLOCKIE: IE from VRDs using LLM Segmentation | arXiv:2505.13535 | 2025 |
| 4 | Multi-Modal Vision vs Text-Based: Invoice Benchmark | arXiv:2509.04469 | 2025 |
| 5 | Invoice IE: Methods and Performance Evaluation | arXiv:2510.15727 | 2025 |
| 6 | Hybrid Architecture for Claim Document Understanding | arXiv:2601.01897 | 2025 |
| 7 | Multi-Stage Field Extraction: OCR + Compact VLMs | arXiv:2510.23066 | 2025 |
| 8 | LayoutLM: Pre-training Text and Layout | KDD 2020 | 2020 |
| 9 | LayoutLMv3: Unified Text and Image Masking | ACM MM 2022 | 2022 |
| 10 | LayoutLLM: LLM Instruction Tuning for VrDU | arXiv:2403.14252 | 2024 |
| 11 | Donut: Document Understanding Transformer (OCR-free) | ECCV 2022 | 2022 |
| 12 | Document Parsing Unveiled: Survey | arXiv:2410.21169 | 2024 |
| 13 | Survey on MLLM-based VrDU | arXiv 2025 | 2025 |
| 14 | OmniDocBench | arXiv:2412.07626 — CVPR 2025 | 2025 |
| 15 | OmniAI OCR Benchmark | getomni.ai | 2024–2025 |
| 16 | DocILE Benchmark | arXiv:2302.05658 — ICDAR 2023 | 2023 |
| 17 | Image2Struct: Benchmarking VLM Structure Extraction | NeurIPS 2024 | 2024 |

### Nhóm 2 — Dataset

| # | Dataset | Nguồn |
|---|---|---|
| 18 | SROIE | ICDAR 2019 |
| 19 | CORD | NeurIPS 2019 |
| 20 | MIDV-500 | arXiv:1807.05786 |
| 21 | MIDV-2020 | ICPR 2021 |
| 22 | CUAD | NeurIPS 2021 |
| 23 | FUNSD | ICDAR 2019 |

### Nhóm 3 — Cơ sở lý thuyết

| # | Paper / Model | Nguồn |
|---|---|---|
| 24 | PaddleOCR / PP-Structure | Baidu 2022 |
| 25 | Tesseract OCR | Google |
| 26 | Surya OCR | Github 2024 |
| 27 | TrOCR: Transformer-based OCR | arXiv:2109.10282 |
| 28 | Attention Is All You Need (Transformer) | NeurIPS 2017 |
| 29 | Qwen2.5-VL Technical Report | arXiv:2502.13923 |
| 30 | InternVL2 | arXiv 2024 |
| 31 | GPT-4 Technical Report | arXiv:2303.08774 |
| 32 | Gemini 1.5 Technical Report | Google DeepMind 2024 |
| 33 | ANLS Metric for Document VQA | arXiv:1907.00490 |
| 34 | Hallucination Survey in LLMs | arXiv:2311.05232 |

### Nhóm 4 — Tools

| # | Tool | Dùng cho |
|---|---|---|
| 35 | PaddleOCR | OCR engine Pipeline B |
| 36 | OpenAI Python SDK | Gọi GPT-4o-mini |
| 37 | Google Generative AI SDK | Gọi Gemini API |
| 38 | OpenRouter API | Gọi open-source VLM free |
| 39 | HuggingFace Transformers | Load model local nếu cần |
| 40 | Pandas + JSON | Xử lý kết quả benchmark |

---

## 11. Vấn đề còn mở (giai đoạn 2)

| # | Vấn đề | Mức độ | Hướng xử lý dự kiến |
|---|---|---|---|
| 1 | Hệ thống mới là mockup, chưa có ứng dụng chạy được | 🔴 Cao | Hiện thực backend bọc 2 pipeline và giao diện 5 bước, đặt trong `system/` |
| 2 | Chưa chốt tech stack và kiến trúc hệ thống | 🔴 Cao | Chốt trong tuần 1 (đề xuất: FastAPI + SQLite, giao diện web theo mockup, dự phòng Streamlit) |
| 3 | Cấu trúc chương: chương 4 đang gộp phương pháp, thực nghiệm và mockup | 🟠 Trung bình | Đề xuất tách chương hệ thống riêng, cần GVHD xác nhận |
| 4 | Thiếu trang phụ đầu (nhiệm vụ, cảm ơn, tóm tắt, abstract, cam đoan) và phụ lục A/B/C | 🟠 Trung bình | Viết ở tuần 8 theo lộ trình trong `README.md` |
| 5 | Benchmark nhỏ (60 mẫu, 5 mẫu viết tay) | 🟡 Thấp | Giữ nguyên, đã ghi là hạn chế ở chương 5. Hội đồng không yêu cầu mở rộng |

Đã đóng: dataset tiếng Việt (dùng tài liệu ngân hàng tự thu thập), GVHD xác nhận scope (đề cương đã bảo vệ xong).

---

## 12. Cấu trúc thư mục

```
LVTN/
├── README.md                  ← trạng thái + lộ trình giai đoạn 2
├── outline/                   ← THESIS_CONTEXT, WRITING_STYLE, DATASOURCE_CONTEXT
├── paper/                     ← thesis.tex (nguồn duy nhất của nội dung chương), references.bib, Images/
├── archive/de_cuong/          ← PDF báo cáo và slide bảo vệ đề cương
├── config/fields, prompts     ← schema trường và prompt template dùng chung 2 pipeline
├── pipelines/                 ← Pipeline A, Pipeline B, model client, OCR engine
├── evaluation/metrics.py      ← EM, Token-F1, hallucination, schema compliance
├── scripts/                   ← chuẩn bị dữ liệu, run_benchmark.py, run_eda.py
├── notebooks/                 ← eda_dataset, results_comparison
├── data/                      ← dữ liệu thô (public + data/VN/DataV3 tự thu thập)
├── data-processed/            ← benchmark 60 mẫu / 5 tập con
├── results/                   ← kết quả theo mô hình, bảng tổng hợp, figures/
├── references/                ← PDF tài liệu tham khảo
└── system/                    ← (sẽ tạo) mã nguồn hệ thống giai đoạn 2
```

---

## 13. API Keys cần thiết

Biến môi trường trong `.env` (mẫu ở `.env.example`):

```bash
AZURE_OPENAI_ENDPOINT / AZURE_OPENAI_KEY / AZURE_OPENAI_API_VERSION      # gpt-4o, gpt-5.2-chat
AZURE_FOUNDRY_ENDPOINT / AZURE_FOUNDRY_KEY                              # Phi-4-MM, Llama-4-Maverick, DeepSeek-V4-Flash
AZURE_DOC_INTELLIGENCE_ENDPOINT / AZURE_DOC_INTELLIGENCE_KEY            # OCR tiếng Việt
GOOGLE_API_KEY                                                          # Gemini, không dùng trong benchmark chính
```

---

## 14. Ghi chú cho Claude Code

Khi nhận task liên quan đến luận văn này, Claude Code cần lưu ý:

1. **Ngôn ngữ code**: Python là ngôn ngữ chính
2. **Output format**: Tất cả extraction đều trả về JSON theo schema định sẵn
3. **Benchmark fairness**: Khi so sánh model, đảm bảo cùng prompt, cùng schema, temperature=0
4. **Rate limiting**: retry exponential backoff và pacing đã có sẵn trong `pipelines/base.py`, dùng lại, không viết mới
5. **Save kết quả incremental**: Dùng `.jsonl` append sau mỗi request, tránh mất dữ liệu khi bị rate limit giữa chừng
6. **Tiếng Việt**: Dùng `ensure_ascii=False` khi json.dumps, đảm bảo encoding UTF-8 toàn bộ pipeline
7. **Đây là luận văn thạc sĩ**: Code cần clean, có docstring, reproducible — không chỉ cần chạy được
8. **Nội dung chương**: chỉ sửa trong `paper/thesis.tex`, không còn file outline `.md` theo chương
9. **Hệ thống giai đoạn 2**: tái dùng `pipelines/` và `evaluation/`, không sao chép logic sang `system/`

---

## 15. Changelog

> Ghi lại mọi thay đổi quan trọng về scope, quyết định kỹ thuật, hoặc cập nhật từ GVHD.
> Format mỗi dòng: `| YYYY-MM-DD | Hạng mục | Nội dung thay đổi | Lý do / Nguồn |`

| Ngày | Hạng mục | Nội dung thay đổi | Lý do / Nguồn |
|---|---|---|---|
| 2026-04-22 | Khởi tạo | Tạo file THESIS_CONTEXT.md lần đầu | Tổng hợp từ conversation Claude.ai |
| 2026-04-22 | Mục lục | Xác định mục lục 5 chương, chương 4 gộp thực nghiệm và phương pháp | Thống nhất với cấu trúc luận văn tham khảo |
| 2026-04-22 | Models | Xác định danh sách 8 VLM free/low-cost để benchmark | Khảo sát API free tier tháng 4/2026 |
| 2026-04-22 | Dataset | Xác nhận 6 public dataset tiếng Anh; VI dataset còn là vấn đề mở | Khảo sát tài liệu |
| 2026-04-22 | References | Xác định 40 tài liệu tham khảo chia 4 nhóm | Tổng hợp từ khảo sát paper |
| 2026-05-08 | Mục lục | Chương 2: bỏ các mục 2.1–2.6, chuyển sang liệt kê công trình liền mạch không chia subsection | Quyết định viết related work theo từng paper thay vì theo chủ đề |
| 2026-05-08 | Mục lục | Chương 3: thêm 3.1 IDP (Intelligent Document Processing), renumber 3.2–3.6, đổi "Các độ đo" → "Các chỉ số đánh giá" | Cập nhật theo outline mới trong README.md |
| 2026-05-08 | Mục lục | Chương 4.6: thêm "(Mockup)" vào tên section | Cập nhật theo outline mới trong README.md |
| 2026-05-24 | Dataset | Hoàn tất 61 mẫu / 6 subset. Thêm real bank docs (DataV3) cho VN Contract + CCCD. Thêm custom doc_type (Milo nutrition label). Bỏ MIDV-500, FUNSD, MC-OCR, toàn bộ handwritten synthetic. Scope thu hẹp từ 155 → 61 mẫu | Xây dựng xong data-processed/ |
| 2026-05-24 | Scope | Thêm doc_type custom (nutrition label); cập nhật Dataset từ "chỉ public" sang "public (EN) + real documents (VN)" | Phản ánh thực tế dataset |
| 2026-05-25 | Models | Chốt 5 mô hình trên Azure (GPT-5.2, GPT-4o, Llama-4-Maverick, Phi-4-MM, DeepSeek-V4-Flash), bỏ danh sách Gemini/Qwen/OpenRouter. OCR: EasyOCR (EN) + Azure Document Intelligence (VN) | Thực nghiệm thực tế |
| 2026-05-27 | Kỹ thuật | Hoàn tất 540 lượt trích xuất, bảng tổng hợp và hình kết quả | `results/` |
| 2026-06-01 | Mục lục | Nộp báo cáo đề cương 54 trang | `archive/de_cuong/bao_cao_de_cuong.pdf` |
| 2026-06 | GVHD | Bảo vệ đề cương xong. Hội đồng: không đổi scope, yêu cầu hiện thực hệ thống thật, tập trung vào xây dựng hệ thống | Buổi bảo vệ đề cương |
| 2026-10-11 | Scope | Chuyển sang giai đoạn 2, hạn nộp tháng 12/2026, lộ trình 9 tuần trong `README.md` | Quyết định của học viên |
| 2026-10-11 | Kỹ thuật | Dọn folder: xóa `draft/`, `publish/`, `slides/`, outline theo chương, file build. `thesis.tex` là nguồn duy nhất của nội dung chương. Chuyển DataV3 sang `data/VN/DataV3/`. Xóa mẫu custom (nhãn dinh dưỡng) | Tối giản quản lý |
| _(thêm vào đây)_ | | | |

---

### Hướng dẫn cập nhật Changelog

Cuối mỗi buổi làm việc với Claude, paste câu này vào chat để lấy nội dung cập nhật:

```
Dựa trên conversation hôm nay, hãy liệt kê những quyết định/thay đổi mới
so với THESIS_CONTEXT.md để tôi thêm vào Changelog (format bảng markdown,
gồm: Ngày, Hạng mục, Nội dung thay đổi, Lý do/Nguồn).
```

Các **hạng mục** thường gặp cần ghi changelog:

| Hạng mục | Ví dụ |
|---|---|
| `Scope` | Thêm/bỏ loại tài liệu, ngôn ngữ, dạng văn bản |
| `Mục lục` | Đổi tên mục, thêm/bỏ mục, thay đổi cấu trúc chương |
| `Dataset` | Thêm/bỏ dataset, xác nhận số lượng mẫu |
| `Models` | Thêm/bỏ model, thay đổi API provider |
| `Metrics` | Thêm/bỏ metric đánh giá |
| `References` | Thêm paper mới vào danh sách tham khảo |
| `GVHD` | Phản hồi, yêu cầu, quyết định từ giảng viên hướng dẫn |
| `Vấn đề mở` | Giải quyết hoặc thêm vấn đề mới vào mục 11 |
| `Kỹ thuật` | Quyết định về công cụ, framework, cách triển khai |
