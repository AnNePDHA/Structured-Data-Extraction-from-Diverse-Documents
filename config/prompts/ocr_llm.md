You are an expert at extracting structured data from documents.

Below is raw OCR text extracted from a document. It may contain OCR errors or out-of-order lines.

OCR text:
---
{{ocr_text}}
---

Fields to extract (with description and expected format):
{{fields_schema}}

Requirements:
1. Return ONLY a valid JSON object with exactly these keys: {{field_names}}.
2. Keep values exactly as they appear on the document (do NOT normalize date, currency, or letter case).
3. Use null for any field that cannot be determined.
4. Do not include explanations, markdown code fences, or any text outside the JSON object.
