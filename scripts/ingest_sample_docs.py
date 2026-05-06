#!/usr/bin/env python3
"""
Ingest the sample documents from sample_docs/ into the running API.

Usage:
    python scripts/ingest_sample_docs.py [--api-url URL] [--api-key KEY]

Defaults to http://localhost:8000 with no API key.
The script chunks each Markdown file by heading (##) and POSTs each chunk
as a separate document so retrieval is paragraph-granular.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import httpx

SAMPLE_DOCS_DIR = Path(__file__).parent.parent / "sample_docs"


def chunk_markdown(text: str, min_chars: int = 100) -> list[tuple[str, str]]:
    """
    Split a Markdown document into (heading, body) tuples at level-2 headings.
    Chunks shorter than min_chars are merged with the previous one.
    """
    parts = re.split(r"\n(?=## )", text)
    chunks: list[tuple[str, str]] = []

    for part in parts:
        lines = part.strip().split("\n")
        if not lines:
            continue
        heading = lines[0].lstrip("#").strip()
        body = "\n".join(lines[1:]).strip()

        if not body:
            continue

        # Merge very short chunks into the previous one
        if chunks and len(body) < min_chars:
            prev_heading, prev_body = chunks[-1]
            chunks[-1] = (prev_heading, f"{prev_body}\n\n{heading}: {body}")
        else:
            chunks.append((heading, body))

    return chunks


def ingest_file(
    client: httpx.Client,
    api_url: str,
    filepath: Path,
    headers: dict,
) -> int:
    """Chunk and ingest a single Markdown file. Returns number of chunks sent."""
    text = filepath.read_text(encoding="utf-8")

    # Extract top-level title if present
    title_match = re.match(r"^# (.+)", text)
    doc_title = title_match.group(1) if title_match else filepath.stem

    chunks = chunk_markdown(text)
    if not chunks:
        print(f"  ⚠  No chunks found in {filepath.name}, skipping.")
        return 0

    documents = [
        {
            "title": f"{doc_title} – {section_heading}",
            "content": section_body,
            "source": filepath.name,
            "metadata": {
                "document_title": doc_title,
                "section": section_heading,
                "file": filepath.name,
            },
        }
        for section_heading, section_body in chunks
    ]

    response = client.post(
        f"{api_url}/api/documents/batch",
        json={"documents": documents},
        headers=headers,
        timeout=60,
    )
    response.raise_for_status()
    result = response.json()
    print(f"  ✓  {filepath.name}: {result['inserted']} chunks ingested")
    return result["inserted"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest sample docs into the RAG API")
    parser.add_argument(
        "--api-url", default="http://localhost:8000", help="Base URL of the running API"
    )
    parser.add_argument(
        "--api-key", default="", help="Bearer token (leave empty if API_KEY is not set)"
    )
    args = parser.parse_args()

    headers: dict[str, str] = {}
    if args.api_key:
        headers["Authorization"] = f"Bearer {args.api_key}"

    md_files = sorted(SAMPLE_DOCS_DIR.glob("*.md"))
    if not md_files:
        print(f"No Markdown files found in {SAMPLE_DOCS_DIR}")
        sys.exit(1)

    print(f"\nIngesting {len(md_files)} document(s) from {SAMPLE_DOCS_DIR}\n")

    total = 0
    with httpx.Client() as client:
        # Verify the API is up
        try:
            client.get(f"{args.api_url}/health", timeout=10).raise_for_status()
        except Exception as e:
            print(f"✗ Cannot reach API at {args.api_url}: {e}")
            sys.exit(1)

        for filepath in md_files:
            total += ingest_file(client, args.api_url, filepath, headers)

    print(f"\n{'─' * 40}")
    print(f"  Total chunks ingested: {total}")
    print(f"{'─' * 40}\n")
    print("Run scripts/test_query.py to verify retrieval and generation.\n")


if __name__ == "__main__":
    main()
