"""Gemini Pro drafts an answer, Claude reviews and improves it.

Usage:
    python3 collab.py "Design a rate limiter for a REST API"

Env vars:
    GEMINI_API_KEY     from https://aistudio.google.com/apikey
    ANTHROPIC_API_KEY  from https://console.anthropic.com
    GEMINI_MODEL       optional, defaults to gemini-3.5-flash
    CLAUDE_MODEL       optional, defaults to claude-opus-5-5
"""

import os
import sys

import anthropic
from google import genai

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-5-5")


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(f'Usage: python3 {sys.argv[0]} "your question"')
    question = " ".join(sys.argv[1:])

    for key in ("GEMINI_API_KEY", "ANTHROPIC_API_KEY"):
        if not os.environ.get(key):
            sys.exit(f"{key} is not set.")

    print(f"--- Gemini ({GEMINI_MODEL}) draft ---\n")
    draft = genai.Client().models.generate_content(
        model=GEMINI_MODEL, contents=question
    ).text
    print(draft)

    print(f"\n--- Claude ({CLAUDE_MODEL}) review ---\n")
    review = anthropic.Anthropic().messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Question:\n{question}\n\n"
                    f"Another model answered:\n{draft}\n\n"
                    "Point out any mistakes or gaps, then give the improved final answer."
                ),
            }
        ],
    )
    print("".join(b.text for b in review.content if b.type == "text"))


if __name__ == "__main__":
    main()
