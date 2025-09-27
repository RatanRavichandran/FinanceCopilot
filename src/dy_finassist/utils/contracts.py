from __future__ import annotations

import io
import re
from functools import lru_cache
from typing import Iterable, Optional

import pdfplumber

try:  # Optional dependencies
    from presidio_analyzer import AnalyzerEngine  # type: ignore
    from presidio_anonymizer import AnonymizerEngine  # type: ignore
except ImportError:  # pragma: no cover - optional
    AnalyzerEngine = AnonymizerEngine = None  # type: ignore


def _normalise_whitespace(text: str) -> str:
    text = re.sub(r"(?<!\.)\n", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_text_from_pdf(file_like: io.BytesIO | str) -> str:
    """Extract raw text from a PDF file-like object or path."""

    with pdfplumber.open(file_like) as pdf:
        pages_text: list[str] = []
        for page in pdf.pages:
            pages_text.append(page.extract_text() or "")
    return _normalise_whitespace(" ".join(pages_text))


@lru_cache(maxsize=1)
def _get_presidio_engines():
    if AnalyzerEngine is None or AnonymizerEngine is None:
        return None, None
    return AnalyzerEngine(), AnonymizerEngine()


def anonymise_text(text: str) -> str:
    analyzer, anonymizer = _get_presidio_engines()
    if analyzer is None or anonymizer is None:
        return text

    results = analyzer.analyze(text=text, language="en")
    return anonymizer.anonymize(text=text, analyzer_results=results).text


def summarise_contract(llm_messages: Iterable[dict[str, str]]) -> str:
    """Delegated to the LLM service; kept for API completeness."""

    # This module only keeps whitespace helpers – actual LLM calls happen elsewhere.
    raise NotImplementedError("Use services.llm.chat for contract summarisation requests.")


__all__ = ["anonymise_text", "extract_text_from_pdf"]
