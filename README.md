# Structured Data Extraction from Diverse Documents: Benchmarking Vision-Language Models and OCR-LLM Pipelines

## Overview

This work compares two strategies for **Structured Data Extraction (SDE)** — turning a document image into a flat JSON object following a predefined schema — on a multilingual benchmark of invoices, citizen ID cards (CCCD), and contracts:

- **Pipeline A — VLM Direct:** image → Vision-Language Model → JSON (no intermediate OCR step).
- **Pipeline B — OCR-LLM:** image → OCR engine (EasyOCR / Azure Document Intelligence) → text-only LLM → JSON.

Each configuration is evaluated along **four dimensions**:

| Dimension | Metrics |
|---|---|
| Accuracy | Exact Match (EM), Token-F1 |
| Robustness | EM drop EN→VI, typed→handwritten |
| Efficiency | Latency (s/doc), Cost (USD / 1,000 docs) |
| Reliability | Hallucination rate, Schema-compliance rate |

A total of **540 extraction runs** were performed: 5 models × (the 4 vision-capable models on both pipelines + the text-only DeepSeek-V4 on OCR-LLM only) × 60 documents.

---

## Benchmark dataset

**60 samples** across **5 subsets** (each sample = one PNG image + one ground-truth JSON). Field values are kept **verbatim** as printed (dates, currency, casing are **not** normalized).

| Subset | Language | Doc type | Form | #Samples |
|---|---|---|---|---|
| `EN/Typed-Invoice` | EN | Invoice | Typed | 20 |
| `EN/Typed-Contract` | EN | Contract | Typed | 20 |
| `VN/Typed-IdCard` | VN | ID card | Typed | 10 |
| `VN/Typed-Contract` | VN | Contract | Typed | 5 |
| `VN/Handwritten-Contract` | VN | Contract | Handwritten | 5 |

**Sources:** SROIE (ICDAR 2019), Kaggle `invoice-receipt-contract-ocr`, Roboflow CCCD, and self-collected real-world Vietnamese banking documents.

---

## Models evaluated

| Model | Provider | Vision | Pipelines |
|---|---|---|---|
| GPT-5.2 | Azure OpenAI | ✅ | A + B |
| GPT-4o | Azure OpenAI | ✅ | A + B |
| Llama-4-Maverick (17B-128E, FP8) | Azure AI Foundry | ✅ | A + B |
| Phi-4-multimodal-instruct | Azure AI Foundry | ✅ | A + B |
| DeepSeek-V4-Flash | Azure AI Foundry | ❌ (text-only) | B only |

---

## Key results

| Model | Pipeline | EM | Token-F1 | Latency (s) | Cost (USD/1k) | Hallu. | Schema |
|---|---|---|---|---|---|---|---|
| Llama-4-Maverick | VLM Direct | **83.6%** | **92.3%** | **1.76** | 0.91 | 2.6% | 100% |
| GPT-4o | VLM Direct | 82.4% | 89.9% | 3.95 | 3.63 | 6.3% | 100% |
| GPT-5.2 | VLM Direct | 80.8% | 92.1% | 8.41 | 6.66 | **0.0%** | 100% |
| DeepSeek-V4 | OCR-LLM | 78.6% | 89.6% | 10.70 | 0.13 | 0.5% | 100% |
| GPT-4o | OCR-LLM | 77.0% | 86.6% | 7.93 | 2.45 | 2.6% | 100% |
| Llama-4-Maverick | OCR-LLM | 76.9% | 88.1% | 9.86 | 0.28 | 3.0% | 100% |
| Phi-4-MM | VLM Direct | 72.3% | 78.1% | 12.55 | 0.30 | 26.8% | 100% |
| GPT-5.2 | OCR-LLM | 72.1% | 88.2% | 11.09 | 5.24 | **0.0%** | 100% |
| Phi-4-MM | OCR-LLM | 70.2% | 82.9% | 11.80 | **0.08** | 3.9% | 98.3% |

**Takeaways:**
- **Best overall:** Llama-4-Maverick (VLM Direct) — highest accuracy, lowest latency, low cost.
- **Best on Vietnamese:** DeepSeek-V4 (OCR-LLM) — VI EM 82.0% > EN EM 77.0%, the most robust across languages.
- **Cheapest:** Phi-4-MM (OCR-LLM) — ~$0.08 per 1,000 documents.
- VLM Direct generally beats OCR-LLM on typed English documents and latency; OCR-LLM is preferable for Vietnamese, handwritten text, or when using text-only models.
- Cost figures cover **LLM/VLM token usage only** (pricing snapshot May 2026); they exclude per-page OCR fees (e.g. Azure Document Intelligence).

---

## Repository structure

```
.
├── README.md
├── 2470281_Report.pdf               # Full thesis (PDF, at repo root)
├── benchmark/                       # 60-sample dataset (images + ground-truth JSON)
│   ├── EN/Typed-Invoice/{img,ground_truth}/
│   ├── EN/Typed-Contract/{img,ground_truth}/
│   ├── VN/Typed-IdCard/{img,ground_truth}/
│   ├── VN/Typed-Contract/{img,ground_truth}/
│   └── VN/Handwritten-Contract/{img,ground_truth}/
├── config/                          # Field schemas & prompt templates (for reproducibility)
│   ├── fields/*.json
│   └── prompts/*.md
├── results/
│   ├── summary_table.csv            # Leaderboard (all 4 dimensions)
│   ├── accuracy_table.csv
│   ├── <model>/                     # Raw per-document JSON outputs per model & pipeline
│   └── figures/                     # Result charts (PNG/PDF) + metric CSVs
└── figures/
    ├── architecture/                # System/pipeline diagrams, UI mockups
    └── eda/                         # Dataset exploratory-analysis charts
```

---
