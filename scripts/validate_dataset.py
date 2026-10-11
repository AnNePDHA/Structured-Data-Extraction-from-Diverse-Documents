# -*- coding: utf-8 -*-
"""
Audit toàn bộ entity files trong 1 dataset folder và in báo cáo thống kê.
Không ghi file, chỉ print.

Usage:
    python scripts/validate_dataset.py data/EN/Typed-Invoice
"""

import json
import re
import sys
from pathlib import Path
from collections import Counter


SLASHES_4Y  = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{4})$")
DASHES_4Y   = re.compile(r"^(\d{1,2})-(\d{1,2})-(\d{4})$")
SLASHES_2Y  = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{2})$")
DASHES_2Y   = re.compile(r"^(\d{1,2})-(\d{1,2})-(\d{2})$")
DOTS_MIX    = re.compile(r"^(\d{1,2})\.(\d{1,2})\.(\d{2,4})$")
SLASHES_YMD = re.compile(r"^(\d{4})/(\d{2})/(\d{2})$")
COMPACT8    = re.compile(r"^\d{8}$")
ISO_ALREADY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TEXT_MONTH  = re.compile(
    r"^\d{1,2}[\s\-/](JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[\s\-/]\d{2,4}$",
    re.IGNORECASE,
)
TEXT_MONTH2 = re.compile(
    r"^(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s+\d{1,2},?\s*\d{2,4}$",
    re.IGNORECASE,
)

# --- Currency prefix patterns ---
CURRENCY_PREFIX = re.compile(r"^\s*(\$|RM|S\$|MYR)\s*")


def detect_date_format(date_str: str) -> str:
    """Classify the apparent date format of a raw date string."""
    if not date_str:
        return "EMPTY"
    s = date_str.strip()
    if ISO_ALREADY.match(s):
        return "YYYY-MM-DD (ISO)"
    # Strip parentheses for further checks
    s_clean = s.lstrip("(").rstrip(")")
    if TEXT_MONTH.match(s_clean):
        return "DD-MMM-YYYY"
    if TEXT_MONTH2.match(s_clean):
        return "MMM-D-YYYY"
    if SLASHES_YMD.match(s_clean):
        return "YYYY/MM/DD"
    if COMPACT8.match(s_clean):
        return "COMPACT8"
    m = SLASHES_4Y.match(s_clean)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        if a > 12:
            return "DD/MM/YYYY"
        if b > 12:
            return "MM/DD/YYYY"
        return "DD/MM/YYYY (ambiguous)"
    if DASHES_4Y.match(s_clean):
        return "DD-MM-YYYY"
    m = SLASHES_2Y.match(s_clean)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        if a > 12:
            return "DD/MM/YY"
        if b > 12:
            return "MM/DD/YY"
        return "DD/MM/YY (ambiguous)"
    if DASHES_2Y.match(s_clean):
        return "DD-MM-YY"
    if DOTS_MIX.match(s_clean):
        return "DD.MM.YY"
    return "OTHER"


def detect_total_format(total_str: str) -> str:
    if total_str is None:
        return "MISSING_FIELD"
    if total_str == "":
        return "EMPTY"
    stripped = total_str.strip()
    m = CURRENCY_PREFIX.match(stripped)
    if m:
        return f"PREFIX_{m.group(1)}"
    if "," in stripped:
        return "COMMA_SEPARATOR"
    if stripped.lstrip("-").replace(".", "").isdigit():
        return "PLAIN_DECIMAL"
    return "OTHER"


def validate(dataset_dir: str):
    root = Path(dataset_dir)
    entities_dir = root / "entities"

    if not entities_dir.exists():
        print(f"[ERROR] Không tìm thấy thư mục entities/: {entities_dir}")
        sys.exit(1)

    files = sorted(entities_dir.glob("*.txt"))
    total = len(files)
    print(f"\n{'='*60}")
    print(f"Dataset: {root}")
    print(f"Tổng entity files: {total}")
    print(f"{'='*60}")

    date_fmt_counter   = Counter()
    total_fmt_counter  = Counter()
    problems = []

    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            problems.append((f.stem, f"JSON parse error: {e}"))
            continue

        date_val  = data.get("date", "")
        total_val = data.get("total", "")

        date_fmt  = detect_date_format(date_val)
        total_fmt = detect_total_format(total_val)

        date_fmt_counter[date_fmt]   += 1
        total_fmt_counter[total_fmt] += 1

        issues = []
        if date_fmt in ("EMPTY", "OTHER"):
            issues.append(f"date='{date_val}'")
        if total_fmt in ("EMPTY", "OTHER", "MISSING_FIELD"):
            issues.append(f"total='{total_val}'")
        if issues:
            problems.append((f.stem, ", ".join(issues)))

    # --- Date format distribution ---
    print("\n[Date formats]")
    for fmt, cnt in date_fmt_counter.most_common():
        bar = "█" * (cnt * 40 // total)
        print(f"  {fmt:<28} {cnt:>4}  {bar}")

    # --- Total format distribution ---
    print("\n[Total formats]")
    for fmt, cnt in total_fmt_counter.most_common():
        bar = "█" * (cnt * 40 // total)
        print(f"  {fmt:<28} {cnt:>4}  {bar}")

    # --- Problem records ---
    print(f"\n[Records có vấn đề] ({len(problems)} records)")
    if problems:
        for stem, desc in problems[:30]:
            print(f"  {stem}: {desc}")
        if len(problems) > 30:
            print(f"  ... và {len(problems) - 30} records khác")
    else:
        print("  (không có vấn đề)")

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/validate_dataset.py <dataset_dir>")
        sys.exit(1)
    validate(sys.argv[1])
