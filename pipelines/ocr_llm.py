"""OCR-LLM pipeline: image → OCR engine → LLM text → structured JSON.

OCR engine is pluggable: pass any OCREngine subclass (default EasyOCR).
LLM backend is a ModelClient (Gemini or Azure).
"""

import json
import logging
import re
import time
from pathlib import Path
from typing import Callable

from .base import BasePipeline, ExtractionResult
from .model_clients import ModelClient
from .ocr_engines import EasyOCREngine, OCREngine
from .prompt_config import field_names, format_fields_schema, render_prompt

logger = logging.getLogger(__name__)


def _parse_json_response(text: str) -> dict:
    """Extract JSON object from model response, stripping markdown fences if present."""
    text = text.strip()
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fenced:
        text = fenced.group(1).strip()
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        text = match.group(0)
    return json.loads(text)


class OCRLLMPipeline(BasePipeline):
    """Run a pluggable OCR engine on the image, then send OCR text to Gemini.

    The OCR engine is injected via constructor (default EasyOCR) so we
    can swap implementations without changing this class.
    """

    def __init__(
        self,
        client: ModelClient,
        prompt_template: str,
        field_config: dict,
        ocr_engine: OCREngine | None = None,
    ):
        super().__init__(client)
        self.prompt_template = prompt_template
        self.field_config = field_config
        self.fields = field_names(field_config)
        self.ocr_engine = ocr_engine or EasyOCREngine()

    def _run_ocr(self, image_path: Path) -> str:
        """Delegate OCR to the injected engine."""
        return self.ocr_engine.extract_text(image_path)

    def extract(
        self, image_path: Path, on_stage: Callable[[str], None] | None = None
    ) -> ExtractionResult:
        """Extract fields using OCR → LLM pipeline.

        on_stage, if given, is called with "ocr", "model", "parse" as each
        stage starts.

        Returns:
            ExtractionResult with .fields, .usage (LLM tokens), and .meta
            (OCR character count, OCR text, rendered prompt, raw response,
            per-stage seconds).
        """
        notify = on_stage or (lambda _stage: None)
        timings = {}

        notify("ocr")
        t0 = time.perf_counter()
        ocr_text = self._run_ocr(image_path)
        timings["ocr"] = round(time.perf_counter() - t0, 3)
        meta = {
            "ocr_chars": len(ocr_text),
            "ocr_engine": self.ocr_engine.name,
            "ocr_text": ocr_text,
            "stage_sec": timings,
        }

        empty = {f: None for f in self.fields}
        if not ocr_text:
            logger.warning("OCR engine returned empty text for %s", image_path.name)
            return ExtractionResult(fields=empty, usage=None, meta=meta)

        prompt = render_prompt(
            self.prompt_template,
            fields_schema=format_fields_schema(self.field_config),
            field_names_str=", ".join(self.fields),
            ocr_text=ocr_text,
        )
        meta["prompt"] = prompt

        notify("model")
        t0 = time.perf_counter()
        raw_text, usage = self._call_with_retry(self.client.generate, prompt)
        timings["model"] = round(time.perf_counter() - t0, 3)
        meta["raw_response"] = raw_text

        notify("parse")
        if raw_text is None:
            logger.warning(
                "Empty / blocked response for %s (finish_reason may be SAFETY)",
                image_path.name,
            )
            return ExtractionResult(fields=empty, usage=usage, meta=meta)

        try:
            parsed = _parse_json_response(raw_text)
        except json.JSONDecodeError as exc:
            logger.warning("Failed to parse JSON response: %s\nRaw: %s", exc, raw_text)
            return ExtractionResult(fields=empty, usage=usage, meta=meta)

        out_fields = {}
        for f in self.fields:
            val = parsed.get(f)
            out_fields[f] = str(val).strip() if val is not None else None
        return ExtractionResult(fields=out_fields, usage=usage, meta=meta)
