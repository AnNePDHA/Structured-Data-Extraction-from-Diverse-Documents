"""OCR engine implementations: pluggable backends for the OCR-LLM pipeline.

Currently exposes:
    - EasyOCREngine: local, free, supports 80+ languages incl. Vietnamese.
    - AzureDocIntelligenceEngine: cloud, Azure Document Intelligence prebuilt-read.
"""

import json
import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path

logger = logging.getLogger(__name__)


class OCREngine(ABC):
    """Abstract OCR engine. Subclass to plug into OCRLLMPipeline."""

    name: str = "abstract"

    @abstractmethod
    def extract_text(self, image_path: Path) -> str:
        """Run OCR on a single image and return concatenated text (line-separated)."""


# ---------------------------------------------------------------------------
# EasyOCR
# ---------------------------------------------------------------------------


class EasyOCREngine(OCREngine):
    """EasyOCR engine — simple, reliable, supports 80+ languages.

    Install:
        pip install easyocr

    First call downloads detection + recognition model weights (~110MB total)
    into ~/.EasyOCR/.
    """

    name = "easyocr"

    # Language code mapping: easyocr uses 2-letter codes ('en', 'vi', ...).
    # Pass any code easyocr supports; full list at:
    # https://www.jaided.ai/easyocr/

    def __init__(self, languages: list[str] | str = "en", gpu: bool = False):
        """Args:
            languages: One code (e.g. 'en') or list of codes (e.g. ['en', 'vi']).
                EasyOCR can run multiple languages simultaneously.
            gpu: True to use CUDA if available. False = CPU only (default,
                safer for portability).
        """
        if isinstance(languages, str):
            languages = [languages]
        self.languages = languages
        self.gpu = gpu
        self._reader = None  # Lazy init — model loading takes ~3-5s

    def _get_reader(self):
        if self._reader is not None:
            return self._reader
        try:
            import easyocr
        except ImportError:
            raise RuntimeError("easyocr not installed. Run: pip install easyocr")
        self._reader = easyocr.Reader(self.languages, gpu=self.gpu, verbose=False)
        return self._reader

    def extract_text(self, image_path: Path) -> str:
        reader = self._get_reader()
        # readtext returns list of (bbox, text, confidence).
        # detail=0 returns just the text strings — simpler.
        # paragraph=False keeps each detected box as a separate line.
        results = reader.readtext(str(image_path), detail=0, paragraph=False)
        if not results:
            return ""
        return "\n".join(str(t) for t in results).strip()


# ---------------------------------------------------------------------------
# Azure Document Intelligence
# ---------------------------------------------------------------------------


class AzureDocIntelligenceEngine(OCREngine):
    """Azure Document Intelligence OCR via the `prebuilt-read` model.

    Returns the document text in natural reading order (result.content).
    Requires the azure-ai-documentintelligence SDK and these env vars
    (or pass endpoint/key explicitly):
        AZURE_DOC_INTELLIGENCE_ENDPOINT
        AZURE_DOC_INTELLIGENCE_KEY

    Install:
        pip install azure-ai-documentintelligence
    """

    name = "azure_di"

    def __init__(
        self,
        endpoint: str | None = None,
        key: str | None = None,
        model_id: str = "prebuilt-read",
    ):
        self.endpoint = endpoint or os.getenv("AZURE_DOC_INTELLIGENCE_ENDPOINT")
        self.key = key or os.getenv("AZURE_DOC_INTELLIGENCE_KEY")
        self.model_id = model_id
        if not self.endpoint or not self.key:
            raise RuntimeError(
                "Azure Document Intelligence requires AZURE_DOC_INTELLIGENCE_ENDPOINT "
                "and AZURE_DOC_INTELLIGENCE_KEY (in .env or passed explicitly)."
            )
        self._client = None  # Lazy init

    def _get_client(self):
        if self._client is not None:
            return self._client
        try:
            from azure.ai.documentintelligence import DocumentIntelligenceClient
            from azure.core.credentials import AzureKeyCredential
        except ImportError:
            raise RuntimeError(
                "azure-ai-documentintelligence not installed. "
                "Run: pip install azure-ai-documentintelligence"
            )
        self._client = DocumentIntelligenceClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.key),
        )
        return self._client

    def extract_text(self, image_path: Path) -> str:
        client = self._get_client()
        with open(image_path, "rb") as f:
            poller = client.begin_analyze_document(
                self.model_id,
                body=f,
                content_type="application/octet-stream",
            )
        result = poller.result()
        return (getattr(result, "content", "") or "").strip()


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def build_engine(name: str = "easyocr", lang: str | None = None) -> OCREngine:
    """Construct an OCR engine by short name ('easyocr' or 'azure_di')."""
    name = name.lower()
    if name == "easyocr":
        return EasyOCREngine(languages=lang or "en")
    if name == "azure_di":
        return AzureDocIntelligenceEngine()
    raise ValueError(
        f"Unknown OCR engine: {name!r}. Supported: 'easyocr', 'azure_di'."
    )


OCR_CONFIG_PATH = Path(
    os.getenv(
        "OCR_ENGINES_CONFIG",
        Path(__file__).resolve().parent.parent / "config" / "ocr_engines.json",
    )
)


def load_ocr_registry(path: Path | None = None) -> dict[str, dict]:
    """Read config/ocr_engines.json (engine id → engine type, languages, env var names, price)."""
    with open(path or OCR_CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def build_ocr_engine(engine_id: str, entry: dict | None = None) -> OCREngine:
    """Construct an OCR engine from its config entry."""
    entry = entry or load_ocr_registry().get(engine_id)
    if entry is None:
        raise ValueError(f"Unknown OCR engine id: {engine_id!r}")
    engine = entry["engine"]
    if engine == "easyocr":
        return EasyOCREngine(
            languages=entry.get("languages", "en"), gpu=entry.get("gpu", False)
        )
    if engine == "azure_di":
        return AzureDocIntelligenceEngine(
            endpoint=os.getenv(entry.get("endpoint_env", "")),
            key=os.getenv(entry.get("key_env", "")),
            model_id=entry.get("model_id", "prebuilt-read"),
        )
    raise ValueError(f"Unhandled OCR engine type: {engine!r}")
