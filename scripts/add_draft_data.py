# -*- coding: utf-8 -*-
"""
Bổ sung data tiếng Việt từ data/VN/DataV3/ vào data-processed/.

3 tasks:
  cccd    : 5 CCCD .tif      → VN/Typed-IdCard/      (id_card, typed)    — ground truth trống
  loan    : 5 HĐ cho vay .tif→ VN/Typed-Contract/    (contract, typed)  — ground truth trống
  account : 5 HĐ mở TK KH6-10→ VN/Handwritten-Contract/ (contract, handwritten) — trống

TIFF nhiều trang → chỉ lấy TRANG ĐẦU, convert sang PNG.
Idempotent: JSON đã tồn tại sẽ KHÔNG bị ghi đè (bảo vệ giá trị user đã điền), trừ khi --force.

Usage:
    python scripts/add_draft_data.py --task all
    python scripts/add_draft_data.py --task cccd --force
"""

import argparse
import json
from collections import OrderedDict
from pathlib import Path

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATAV3       = PROJECT_ROOT / "data" / "VN" / "DataV3"
OUT_BASE     = PROJECT_ROOT / "data-processed" / "VN"

CCCD_SRC    = DATAV3 / "Data/Training/2. Phong HTTD_CreditSupport/CCCD"
LOAN_SRC    = DATAV3 / "Data/Training/2. Phong HTTD_CreditSupport/HOP DONG CHO VAY"
ACCOUNT_SRC = DATAV3 / "Data/Training/1. Phong DVTK_OpeningAcoount/HOP DONG MO TAI KHOAN"

ID_CARD_FIELDS = ["current_place", "dob", "expire_date", "name", "nationality", "origin_place", "id_num"]
CONTRACT_FIELDS = ["party_a", "party_b", "effective_date", "term", "governing_law", "contract_number", "contract_value"]


# ---------------------------------------------------------------------------
# Image conversion — chỉ trang đầu
# ---------------------------------------------------------------------------

def tiff_first_page_to_png(src: Path, dst: Path):
    with Image.open(src) as im:
        im.seek(0)  # trang đầu
        im.convert("RGB").save(dst, "PNG")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def prepare_out(folder_name: str) -> tuple[Path, Path]:
    out_root = OUT_BASE / folder_name
    img_dir  = out_root / "img"
    gt_dir   = out_root / "ground_truth"
    img_dir.mkdir(parents=True, exist_ok=True)
    gt_dir.mkdir(parents=True, exist_ok=True)
    return img_dir, gt_dir


def write_json(gt_dir: Path, doc_name: str, record: dict, force: bool) -> bool:
    """Ghi JSON. Return True nếu ghi mới, False nếu bỏ qua (đã tồn tại)."""
    path = gt_dir / f"{doc_name}.json"
    if path.exists() and not force:
        return False
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return True


def empty_record(doc_name: str, doc_type: str, subtype: str, field_keys: list) -> OrderedDict:
    return OrderedDict([
        ("doc_name",   doc_name),
        ("lang",       "VN"),
        ("doc_type",   doc_type),
        ("subtype",    subtype),
        ("image_path", f"img/{doc_name}.png"),
        ("fields",     OrderedDict((k, "") for k in field_keys)),
    ])


def process_tiff_folder(src_dir: Path, folder_name: str, doc_type: str, subtype: str,
                        field_keys: list, force: bool, name_filter=None):
    if not src_dir.exists():
        print(f"[ERROR] Không tìm thấy: {src_dir}")
        return
    img_dir, gt_dir = prepare_out(folder_name)
    tiffs = sorted(p for p in src_dir.iterdir() if p.suffix.lower() in (".tif", ".tiff"))
    if name_filter:
        tiffs = [p for p in tiffs if name_filter(p.stem)]

    n_img = n_new = n_skip = 0
    for src in tiffs:
        doc_name = src.stem
        dst_img = img_dir / f"{doc_name}.png"
        if not dst_img.exists():
            tiff_first_page_to_png(src, dst_img)
        n_img += 1
        rec = empty_record(doc_name, doc_type, subtype, field_keys)
        if write_json(gt_dir, doc_name, rec, force):
            n_new += 1
        else:
            n_skip += 1

    print(f"[{folder_name}] ảnh: {n_img}, JSON mới: {n_new}, bỏ qua: {n_skip}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", choices=["cccd", "loan", "account", "all"], default="all")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    t = args.task
    if t in ("cccd", "all"):
        process_tiff_folder(CCCD_SRC, "Typed-IdCard", "id_card", "typed", ID_CARD_FIELDS, args.force)
    if t in ("loan", "all"):
        process_tiff_folder(LOAN_SRC, "Typed-Contract", "contract", "typed", CONTRACT_FIELDS, args.force)
    if t in ("account", "all"):
        # Chỉ KH6..KH10
        kh = {f"KH{i}" for i in range(6, 11)}
        def is_kh6_10(stem: str) -> bool:
            return any(f"_{k}_" in stem for k in kh)
        process_tiff_folder(ACCOUNT_SRC, "Handwritten-Contract", "contract", "handwritten",
                            CONTRACT_FIELDS, args.force, name_filter=is_kh6_10)


if __name__ == "__main__":
    main()
