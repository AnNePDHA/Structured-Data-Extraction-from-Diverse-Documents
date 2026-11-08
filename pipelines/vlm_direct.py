"""VLM Direct pipeline: image → vision model → structured JSON.

The model backend is a ModelClient (Gemini or Azure), so any vision-capable
model works. Prompt template and field list come from external config
(see prompt_config).
"""

import json
import logging
import re
import time
from pathlib import Path
from typing import Callable

from PIL import Image

from .base import BasePipeline, ExtractionResult
from .model_clients import ModelClient
from .prompt_config import field_names, format_fields_schema, render_prompt

logger = logging.getLogger(__name__)


def _parse_json_response(text: str) -> dict:
    """Extract JSON object from model response, stripping markdown fences if present."""
    text = text.strip()
    # Strip ```json ... ``` or ``` ... ``` fences
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fenced:
        text = fenced.group(1).strip()
    # Find first {...} block
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        text = match.group(0)
    return json.loads(text)


class VLMDirectPipeline(BasePipeline):
    """Send a document image directly to a vision model and extract fields.

    Prompt template and field config are injected so they can be edited
    externally (config/prompts/vlm_direct.md, config/fields/<doctype>.json).
    The model backend is supplied as a ModelClient.
    """

    def __init__(
        self,
        client: ModelClient,
        prompt_template: str,
        field_config: dict,
    ):
        if not client.supports_vision:
            raise ValueError(
                f"Model {client.name!r} does not support vision; it cannot be used "
                "for the VLM-direct pipeline. Use the OCR-LLM pipeline instead."
            )
        super().__init__(client)
        self.prompt_template = prompt_template
        self.field_config = field_config
        self.fields = field_names(field_config)

    def extract(
        self, image_path: Path, on_stage: Callable[[str], None] | None = None
    ) -> ExtractionResult:
        """Extract fields from a document image via VLM.

        on_stage, if given, is called with "prepare", "model", "parse" as each
        stage starts. meta carries the rendered prompt, raw response and
        per-stage seconds.

        Returns:
            ExtractionResult with .fields (dict) and .usage (token counts).
        """
        notify = on_stage or (lambda _stage: None)
        timings = {}

        notify("prepare")
        t0 = time.perf_counter()
        # Load image into memory and close file handle (avoid Windows file locks)
        with Image.open(image_path) as img:
            img.load()
            image = img.copy()

        prompt = render_prompt(
            self.prompt_template,
            fields_schema=format_fields_schema(self.field_config),
            field_names_str=", ".join(self.fields),
        )
        timings["prepare"] = round(time.perf_counter() - t0, 3)

        notify("model")
        t0 = time.perf_counter()
        raw_text, usage = self._call_with_retry(
            self.client.generate, prompt, image=image
        )
        timings["model"] = round(time.perf_counter() - t0, 3)

        notify("parse")
        t0 = time.perf_counter()
        meta = {"prompt": prompt, "raw_response": raw_text, "stage_sec": timings}
        empty = {f: None for f in self.fields}
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

        # Keep only configured fields, coerce to str or None
        out_fields = {}
        for f in self.fields:
            val = parsed.get(f)
            out_fields[f] = str(val).strip() if val is not None else None
        timings["parse"] = round(time.perf_counter() - t0, 3)
        return ExtractionResult(fields=out_fields, usage=usage, meta=meta)
