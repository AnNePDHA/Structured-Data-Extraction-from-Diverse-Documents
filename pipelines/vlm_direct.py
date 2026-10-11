"""VLM Direct pipeline: image → vision model → structured JSON.

The model backend is a ModelClient (Gemini or Azure), so any vision-capable
model works. Prompt template and field list come from external config
(see prompt_config).
"""

import json
import logging
import re
from pathlib import Path

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

    def extract(self, image_path: Path) -> ExtractionResult:
        """Extract fields from a document image via VLM.

        Returns:
            ExtractionResult with .fields (dict) and .usage (token counts).
        """
        # Load image into memory and close file handle (avoid Windows file locks)
        with Image.open(image_path) as img:
            img.load()
            image = img.copy()

        prompt = render_prompt(
            self.prompt_template,
            fields_schema=format_fields_schema(self.field_config),
            field_names_str=", ".join(self.fields),
        )

        raw_text, usage = self._call_with_retry(
            self.client.generate, prompt, image=image
        )

        empty = {f: None for f in self.fields}
        if raw_text is None:
            logger.warning(
                "Empty / blocked response for %s (finish_reason may be SAFETY)",
                image_path.name,
            )
            return ExtractionResult(fields=empty, usage=usage)

        try:
            parsed = _parse_json_response(raw_text)
        except json.JSONDecodeError as exc:
            logger.warning("Failed to parse JSON response: %s\nRaw: %s", exc, raw_text)
            return ExtractionResult(fields=empty, usage=usage)

        # Keep only configured fields, coerce to str or None
        out_fields = {}
        for f in self.fields:
            val = parsed.get(f)
            out_fields[f] = str(val).strip() if val is not None else None
        return ExtractionResult(fields=out_fields, usage=usage)
