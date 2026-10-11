# DATASOURCE CONTEXT — Dữ liệu thực nghiệm

> File này track kế hoạch và trạng thái dữ liệu thực nghiệm, tương tự THESIS_CONTEXT.md.
> Cập nhật lần cuối: 2026-10-11

---

## 1. Ma trận dữ liệu thực tế

**Tổng benchmark: 60 mẫu — đã xây dựng xong trong `data-processed/`**

| Subset folder | Lang | Doc Type | Subtype | Số mẫu | Nguồn |
|---|---|---|---|---|---|
| `EN/Typed-Invoice` | EN | invoice | typed | 20 | SROIE (7) + Kaggle rubabq66 invoice (7) + Kaggle rubabq66 receipt (6) |
| `EN/Typed-Contract` | EN | contract | typed | 20 | Kaggle rubabq66 invoice-receipt-contract-ocr (synthetic contracts) |
| `VN/Typed-IdCard` | VN | id_card | typed | 10 | Roboflow CCCD diop (5) + CCCD thực tự thu thập (5) |
| `VN/Typed-Contract` | VN | contract | typed | 5 | HĐ cho vay ngân hàng (tự thu thập) |
| `VN/Handwritten-Contract` | VN | contract | handwritten | 5 | HĐ mở tài khoản ngân hàng (tự thu thập, KH6–KH10) |
| **Tổng** | | | | **60** | |

**Định dạng chuẩn:** Mỗi mẫu gồm 1 ảnh PNG (trang đầu, convert từ TIFF/PDF nếu cần) + 1 file JSON ground truth theo schema thống nhất `{doc_name, lang, doc_type, subtype, image_path, fields}`.

---

## 2. Chi tiết từng nguồn

### SROIE (7 mẫu → merged vào Typed-Invoice)
- **Link:** huggingface.co/datasets/rth/sroie-2019-v2
- **Paper:** Huang et al., ICDAR 2019
- **Ground truth có sẵn:** `company`, `date`, `address`, `total`
- **Cách lấy:** Lấy 7 mẫu từ tập test, chọn ngẫu nhiên seed=42
- **Trạng thái:** ✅ Đã xử lý, merge vào `EN/Typed-Invoice/`

---

### Kaggle — invoice-receipt-contract-ocr (rubabq66) — EN Invoice + Contract
- **Link:** kaggle.com/datasets/rubabq66/invoice-receipt-contract-ocr
- **Mapping:** EN Invoice (7 invoice + 6 receipt → merged) + EN Contract (20 mẫu synthetic)
- **Ground truth có sẵn:** Raw text annotation per document; tác giả parse và map sang schema chuẩn
  - Invoice schema: `company` (From), `date`, `address` (null), `total`
  - Receipt schema: `company` (merchant), `date`, `address` (location), `total`
  - Contract schema: `party_a`, `party_b`, `effective_date`, `term`, `governing_law`, `contract_number`, `contract_value`
- **Ghi chú:** Thay thế CUAD (chỉ có text, không có ảnh) cho EN Contract
- **Trạng thái:** ✅ Đã xử lý — 13 mẫu vào `EN/Typed-Invoice/`, 20 mẫu vào `EN/Typed-Contract/`

---

### Roboflow CCCD (diop/clone-dataset-type-od) — 5 mẫu
- **Link:** universe.roboflow.com/diop/clone-dataset-type-od/dataset/2
- **Ground truth có sẵn:** Bounding box + nhãn field (object detection format)
- **Field dùng trong thesis:** `dob`, `expire_date`, `name`, `nationality`, `origin_place`, `id_num` (6 field — đã bỏ `current_place`)
- **Ghi chú:** Annotation là bbox, tác giả map sang structured JSON theo 6 field CCCD
- **Trạng thái:** ✅ 5 mẫu đã vào `VN/Typed-IdCard/`

---

### Real CCCD scans — data/VN/DataV3 (5 mẫu)
- **Nguồn:** `data/VN/DataV3/Data/Training/2. Phong HTTD_CreditSupport/CCCD/` — tài liệu thực từ ngân hàng
- **Định dạng gốc:** `.tif` nhiều trang → lấy trang đầu, convert sang PNG
- **Field:** 6 field CCCD (cùng schema với Roboflow)
- **Trạng thái:** ✅ 5 mẫu PNG đã vào `VN/Typed-IdCard/`

---

### Real bank loan contracts — data/VN/DataV3 (5 mẫu typed)
- **Nguồn:** `data/VN/DataV3/Data/Training/2. Phong HTTD_CreditSupport/HOP DONG CHO VAY/`
- **Loại:** Hợp đồng cho vay ngân hàng (đánh máy)
- **Định dạng gốc:** `.tif` → convert trang đầu sang PNG
- **Field:** `party_a`, `party_b`, `effective_date`, `term`, `governing_law`, `contract_number`, `contract_value` (7 field)
- **Trạng thái:** ✅ 5 mẫu PNG đã vào `VN/Typed-Contract/`

---

### Real bank account-opening contracts — data/VN/DataV3 (5 mẫu handwritten)
- **Nguồn:** `data/VN/DataV3/Data/Training/1. Phong DVTK_OpeningAcoount/HOP DONG MO TAI KHOAN/` — chỉ lấy KH6–KH10
- **Loại:** Hợp đồng mở tài khoản ngân hàng (có phần viết tay)
- **Định dạng gốc:** `.tif` → convert trang đầu sang PNG
- **Field:** 7 field contract (cùng schema typed contract)
- **Trạng thái:** ✅ 5 mẫu PNG đã vào `VN/Handwritten-Contract/`

---

## 3. Schema ground truth

| doc_type | Field keys | Số field |
|---|---|---|
| `invoice` | `company`, `date`, `address`, `total` | 4 |
| `contract` | `party_a`, `party_b`, `effective_date`, `term`, `governing_law`, `contract_number`, `contract_value` | 7 |
| `id_card` | `dob`, `expire_date`, `name`, `nationality`, `origin_place`, `id_num` | 6 |

Config field descriptions: `config/fields/{doc_type}.json`
JSON schema validation: `data/schema/{doc_type}.json`

---

## 4. Tổng hợp nguồn (thực tế)

| Nguồn | Loại | Subset | Số mẫu | Trạng thái |
|---|---|---|---|---|
| SROIE (Huang et al., ICDAR 2019) | Public | EN/Typed-Invoice | 7 | ✅ |
| Kaggle rubabq66 — invoice | Public | EN/Typed-Invoice | 7 | ✅ |
| Kaggle rubabq66 — receipt | Public | EN/Typed-Invoice | 6 | ✅ |
| Kaggle rubabq66 — contract | Public | EN/Typed-Contract | 20 | ✅ |
| Roboflow CCCD (diop) | Public | VN/Typed-IdCard | 5 | ✅ |
| CCCD thực tế | Tự thu thập | VN/Typed-IdCard | 5 | ✅ |
| HĐ cho vay | Tự thu thập | VN/Typed-Contract | 5 | ✅ |
| HĐ mở tài khoản (KH6–10) | Tự thu thập | VN/Handwritten-Contract | 5 | ✅ |
| **Tổng** | | | **60** | |

---

## 5. Vấn đề còn mở

| # | Vấn đề | Mức độ | Hướng xử lý |
|---|---|---|---|
| 1 | VN Handwritten Contract chỉ có 5 mẫu | 🟡 Thấp | Đủ để so sánh typed vs handwritten trong VN Contract; có thể mở rộng sau |

---

## 6. Changelog

| Ngày | Nội dung |
|---|---|
| 2026-05-10 | Khởi tạo DATASOURCE_CONTEXT.md — tổng hợp kế hoạch data 155 tài liệu |
| 2026-05-10 | Bỏ CORD (redundant với SROIE); recategorize CCCD thành self-created synthetic |
| 2026-05-19 | SROIE: ✅ đã tải 20 mẫu vào `data-processed/EN/Typed-Invoice/`. Thay CUAD bằng Kaggle (rubabq66/invoice-receipt-contract-ocr) cho EN Contract. Thay "CCCD tự tạo template" bằng Roboflow dataset (diop/clone-dataset-type-od) cho VI ID Card. VI Contract chuyển từ "Bộ LĐTBXH template" sang "tự tìm trên mạng + tự annotate" |
| 2026-05-24 | Hoàn tất xây dựng toàn bộ dataset. Thu hẹp scope từ 155 (kế hoạch) xuống thực tế. Thêm 3 nguồn tài liệu thực tự thu thập (CCCD, HĐ cho vay, HĐ mở TK). Bỏ các tập chưa tải (MIDV-500, FUNSD, MC-OCR, tất cả handwritten synthetic). Merge invoice+receipt thành 1 Typed-Invoice (20 mẫu). |
| 2026-05-24 | Benchmark chốt **60 mẫu** (3 doc_type: invoice/contract/id_card). Loại custom (nhãn dinh dưỡng) khỏi thesis — không show. Bỏ `current_place` khỏi schema id_card (còn 6 field). Gỡ tên riêng "DataV3"/"Nestlé"/"Milo" khỏi thesis.tex và phần trình bày. |
| 2026-10-11 | Chuyển tài liệu ngân hàng tự thu thập từ `draft/DataV3/` sang `data/VN/DataV3/`. Xóa hẳn mẫu custom (nhãn dinh dưỡng) và folder `VN/Typed-Custom`. |
