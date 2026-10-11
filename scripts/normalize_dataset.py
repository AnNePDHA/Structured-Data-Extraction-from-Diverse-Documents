# -*- coding: utf-8 -*-
"""
Chọn N mẫu ngẫu nhiên từ dataset folder, copy ảnh và ghi ground truth ra data-processed/.
Mỗi mẫu là 1 file JSON riêng trong ground_truth/, ảnh nằm trong img/.
Giữ nguyên giá trị từ entities (không normalize) — đây là ground truth để benchmark.

Output structure:
    data-processed/{LANG}/{SUBTYPE}-{DOCTYPE}/
    ├── img/               ← ảnh đã copy
    └── ground_truth/      ← 1 file .json per image

Usage:
    python scripts/normalize_dataset.py \\
        --dataset data/EN/Typed-Invoice \\
        --lang EN --doc-type invoice --subtype typed \\
        --sample 20
"""

import argparse
import json
import random
import shutil
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Build ground_truth/ from entity files")
    parser.add_argument("--dataset",  required=True, help="Path đến dataset folder (nguồn)")
    parser.add_argument("--lang",     required=True, choices=["EN", "VI"])
    parser.add_argument("--doc-type", required=True, choices=["invoice", "id_card", "contract", "form"])
    parser.add_argument("--subtype",  required=True, choices=["typed", "handwritten"])
    parser.add_argument("--sample",   type=int, default=20, help="Số mẫu lấy (default: 20, 0 = lấy tất cả)")
    parser.add_argument("--seed",     type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)

    dataset_root = Path(args.dataset).resolve()
    entities_dir = dataset_root / "entities"
    src_img_dir  = dataset_root / "img"

    if not entities_dir.exists():
        print(f"[ERROR] Không tìm thấy: {entities_dir}")
        return

    all_files = sorted(entities_dir.glob("*.txt"))
    print(f"Tổng files: {len(all_files)}")

    selected = all_files if args.sample == 0 else random.sample(all_files, min(args.sample, len(all_files)))
    selected = sorted(selected)
    print(f"Chọn: {len(selected)} mẫu")

    # Output: data-processed/{lang}/{subtype}-{doc_type}/
    project_root = dataset_root.parent.parent.parent  # data/EN/Typed-Invoice → project root
    folder_name  = f"{args.subtype.capitalize()}-{args.doc_type.capitalize()}"
    out_root     = project_root / "data-processed" / args.lang / folder_name
    gt_dir       = out_root / "ground_truth"
    img_out_dir  = out_root / "img"
    gt_dir.mkdir(parents=True, exist_ok=True)
    img_out_dir.mkdir(parents=True, exist_ok=True)

    copied_img = 0
    for f in selected:
        data = json.loads(f.read_text(encoding="utf-8"))

        record = {
            "doc_name":  f.stem,
            "lang":      args.lang,
            "doc_type":  args.doc_type,
            "subtype":   args.subtype,
            "image_path": f"img/{f.stem}.jpg",
            "fields":    data,
        }

        (gt_dir / (f.stem + ".json")).write_text(
            json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        src_img = src_img_dir / (f.stem + ".jpg")
        if src_img.exists():
            shutil.copy(src_img, img_out_dir / src_img.name)
            copied_img += 1

    print(f"Đã ghi {len(selected)} JSON → {gt_dir}")
    print(f"Đã copy {copied_img} ảnh   → {img_out_dir}")


if __name__ == "__main__":
    main()
