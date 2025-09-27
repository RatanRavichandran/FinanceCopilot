from __future__ import annotations

import argparse
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from dy_finassist.services.llm import ChatMessage, LLMUnavailable, chat  # noqa: E402


def extract_clean_text(url: str) -> str:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")
    return soup.get_text(separator=" ", strip=True)


def summarise(text: str) -> str:
    return chat(
        [
            ChatMessage(
                role="system",
                content=(
                    "Summarise this loan product page for a product manager. Highlight product eligibility, key benefits, fees, and calls to action."
                ),
            ),
            ChatMessage(role="user", content=text[:12_000]),
        ],
        max_tokens=400,
        temperature=0.3,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarise loan information pages with the LLM.")
    parser.add_argument("url", help="Webpage to scrape")
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "data/reference/loans_summary_output.txt",
        help="Where to store the summary",
    )
    args = parser.parse_args()

    raw_text = extract_clean_text(args.url)

    try:
        summary = summarise(raw_text)
    except LLMUnavailable:
        summary = "Set OPENAI_API_KEY to enable automatic summarisation."

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(summary, encoding="utf-8")
    print(f"Summary written to {args.output}")


if __name__ == "__main__":
    main()
