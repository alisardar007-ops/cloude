"""MCP server that lets Claude (Claude Code, Claude Desktop, ...) ask Gemini.

Exposes two tools:
    ask_gemini  sends a prompt (and optionally the contents of local files)
                to Gemini and returns its reply.
    make_video  generates a short video with Veo and saves it as an .mp4.

Env vars:
    GEMINI_API_KEY  required, from https://aistudio.google.com/apikey
    GEMINI_MODEL    optional, defaults to DEFAULT_MODEL below
    VEO_MODEL       optional, defaults to DEFAULT_VIDEO_MODEL below
"""

import os
import re
import time
from datetime import datetime
from pathlib import Path

from google import genai
from google.genai import types
from mcp.server.fastmcp import FastMCP

DEFAULT_MODEL = "gemini-3.5-flash"
DEFAULT_VIDEO_MODEL = "veo-3.1-lite-generate-preview"
MAX_FILE_BYTES = 2_000_000
VIDEO_DIR = Path("videos")
VIDEO_TIMEOUT_SECONDS = 15 * 60

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
    """Ask Gemini a question and return its answer.

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


def _default_video_path(prompt: str) -> Path:
    slug = re.sub(r"[^a-z0-9]+", "-", prompt.lower()).strip("-")[:40] or "video"
    return VIDEO_DIR / f"{datetime.now():%Y%m%d-%H%M%S}-{slug}.mp4"


@mcp.tool()
def make_video(
    prompt: str,
    output_path: str | None = None,
    aspect_ratio: str | None = None,
    duration_seconds: int | None = None,
    negative_prompt: str | None = None,
    model: str | None = None,
) -> str:
    """Generate a short video with Google Veo and save it as an .mp4 file.

    Requires billing on the Gemini API key: the free tier can't generate
    video. Each call is billed per second of video, and takes a few minutes.

    Args:
        prompt: What should happen in the video. Describe the subject, action,
            setting, camera movement, style, and any dialogue or sound.
        output_path: Optional .mp4 path to save to (defaults to videos/<time>-<prompt>.mp4).
        aspect_ratio: Optional "16:9" (landscape, default) or "9:16" (portrait).
        duration_seconds: Optional clip length in seconds (model default if omitted).
        negative_prompt: Optional description of what to keep out of the video.
        model: Optional Veo model id (defaults to VEO_MODEL env var).
    """
    client = _get_client()
    operation = client.models.generate_videos(
        model=model or os.environ.get("VEO_MODEL", DEFAULT_VIDEO_MODEL),
        prompt=prompt,
        config=types.GenerateVideosConfig(
            number_of_videos=1,
            aspect_ratio=aspect_ratio,
            duration_seconds=duration_seconds,
            negative_prompt=negative_prompt,
        ),
    )

    deadline = time.monotonic() + VIDEO_TIMEOUT_SECONDS
    while not operation.done:
        if time.monotonic() > deadline:
            raise TimeoutError(f"Video still generating after {VIDEO_TIMEOUT_SECONDS}s: {operation.name}")
        time.sleep(10)
        operation = client.operations.get(operation)

    if operation.error:
        raise RuntimeError(f"Video generation failed: {operation.error}")
    videos = operation.response.generated_videos if operation.response else None
    if not videos:
        reasons = operation.response.rai_media_filtered_reasons if operation.response else None
        raise RuntimeError(f"Veo returned no video. Filtered reasons: {reasons or 'none given'}")

    path = Path(output_path).expanduser() if output_path else _default_video_path(prompt)
    path.parent.mkdir(parents=True, exist_ok=True)
    video = videos[0].video
    client.files.download(file=video)
    video.save(str(path))
    return f"Saved video to {path.resolve()}"


if __name__ == "__main__":
    mcp.run()
