# -*- coding: utf-8 -*-
"""
Generate EDA figures for the benchmark dataset.
Output: notebooks/figures/fig1_*.png ... fig8_*.png
"""

import json
import numpy as np
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR     = PROJECT_ROOT / "data-processed"
FIG_DIR      = PROJECT_ROOT / "notebooks" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "figure.dpi": 150,
    "savefig.dpi": 150,
    "font.family": "DejaVu Sans",
    "axes.spines.top": False,
    "axes.spines.right": False,
})
PALETTE = {
    "EN": "#4C72B0", "VN": "#DD8452",
    "typed": "#4C72B0", "handwritten": "#C44E52",
    "invoice": "#4C72B0", "contract": "#DD8452",
    "id_card": "#55A868", "custom": "#8172B2",
}


def is_filled(v) -> bool:
    if isinstance(v, dict):
        return any(str(vv).strip() not in ("", "null", "None") for vv in v.values())
    return str(v).strip() not in ("", "null", "None")


def save(name: str):
    path = FIG_DIR / f"{name}.png"
    plt.savefig(path, bbox_inches="tight")
    print(f"Saved -> {path}")
    plt.close()


# ── Load data ──────────────────────────────────────────────────────────────
rows = []
for jf in sorted(DATA_DIR.rglob("ground_truth/*.json")):
    with open(jf, encoding="utf-8") as f:
        d = json.load(f)
    dataset  = jf.parent.parent.name
    fields   = d.get("fields", {})
    n_fields = len(fields)
    n_filled = sum(1 for v in fields.values() if is_filled(v))
    rows.append({
        "doc_name":     d["doc_name"],
        "lang":         d["lang"],
        "doc_type":     d["doc_type"],
        "subtype":      d["subtype"],
        "dataset":      dataset,
        "n_fields":     n_fields,
        "n_filled":     n_filled,
        "completeness": round(n_filled / n_fields * 100, 1) if n_fields else 0,
        "status":       "filled" if n_filled == n_fields else ("partial" if n_filled > 0 else "blank"),
    })

df = pd.DataFrame(rows)
print(f"Loaded {len(df)} records")


# ── Fig 1: Samples per Dataset (stacked by lang) ───────────────────────────
order = df.groupby("dataset").size().sort_values(ascending=False).index.tolist()
dataset_lang = df.groupby(["dataset", "lang"]).size().reset_index(name="count")

fig, ax = plt.subplots(figsize=(9, 4))
bottom = {d: 0 for d in order}
for lang, grp in dataset_lang.groupby("lang"):
    vals = [grp.set_index("dataset")["count"].get(d, 0) for d in order]
    ax.bar(order, vals, bottom=[bottom[d] for d in order],
           label=lang, color=PALETTE[lang], edgecolor="white", linewidth=0.5)
    for i, (d, v) in enumerate(zip(order, vals)):
        if v > 0:
            ax.text(i, bottom[d] + v / 2, str(v), ha="center", va="center",
                    fontsize=10, color="white", fontweight="bold")
        bottom[d] += v
ax.set_xlabel("Dataset")
ax.set_ylabel("Number of samples")
ax.set_title("Samples per Dataset (coloured by Language)", fontsize=13, pad=10)
ax.legend(title="Language")
plt.tight_layout()
save("fig1_samples_per_dataset")


# ── Fig 2: Language pie ────────────────────────────────────────────────────
lang_counts = df["lang"].value_counts()
fig, ax = plt.subplots(figsize=(5, 5))
wedges, texts, autotexts = ax.pie(
    lang_counts, labels=lang_counts.index,
    autopct="%1.1f%%",
    colors=[PALETTE[l] for l in lang_counts.index],
    startangle=140,
    wedgeprops=dict(edgecolor="white", linewidth=2),
)
for at in autotexts:
    at.set_fontsize(12)
    at.set_color("white")
    at.set_fontweight("bold")
ax.set_title("Language Distribution", fontsize=13, pad=12)
ax.legend(
    [f"{l} ({c} samples)" for l, c in lang_counts.items()],
    loc="lower right", fontsize=10,
)
plt.tight_layout()
save("fig2_language_distribution")


# ── Fig 3: Doc type horizontal bar ────────────────────────────────────────
dtype_counts = df["doc_type"].value_counts()
fig, ax = plt.subplots(figsize=(6, 4))
bars = ax.barh(dtype_counts.index, dtype_counts.values,
               color=[PALETTE[t] for t in dtype_counts.index], edgecolor="white")
for bar, val in zip(bars, dtype_counts.values):
    ax.text(val + 0.3, bar.get_y() + bar.get_height() / 2, str(val), va="center", fontsize=11)
ax.set_xlabel("Number of samples")
ax.set_title("Document Type Distribution", fontsize=13, pad=10)
ax.set_xlim(0, dtype_counts.max() + 4)
plt.tight_layout()
save("fig3_doctype_distribution")


# ── Fig 4: Subtype bar ────────────────────────────────────────────────────
subtype_counts = df["subtype"].value_counts()
fig, ax = plt.subplots(figsize=(5, 4))
bars = ax.bar(subtype_counts.index, subtype_counts.values,
              color=[PALETTE[s] for s in subtype_counts.index],
              edgecolor="white", width=0.5)
for bar, val in zip(bars, subtype_counts.values):
    ax.text(bar.get_x() + bar.get_width() / 2, val + 0.3, str(val),
            ha="center", fontsize=12, fontweight="bold")
ax.set_ylabel("Number of samples")
ax.set_title("Subtype: Typed vs Handwritten", fontsize=13, pad=10)
ax.set_ylim(0, subtype_counts.max() + 5)
plt.tight_layout()
save("fig4_subtype_distribution")


# ── Fig 5: GT Completeness stacked bar ────────────────────────────────────
STATUS_COLORS = {"filled": "#55A868", "partial": "#DD8452", "blank": "#C44E52"}
status_order  = ["filled", "partial", "blank"]
pivot = (
    df.groupby(["dataset", "status"])
    .size()
    .unstack(fill_value=0)
    .reindex(columns=status_order, fill_value=0)
)
pivot = pivot.loc[df.groupby("dataset").size().sort_values(ascending=False).index]

fig, ax = plt.subplots(figsize=(9, 4))
bottom = np.zeros(len(pivot))
for status in status_order:
    vals = pivot[status].values
    ax.bar(pivot.index, vals, bottom=bottom,
           label=status.capitalize(), color=STATUS_COLORS[status],
           edgecolor="white", linewidth=0.5)
    for i, v in enumerate(vals):
        if v > 0:
            ax.text(i, bottom[i] + v / 2, str(v), ha="center", va="center",
                    fontsize=10, color="white", fontweight="bold")
    bottom += vals
ax.set_ylabel("Number of samples")
ax.set_title("Ground Truth Completeness per Dataset", fontsize=13, pad=10)
ax.legend(title="GT Status", loc="upper right")
plt.tight_layout()
save("fig5_gt_completeness")


# ── Fig 6: Field fill rate heatmap ────────────────────────────────────────
field_rows = []
for jf in sorted(DATA_DIR.rglob("ground_truth/*.json")):
    with open(jf, encoding="utf-8") as f:
        d = json.load(f)
    for field, val in d.get("fields", {}).items():
        field_rows.append({
            "doc_type": d["doc_type"],
            "field":    field,
            "filled":   int(is_filled(val)),
        })
fdf = pd.DataFrame(field_rows)
pivot_f = (
    fdf.groupby(["doc_type", "field"])["filled"]
    .mean()
    .mul(100)
    .unstack("field")
    .fillna(np.nan)
)
pivot_f = pivot_f.reindex(
    [r for r in ["invoice", "contract", "id_card", "custom"] if r in pivot_f.index]
)

fig, ax = plt.subplots(figsize=(14, 3.5))
sns.heatmap(
    pivot_f, ax=ax, annot=True, fmt=".0f", cmap="RdYlGn",
    vmin=0, vmax=100, linewidths=0.5, linecolor="white",
    cbar_kws={"label": "% Filled"}, mask=pivot_f.isna(),
)
ax.set_title("Field Fill Rate (%) per Document Type", fontsize=13, pad=10)
ax.set_ylabel("doc_type")
ax.set_xlabel("Field")
plt.xticks(rotation=35, ha="right", fontsize=8)
plt.tight_layout()
save("fig6_field_fill_rate")


# ── Fig 7: Lang x DocType grouped bar ─────────────────────────────────────
cross = df.groupby(["lang", "doc_type"]).size().unstack(fill_value=0)
doc_type_order = [c for c in ["invoice", "contract", "id_card", "custom"] if c in cross.columns]
cross = cross.reindex(columns=doc_type_order)

fig, ax = plt.subplots(figsize=(7, 3.5))
x = np.arange(len(cross.columns))
width = 0.35
for i, (lang, row) in enumerate(cross.iterrows()):
    offset = (i - 0.5) * width
    bars = ax.bar(x + offset, row.values, width,
                  label=lang, color=PALETTE[lang], edgecolor="white")
    for bar, val in zip(bars, row.values):
        if val > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.2,
                    str(val), ha="center", va="bottom", fontsize=10)
ax.set_xticks(x)
ax.set_xticklabels(cross.columns)
ax.set_ylabel("Number of samples")
ax.set_title("Language x Document Type", fontsize=13, pad=10)
ax.legend(title="Language")
ax.set_ylim(0, cross.values.max() + 4)
plt.tight_layout()
save("fig7_lang_x_doctype")


# ── Fig 8: Dataset overview horizontal bar ────────────────────────────────
dataset_info = (
    df.groupby(["dataset", "lang", "doc_type", "subtype"])
    .size()
    .reset_index(name="samples")
)
dataset_info["label"] = dataset_info.apply(
    lambda r: f"{r['dataset']}  ({r['lang']} · {r['doc_type']} · {r['subtype']})",
    axis=1,
)
dataset_info = dataset_info.sort_values("samples", ascending=True)

fig, ax = plt.subplots(figsize=(9, 5.5))
colors = [PALETTE[r["lang"]] for _, r in dataset_info.iterrows()]
bars = ax.barh(dataset_info["label"], dataset_info["samples"],
               color=colors, edgecolor="white", height=0.6)
for bar, val in zip(bars, dataset_info["samples"]):
    ax.text(val + 0.1, bar.get_y() + bar.get_height() / 2, str(val), va="center", fontsize=10)
patches = [mpatches.Patch(color=PALETTE[l], label=l) for l in ["EN", "VN"]]
ax.legend(handles=patches, title="Language", loc="lower right")
ax.set_xlabel("Number of samples")
ax.set_title("Dataset Overview — All 6 Subsets", fontsize=13, pad=10)
ax.set_xlim(0, dataset_info["samples"].max() + 4)
plt.tight_layout()
save("fig8_dataset_overview")

print("\nAll 8 figures generated successfully.")
