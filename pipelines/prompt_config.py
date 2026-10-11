"""Load and render externalized prompt templates + field configs.

Config layout:
    config/
    ├── prompts/
    │   ├── vlm_direct.md   # uses {{fields_schema}}, {{field_names}}
    │   └── ocr_llm.md      # uses {{ocr_text}}, {{fields_schema}}, {{field_names}}
    └── fields/
        └── invoice.json    # {field: {description?, format?/unit?}}

Placeholders use double braces ({{name}}) and are filled via str.replace,
so JSON braces inside a template never collide with str.format.
"""

import json
from pathlib import Path


def load_field_config(path: Path) -> dict:
    """Load a field-config JSON. Keys are field names; values hold metadata."""
    with open(path, encoding="utf-8") as f:
        config = json.load(f)
    if not isinstance(config, dict) or not config:
        raise ValueError(f"Field config must be a non-empty object: {path}")
    return config


def load_prompt_template(path: Path) -> str:
    """Read a prompt template text file."""
    with open(path, encoding="utf-8") as f:
        return f.read()


def field_names(config: dict) -> list[str]:
    """Return the ordered list of field keys from a field config."""
    return list(config.keys())


def format_fields_schema(config: dict) -> str:
    """Render the field config into a readable bullet list for the prompt.

    Example output:
        - company: Name of the company or store issuing the invoice
        - date: Invoice date (format: keep the original format ...)
        - total: Total payable amount (unit: VND)

    Fields with no description/format still appear (key only), so the model
    is told to extract them.
    """
    lines = []
    for name, meta in config.items():
        if not isinstance(meta, dict):
            # Allow a plain string value as the description shorthand.
            meta = {"description": str(meta)} if meta else {}
        desc = meta.get("description", "").strip()
        # Support either "format" or "unit" as the qualifier note.
        qualifier = meta.get("format") or meta.get("unit")
        line = f"- {name}"
        if desc:
            line += f": {desc}"
        if qualifier:
            note_key = "unit" if "unit" in meta and not meta.get("format") else "format"
            line += f" ({note_key}: {qualifier})"
        lines.append(line)
    return "\n".join(lines)


def render_prompt(
    template: str,
    *,
    fields_schema: str,
    field_names_str: str,
    ocr_text: str | None = None,
) -> str:
    """Fill {{...}} placeholders in a prompt template.

    Replaces: {{fields_schema}}, {{field_names}}, and {{ocr_text}} (if provided).
    """
    out = template.replace("{{fields_schema}}", fields_schema)
    out = out.replace("{{field_names}}", field_names_str)
    if ocr_text is not None:
        out = out.replace("{{ocr_text}}", ocr_text)
    return out
