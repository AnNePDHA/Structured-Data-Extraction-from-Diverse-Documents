# -*- coding: utf-8 -*-
"""
Preprocess Kaggle OCR dataset (rubabq66/invoice-receipt-contract-ocr) — ground truth là text thô.

Hai target:
  --target invoice : gộp 7 SROIE + 7 Kaggle-invoice + 6 Kaggle-receipt → 20 mẫu,
                     map về schema SROIE {company, date, address, total}.
  --target contract: 20 mẫu CONTRACT, parse 5 field {party_a, party_b, effective_date,
                     term, governing_law}.

NGUYÊN TẮC: KHÔNG normalize. Mọi giá trị trích ra là substring nguyên văn như trên document
(date, currency, hoa/thường giữ nguyên). Field không match → null.

Usage:
    python scripts/preprocess_kaggle_ocr.py --target invoice
    python scripts/preprocess_kaggle_ocr.py --target contract
"""

import argparse
import json
import random
import re
import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SROIE_SRC    = PROJECT_ROOT / "data" / "EN" / "Typed-Invoice"      # entities/ + img/
KAGGLE_SRC   = PROJECT_ROOT / "data" / "EN" / "Typed-Contract"     # ground_truth/ + images/


# ---------------------------------------------------------------------------
# Parsers — chỉ trích substring nguyên văn, KHÔNG reformat
# ---------------------------------------------------------------------------

RE_PARTIES   = re.compile(r'between\s+(.+?)\s*\("Party A"\)\s+and\s+(.+?)\s*\("Party B"\)', re.IGNORECASE)
# Effective date = date đầu tiên trong document. Không dùng anchor từ ngữ vì text wrap
# có thể cắt bất kỳ từ nào ("effect ive", "a s of"). Date này luôn == date ở chữ ký.
RE_ANY_DATE  = re.compile(r'([0-9]{4}-[0-9]{2}-[0-9]{2})')
RE_TERM      = re.compile(r'TERM:\s*(.+?)\.', re.IGNORECASE)
RE_GOV_LAW   = re.compile(r'governed\s+by\s+the\s+laws\s+of\s+(.+?)\.', re.IGNORECASE)

RE_FROM      = re.compile(r'^From:\s*(.+)$', re.MULTILINE)
RE_DATE      = re.compile(r'Date:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})')
RE_TOTAL     = re.compile(r'^TOTAL:\s*(.+)$', re.MULTILINE)
RE_TIME      = re.compile(r'Time:\s*([0-9]{2}:[0-9]{2}:[0-9]{2})')


def parse_contract(text: str) -> dict:
    # Join các dòng vì text wrap giữa câu (vd "effective as \nof 2026-..")
    joined = re.sub(r'\s+', ' ', text)
    m_party = RE_PARTIES.search(joined)
    m_eff   = RE_ANY_DATE.search(joined)
    m_term  = RE_TERM.search(joined)
    m_law   = RE_GOV_LAW.search(joined)
    return {
        "party_a":        m_party.group(1).strip() if m_party else None,
        "party_b":        m_party.group(2).strip() if m_party else None,
        "effective_date": m_eff.group(1)           if m_eff   else None,
        "term":           m_term.group(1).strip()  if m_term  else None,
        "governing_law":  m_law.group(1).strip()   if m_law   else None,
    }


def parse_kaggle_invoice(text: str) -> dict:
    """Map về schema SROIE: company=From, date=Date, address=null, total=TOTAL."""
    m_from  = RE_FROM.search(text)
    m_date  = RE_DATE.search(text)
    m_total = RE_TOTAL.search(text)
    return {
        "company": m_from.group(1).strip()  if m_from  else None,
        "date":    m_date.group(1)          if m_date  else None,
        "address": None,
        "total":   m_total.group(1).strip() if m_total else None,
    }


def parse_kaggle_receipt(text: str) -> dict:
    """Map về schema SROIE: company=dòng merchant (sau dòng [..]), address=dòng location."""
    lines = [ln.rstrip("\n") for ln in text.splitlines()]
    company = address = None
    # Dòng 0 là "[BRAND]"; dòng 1 = merchant; dòng 2 = location
    if len(lines) >= 2 and lines[0].strip().startswith("["):
        company = lines[1].strip() or None
        if len(lines) >= 3:
            address = lines[2].strip() or None
    m_date  = RE_DATE.search(text)
    m_total = RE_TOTAL.search(text)
    return {
        "company": company,
        "date":    m_date.group(1)          if m_date  else None,
        "address": address,
        "total":   m_total.group(1).strip() if m_total else None,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def write_record(gt_dir: Path, img_out: Path, src_img: Path, doc_name: str,
                 doc_type: str, fields: dict) -> bool:
    """Ghi 1 JSON envelope + copy ảnh. Return True nếu copy ảnh thành công."""
    ext = src_img.suffix
    record = {
        "doc_name":   doc_name,
        "lang":       "EN",
        "doc_type":   doc_type,
        "subtype":    "typed",
        "image_path": f"img/{doc_name}{ext}",
        "fields":     fields,
    }
    (gt_dir / f"{doc_name}.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if src_img.exists():
        shutil.copy(src_img, img_out / f"{doc_name}{ext}")
        return True
    return False


def count_nulls(fields: dict) -> int:
    return sum(1 for v in fields.values() if v is None)


def prepare_out(folder_name: str) -> tuple[Path, Path]:
    out_root = PROJECT_ROOT / "data-processed" / "EN" / folder_name
    gt_dir   = out_root / "ground_truth"
    img_out  = out_root / "img"
    if out_root.exists():
        shutil.rmtree(out_root)
    gt_dir.mkdir(parents=True, exist_ok=True)
    img_out.mkdir(parents=True, exist_ok=True)
    return gt_dir, img_out


# ---------------------------------------------------------------------------
# Target: invoice (merge 7/7/6)
# ---------------------------------------------------------------------------

def build_invoice(seed: int):
    random.seed(seed)
    gt_dir, img_out = prepare_out("Typed-Invoice")

    n_sroie, n_inv, n_rcpt = 7, 7, 6
    total_null = 0

    # --- 7 SROIE (entities JSON sẵn) ---
    sroie_files = sorted((SROIE_SRC / "entities").glob("*.txt"))
    sroie_pick  = sorted(random.sample(sroie_files, n_sroie))
    for f in sroie_pick:
        fields = json.loads(f.read_text(encoding="utf-8"))  # đã là {company,date,address,total}
        src_img = SROIE_SRC / "img" / f"{f.stem}.jpg"
        write_record(gt_dir, img_out, src_img, f.stem, "invoice", fields)
        total_null += count_nulls(fields)

    # --- 7 Kaggle invoice + 6 receipt (text thô) ---
    gt_src = KAGGLE_SRC / "ground_truth"
    inv_files  = sorted(gt_src.glob("INVOICE_*.txt"))
    rcpt_files = sorted(gt_src.glob("RECEIPT_*.txt"))
    inv_pick   = sorted(random.sample(inv_files,  n_inv))
    rcpt_pick  = sorted(random.sample(rcpt_files, n_rcpt))

    for f in inv_pick:
        fields = parse_kaggle_invoice(f.read_text(encoding="utf-8"))
        src_img = KAGGLE_SRC / "images" / f"{f.stem}.png"
        write_record(gt_dir, img_out, src_img, f.stem, "invoice", fields)
        # address=null là hợp lệ cho invoice synthetic → không tính là lỗi
        total_null += count_nulls({k: v for k, v in fields.items() if k != "address"})

    for f in rcpt_pick:
        fields = parse_kaggle_receipt(f.read_text(encoding="utf-8"))
        src_img = KAGGLE_SRC / "images" / f"{f.stem}.png"
        write_record(gt_dir, img_out, src_img, f.stem, "invoice", fields)
        total_null += count_nulls(fields)

    n_jpg = len(list(img_out.glob("*.jpg")))
    n_png = len(list(img_out.glob("*.png")))
    print(f"[invoice] Đã ghi 20 JSON vào {gt_dir}")
    print(f"  Nguồn: {n_sroie} SROIE + {n_inv} Kaggle-invoice + {n_rcpt} receipt")
    print(f"  Ảnh: {n_jpg} .jpg + {n_png} .png")
    print(f"  Field null ngoài dự kiến: {total_null}")


# ---------------------------------------------------------------------------
# Target: contract
# ---------------------------------------------------------------------------

def build_contract(seed: int, sample: int):
    random.seed(seed)
    gt_dir, img_out = prepare_out("Typed-Contract")

    files = sorted((KAGGLE_SRC / "ground_truth").glob("CONTRACT_*.txt"))
    pick  = sorted(random.sample(files, min(sample, len(files))))

    total_null = 0
    for f in pick:
        fields = parse_contract(f.read_text(encoding="utf-8"))
        src_img = KAGGLE_SRC / "images" / f"{f.stem}.png"
        write_record(gt_dir, img_out, src_img, f.stem, "contract", fields)
        total_null += count_nulls(fields)

    print(f"[contract] Đã ghi {len(pick)} JSON vào {gt_dir}")
    print(f"  Ảnh: {len(list(img_out.glob('*.png')))} .png")
    print(f"  Field null: {total_null}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, choices=["invoice", "contract"])
    parser.add_argument("--seed",   type=int, default=42)
    parser.add_argument("--sample", type=int, default=20, help="Chỉ áp dụng cho contract")
    args = parser.parse_args()

    if args.target == "invoice":
        build_invoice(args.seed)
    else:
        build_contract(args.seed, args.sample)


if __name__ == "__main__":
    main()
