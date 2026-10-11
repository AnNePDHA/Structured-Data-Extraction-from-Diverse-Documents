# -*- coding: utf-8 -*-
"""
Khởi tạo ground_truth placeholder cho VN Typed-IdCard.

Roboflow dataset gốc là YOLO object-detection (chỉ bbox + class, không có text value),
nên không parse được giá trị. Script này MOVE ảnh sang data-processed/ và sinh JSON
placeholder (field rỗng "") để user tự điền tay.

NGUYÊN TẮC: idempotent — JSON đã tồn tại sẽ KHÔNG bị ghi đè (tránh mất giá trị đã điền),
trừ khi truyền --force.

Usage:
    python scripts/init_idcard_groundtruth.py
    python scripts/init_idcard_groundtruth.py --force   # ghi đè JSON cũ
"""

import argparse
import json
import shutil
from collections import OrderedDict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_IMAGES   = PROJECT_ROOT / "data" / "VN" / "Typed-IdCard" / "images"
OUT_ROOT     = PROJECT_ROOT / "data-processed" / "VN" / "Typed-IdCard"

# Đúng thứ tự field user yêu cầu
FIELD_KEYS = ["current_place", "dob", "expire_date", "name", "nationality", "origin_place", "id_num"]
IMG_EXTS   = {".jpg", ".jpeg", ".png"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Ghi đè JSON đã tồn tại")
    args = parser.parse_args()

    if not SRC_IMAGES.exists():
        print(f"[ERROR] Không tìm thấy: {SRC_IMAGES}")
        return

    img_out = OUT_ROOT / "img"
    gt_dir  = OUT_ROOT / "ground_truth"
    img_out.mkdir(parents=True, exist_ok=True)
    gt_dir.mkdir(parents=True, exist_ok=True)

    images = sorted(p for p in SRC_IMAGES.iterdir() if p.suffix.lower() in IMG_EXTS)
    if not images:
        print(f"[WARN] Không có ảnh trong {SRC_IMAGES}")
        return

    n_moved = n_new = n_skip = 0
    for src in images:
        dst_img = img_out / src.name
        # MOVE ảnh (nếu đã ở đích thì bỏ qua)
        if not dst_img.exists():
            shutil.move(str(src), str(dst_img))
            n_moved += 1

        gt_path = gt_dir / f"{src.stem}.json"
        if gt_path.exists() and not args.force:
            n_skip += 1
            continue

        record = OrderedDict([
            ("doc_name",   src.stem),
            ("lang",       "VN"),
            ("doc_type",   "id_card"),
            ("subtype",    "typed"),
            ("image_path", f"img/{src.name}"),
            ("fields",     OrderedDict((k, "") for k in FIELD_KEYS)),
        ])
        gt_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        n_new += 1

    print(f"Ảnh move sang img/: {n_moved}")
    print(f"JSON tạo mới: {n_new}, bỏ qua (đã có): {n_skip}")
    print(f"Output: {OUT_ROOT}")
    # Dọn folder images/ gốc nếu đã rỗng
    if SRC_IMAGES.exists() and not any(SRC_IMAGES.iterdir()):
        SRC_IMAGES.rmdir()
        print(f"Đã xóa folder rỗng: {SRC_IMAGES}")


if __name__ == "__main__":
    main()
