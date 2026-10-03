"""MCP server that lets Claude (Claude Code, Claude Desktop, ...) ask Gemini Pro.

Exposes one tool, `ask_gemini`, which sends a prompt (and optionally the
contents of local files) to Gemini and returns its reply.

Env vars:
    GEMINI_API_KEY  required, from https://aistudio.google.com/apikey
    GEMINI_MODEL    optional, defaults to DEFAULT_MODEL below
"""

import os
from pathlib import Path

from google import genai
from google.genai import types
from mcp.server.fastmcp import FastMCP

DEFAULT_MODEL = "gemini-3.1-pro-preview"
MAX_FILE_BYTES = 2_000_000

mcp = FastMCP("gemini")
_client = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        if not (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")):
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Get a key at https://aistudio.google.com/apikey "
                "and export it before starting Claude Code."
            )
        _client = genai.Client()
    return _client


def _read_files(paths: list[str]) -> str:
    parts = []
    for p in paths:
        path = Path(p).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"Not a file: {p}")
        if path.stat().st_size > MAX_FILE_BYTES:
            raise ValueError(f"File too large (> {MAX_FILE_BYTES} bytes): {p}")
        text = path.read_text(encoding="utf-8", errors="replace")
        parts.append(f"===== FILE: {p} =====\n{text}")
    return "\n\n".join(parts)


@mcp.tool()
def ask_gemini(
    prompt: str,
    files: list[str] | None = None,
    system_instruction: str | None = None,
    model: str | None = None,
    temperature: float | None = None,
) -> str:
    """Ask Google Gemini Pro a question and return its answer.

    Use this for a second opinion, to cross-check a solution, or to have
    Gemini read large files with its long context window.

    Args:
        prompt: The question or task for Gemini.
        files: Optional local text file paths whose contents are sent along.
        system_instruction: Optional system prompt for Gemini.
        model: Optional Gemini model id (defaults to GEMINI_MODEL env var).
        temperature: Optional sampling temperature (0.0-2.0).
    """
    contents = prompt
    if files:
        contents = f"{_read_files(files)}\n\n{prompt}"

    response = _get_client().models.generate_content(
        model=model or os.environ.get("GEMINI_MODEL", DEFAULT_MODEL),
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
        ),
    )
    return response.text or "(Gemini returned no text)"


if __name__ == "__main__":
    mcp.run()
