"""Model client abstraction: one interface over Gemini + Azure backends.

A ``ModelClient`` hides provider differences behind a single ``generate``
method that takes a text prompt and (optionally) an image, and returns the raw
response text plus a normalized usage dict. Pipelines (vlm_direct, ocr_llm)
depend only on this interface, so swapping Gemini ↔ Azure is a config change.

Providers
---------
- gemini        : google-generativeai (gemini-*, gemma-*)
- azure_openai  : openai.AzureOpenAI chat.completions (gpt-4o, gpt-5-chat, gpt-5.2-chat)
- azure_foundry : azure-ai-inference ChatCompletionsClient
                  (Phi-4-multimodal-instruct, Llama-4-Maverick-...)
- openai_compatible : openai.OpenAI with a custom base_url (OpenRouter, Groq, vLLM, ...)

Credentials/endpoints live in environment variables (see .env.example);
the model list, provider, pricing and env var names live in config/models.json.
"""

import base64
import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Usage normalization
# ---------------------------------------------------------------------------


def _usage_dict(
    prompt_tokens=None,
    completion_tokens=None,
    thinking_tokens=None,
    total_tokens=None,
) -> dict:
    """Normalized token-usage dict shared across providers.

    ``thinking_tokens`` is Gemini-only (internal reasoning); Azure leaves it None.
    Shape matches what scripts/run_benchmark.py::_usage_stats expects.
    """
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "thinking_tokens": thinking_tokens,
        "total_tokens": total_tokens,
    }


def _image_to_data_uri(image: Image.Image) -> str:
    """Encode a PIL image as a base64 PNG data URI (for OpenAI/Foundry vision)."""
    import io

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------


class ModelClient(ABC):
    """Provider-agnostic chat/vision client.

    Attributes:
        name: Model name as the user types it (recorded in benchmark results).
        provider: "gemini" | "azure_openai" | "azure_foundry".
        supports_vision: True if the model accepts images.
        min_interval_sec: Minimum spacing between calls (pacing). Free-tier
            Gemini needs ~13s; paid Azure can run back-to-back (0.0).
    """

    name: str
    provider: str
    supports_vision: bool = True
    min_interval_sec: float = 0.0

    @abstractmethod
    def generate(
        self, prompt: str, image: Image.Image | None = None
    ) -> tuple[str | None, dict | None]:
        """Run one generation.

        Args:
            prompt: Text prompt.
            image: Optional PIL image (vision). Ignored by text-only callers.

        Returns:
            (raw_text, usage_dict). raw_text is None if the response was empty
            or blocked; usage_dict is None if the provider returned no usage.
        """


# ---------------------------------------------------------------------------
# Gemini
# ---------------------------------------------------------------------------


def _gemini_extract_usage(response) -> dict | None:
    """Pull token counts from a google-generativeai response.usage_metadata.

    For Gemini 2.5+ with reasoning, total may exceed prompt+completion because
    internal "thinking" tokens are counted; thinking_tokens exposes that delta.
    """
    um = getattr(response, "usage_metadata", None)
    if um is None:
        return None
    return _usage_dict(
        prompt_tokens=getattr(um, "prompt_token_count", None),
        completion_tokens=getattr(um, "candidates_token_count", None),
        thinking_tokens=getattr(um, "thoughts_token_count", None),
        total_tokens=getattr(um, "total_token_count", None),
    )


def _gemini_safe_text(response) -> str | None:
    """Safely extract text from a google-generativeai response.

    Accessing response.text raises ValueError when the response is empty,
    blocked by safety filters, or has no valid Part. Returns None instead.
    """
    try:
        candidates = getattr(response, "candidates", None) or []
        if not candidates:
            return None
        parts = getattr(candidates[0].content, "parts", None) or []
        text = "".join(getattr(p, "text", "") or "" for p in parts)
        return text or None
    except Exception as exc:
        logger.warning("Could not extract text from Gemini response: %s", exc)
        return None


class GeminiClient(ModelClient):
    """Google Gemini via google-generativeai. Vision + text, temperature=0."""

    provider = "gemini"

    def __init__(self, model: str, api_key: str, min_interval_sec: float = 13.0):
        import google.generativeai as genai

        self.name = model
        self.supports_vision = True
        self.min_interval_sec = min_interval_sec
        self._genai = genai
        genai.configure(api_key=api_key)
        self._client = genai.GenerativeModel(
            model_name=model,
            generation_config=genai.types.GenerationConfig(
                temperature=0,
                response_mime_type="text/plain",
            ),
        )

    def generate(
        self, prompt: str, image: Image.Image | None = None
    ) -> tuple[str | None, dict | None]:
        contents = [image, prompt] if image is not None else prompt
        response = self._client.generate_content(contents)
        return _gemini_safe_text(response), _gemini_extract_usage(response)


# ---------------------------------------------------------------------------
# Azure OpenAI (gpt-4o, gpt-5-chat, gpt-5.2-chat)
# ---------------------------------------------------------------------------


class AzureOpenAIClient(ModelClient):
    """Azure OpenAI chat.completions. Vision via base64 image_url data URI."""

    provider = "azure_openai"

    def __init__(
        self,
        model: str,
        endpoint: str,
        api_key: str,
        api_version: str,
        deployment: str | None = None,
        min_interval_sec: float = 0.0,
        temperature: float | None = 0.0,
    ):
        from openai import AzureOpenAI

        self.name = model
        self.deployment = deployment or model
        self.supports_vision = True
        self.min_interval_sec = min_interval_sec
        # Some models (e.g. gpt-5-chat, gpt-5.2-chat) only accept the default
        # temperature; passing 0 → HTTP 400. Set temperature=None to omit it.
        self.temperature = temperature
        self._client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
        )

    def generate(
        self, prompt: str, image: Image.Image | None = None
    ) -> tuple[str | None, dict | None]:
        if image is not None:
            content = [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": _image_to_data_uri(image)}},
            ]
        else:
            content = prompt
        kwargs = {}
        if self.temperature is not None:
            kwargs["temperature"] = self.temperature
        response = self._client.chat.completions.create(
            model=self.deployment,
            messages=[{"role": "user", "content": content}],
            **kwargs,
        )
        text = response.choices[0].message.content if response.choices else None
        usage = None
        if getattr(response, "usage", None) is not None:
            u = response.usage
            usage = _usage_dict(
                prompt_tokens=getattr(u, "prompt_tokens", None),
                completion_tokens=getattr(u, "completion_tokens", None),
                total_tokens=getattr(u, "total_tokens", None),
            )
        return (text or None), usage


# ---------------------------------------------------------------------------
# Azure AI Foundry (Phi-4-multimodal, Llama-4-Maverick) via azure-ai-inference
# ---------------------------------------------------------------------------


class AzureFoundryClient(ModelClient):
    """Azure AI Foundry serverless models via azure-ai-inference.

    Endpoint points at the resource's `/models` route; the concrete model is
    selected with the ``model`` request parameter. Vision uses ImageContentItem.
    """

    provider = "azure_foundry"

    def __init__(
        self,
        model: str,
        endpoint: str,
        api_key: str,
        supports_vision: bool = True,
        min_interval_sec: float = 0.0,
    ):
        from azure.ai.inference import ChatCompletionsClient
        from azure.core.credentials import AzureKeyCredential

        self.name = model
        self.supports_vision = supports_vision
        self.min_interval_sec = min_interval_sec
        self._client = ChatCompletionsClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(api_key),
        )

    def generate(
        self, prompt: str, image: Image.Image | None = None
    ) -> tuple[str | None, dict | None]:
        from azure.ai.inference.models import (
            ImageContentItem,
            ImageUrl,
            TextContentItem,
            UserMessage,
        )

        if image is not None:
            message = UserMessage(
                content=[
                    TextContentItem(text=prompt),
                    ImageContentItem(
                        image_url=ImageUrl(url=_image_to_data_uri(image))
                    ),
                ]
            )
        else:
            message = UserMessage(content=prompt)

        response = self._client.complete(
            messages=[message],
            model=self.name,
            temperature=0,
        )
        text = response.choices[0].message.content if response.choices else None
        usage = None
        if getattr(response, "usage", None) is not None:
            u = response.usage
            usage = _usage_dict(
                prompt_tokens=getattr(u, "prompt_tokens", None),
                completion_tokens=getattr(u, "completion_tokens", None),
                total_tokens=getattr(u, "total_tokens", None),
            )
        return (text or None), usage


# ---------------------------------------------------------------------------
# OpenAI-compatible endpoints (OpenRouter, Groq, vLLM, ...)
# ---------------------------------------------------------------------------


class OpenAICompatibleClient(ModelClient):
    """Any endpoint that speaks the OpenAI chat.completions protocol."""

    provider = "openai_compatible"

    def __init__(
        self,
        model: str,
        base_url: str,
        api_key: str,
        supports_vision: bool = False,
        min_interval_sec: float = 0.0,
        temperature: float | None = 0.0,
    ):
        from openai import OpenAI

        self.name = model
        self.supports_vision = supports_vision
        self.min_interval_sec = min_interval_sec
        self.temperature = temperature
        self._client = OpenAI(base_url=base_url, api_key=api_key)

    def generate(
        self, prompt: str, image: Image.Image | None = None
    ) -> tuple[str | None, dict | None]:
        if image is not None:
            content = [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": _image_to_data_uri(image)}},
            ]
        else:
            content = prompt
        kwargs = {}
        if self.temperature is not None:
            kwargs["temperature"] = self.temperature
        response = self._client.chat.completions.create(
            model=self.name,
            messages=[{"role": "user", "content": content}],
            **kwargs,
        )
        text = response.choices[0].message.content if response.choices else None
        usage = None
        if getattr(response, "usage", None) is not None:
            u = response.usage
            usage = _usage_dict(
                prompt_tokens=getattr(u, "prompt_tokens", None),
                completion_tokens=getattr(u, "completion_tokens", None),
                total_tokens=getattr(u, "total_tokens", None),
            )
        return (text or None), usage


# ---------------------------------------------------------------------------
# Registry + factory
# ---------------------------------------------------------------------------

PROVIDERS = ("azure_openai", "azure_foundry", "openai_compatible", "gemini")

MODELS_CONFIG_PATH = Path(
    os.getenv(
        "MODELS_CONFIG",
        Path(__file__).resolve().parent.parent / "config" / "models.json",
    )
)


def load_model_registry(path: Path | None = None) -> dict[str, dict]:
    """Read config/models.json on every call so edits from the web app apply at once.

    Each entry: provider, supports_vision, fixed_temperature?, price_per_1m?,
    endpoint_env / endpoint, key_env, api_version_env (azure_openai),
    deployment? (azure_openai), min_interval_sec?.
    "fixed_temperature": true → model only accepts its default temperature;
    we must NOT send temperature=0 (gpt-5 family returns HTTP 400 otherwise).
    """
    with open(path or MODELS_CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def _require_env(*names: str) -> list[str]:
    """Return the values of the named env vars, or raise listing the missing ones."""
    values = [os.getenv(n) for n in names]
    missing = [n for n, v in zip(names, values) if not v]
    if missing:
        raise RuntimeError(
            "Missing required environment variable(s): "
            + ", ".join(missing)
            + ". Copy .env.example to .env and fill them in."
        )
    return values


def _is_gemini_name(model_name: str) -> bool:
    return model_name.startswith(("gemini", "gemma", "models/gemini", "models/gemma"))


def get_model_entry(model_name: str) -> dict:
    """Return the config entry for a model; gemini-*/gemma-* fall back to GOOGLE_API_KEY."""
    registry = load_model_registry()
    entry = registry.get(model_name)
    if entry:
        return entry
    if _is_gemini_name(model_name):
        return {"provider": "gemini", "supports_vision": True, "key_env": "GOOGLE_API_KEY"}
    raise ValueError(
        f"Unknown model {model_name!r}. Models in {MODELS_CONFIG_PATH.name}: "
        + ", ".join(registry)
        + "; or any gemini-*/gemma-* model."
    )


def resolve_provider(model_name: str) -> str:
    """Return the provider id for a model name."""
    return get_model_entry(model_name)["provider"]


def required_env(entry: dict) -> list[str]:
    """Env var names a model entry needs at call time."""
    names = [entry.get("key_env")]
    if not entry.get("endpoint"):
        names.append(entry.get("endpoint_env"))
    if entry.get("provider") == "azure_openai":
        names.append(entry.get("api_version_env"))
    if entry.get("provider") == "gemini":
        names = [entry.get("key_env")]
    return [n for n in names if n]


def build_client(model_name: str, entry: dict | None = None) -> ModelClient:
    """Construct the right ModelClient for a model name, reading creds from env.

    Raises RuntimeError if the provider's required env vars are unset, and
    ValueError if the model name is unrecognized.
    """
    entry = entry or get_model_entry(model_name)
    provider = entry["provider"]
    supports_vision = entry.get("supports_vision", False)
    min_interval = float(entry.get("min_interval_sec", 0.0))
    # gpt-5 family rejects temperature override → omit it (temperature=None).
    temperature = None if entry.get("fixed_temperature") else 0.0

    def endpoint() -> str:
        if entry.get("endpoint"):
            return entry["endpoint"]
        return _require_env(entry["endpoint_env"])[0]

    if provider == "gemini":
        (key,) = _require_env(entry.get("key_env", "GOOGLE_API_KEY"))
        return GeminiClient(
            model=model_name, api_key=key, min_interval_sec=min_interval or 13.0
        )

    if provider == "azure_openai":
        key, api_version = _require_env(entry["key_env"], entry["api_version_env"])
        return AzureOpenAIClient(
            model=model_name,
            endpoint=endpoint(),
            api_key=key,
            api_version=api_version,
            deployment=entry.get("deployment"),
            min_interval_sec=min_interval,
            temperature=temperature,
        )

    if provider == "azure_foundry":
        (key,) = _require_env(entry["key_env"])
        return AzureFoundryClient(
            model=model_name,
            endpoint=endpoint(),
            api_key=key,
            supports_vision=supports_vision,
            min_interval_sec=min_interval,
        )

    if provider == "openai_compatible":
        (key,) = _require_env(entry["key_env"])
        return OpenAICompatibleClient(
            model=model_name,
            base_url=endpoint(),
            api_key=key,
            supports_vision=supports_vision,
            min_interval_sec=min_interval,
            temperature=temperature,
        )

    raise ValueError(f"Unhandled provider: {provider!r}")
