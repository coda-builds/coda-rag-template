#!/usr/bin/env python3
"""
Run a set of demo queries against the RAG API and print formatted results.

Usage:
    python scripts/test_query.py [--api-url URL] [--api-key KEY]
"""

from __future__ import annotations

import argparse
import sys
import textwrap

import httpx

DEMO_QUERIES = [
    "What is the annual leave entitlement and how far in advance must I book it?",
    "What are the MFA requirements for company systems?",
    "What is the expense limit for a hotel in London without needing pre-approval?",
    "How do I submit an expense claim and when will I be reimbursed?",
    "What do I need to complete before my first day at the company?",
    "What is the uptime SLA for the Growth plan?",
    "Can I carry over unused annual leave, and if so how many days?",
    "What are the password requirements for company accounts?",
]


def run_query(client: httpx.Client, api_url: str, headers: dict, query: str) -> dict:
    response = client.post(
        f"{api_url}/api/query",
        json={"query": query, "top_k": 4},
        headers=headers,
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def print_result(result: dict) -> None:
    print(f"\n{'═' * 70}")
    print(f"  Q: {result['query']}")
    print(f"{'═' * 70}")
    answer = textwrap.fill(
        result["answer"], width=68, initial_indent="  ", subsequent_indent="  "
    )
    print(answer)
    print(f"\n  Sources ({len(result['sources'])} chunks retrieved):")
    for src in result["sources"]:
        print(f"    • [{src['score']:.3f}] {src['title']}  ({src['source'] or '—'})")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run demo queries against the RAG API")
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--api-key", default="")
    parser.add_argument(
        "--query", default="", help="Run a single custom query instead of the demo set"
    )
    args = parser.parse_args()

    headers: dict[str, str] = {}
    if args.api_key:
        headers["Authorization"] = f"Bearer {args.api_key}"

    queries = [args.query] if args.query else DEMO_QUERIES

    print(f"\nRunning {len(queries)} query/queries against {args.api_url}\n")

    with httpx.Client() as client:
        try:
            client.get(f"{args.api_url}/health", timeout=10).raise_for_status()
        except Exception as e:
            print(f"✗ Cannot reach API: {e}")
            sys.exit(1)

        for query in queries:
            try:
                result = run_query(client, args.api_url, headers, query)
                print_result(result)
            except httpx.HTTPStatusError as e:
                print(f"✗ Query failed: {e.response.status_code} – {e.response.text}")


if __name__ == "__main__":
    main()
