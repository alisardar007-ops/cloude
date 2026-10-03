# Claude + Gemini

Two ways to use Claude and Gemini together:

1. **`gemini_mcp_server.py`**: an MCP server that gives Claude Code `ask_gemini` and `make_video` tools.
2. **`collab.py`**: a script where Gemini drafts an answer and Claude reviews it.

## Setup

```bash
pip install -r requirements.txt
export GEMINI_API_KEY=...      # https://aistudio.google.com/apikey
export ANTHROPIC_API_KEY=...   # https://console.anthropic.com (only needed for collab.py)
```

A Gemini app or Claude.ai subscription doesn't give you API access. You need API keys from the links above.

## 1. Use Gemini from inside Claude Code

The `.mcp.json` in this repo registers the server automatically. Start Claude Code in this folder
with `GEMINI_API_KEY` exported, approve the `gemini` server when asked, and check that it shows up with `/mcp`.
Then just ask, for example:

- "Ask Gemini for a second opinion on this function."
- "Have Gemini read `src/` with ask_gemini and summarize the architecture."

To use it from **any** project, register it once at user scope with an absolute path:

```bash
claude mcp add gemini --scope user -e GEMINI_API_KEY=$GEMINI_API_KEY \
  -- python3 /absolute/path/to/gemini_mcp_server.py
```

For **Claude Desktop**, add this to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "gemini": {
      "command": "python3",
      "args": ["/absolute/path/to/gemini_mcp_server.py"],
      "env": { "GEMINI_API_KEY": "your-key" }
    }
  }
}
```

The `ask_gemini` tool takes these arguments: `prompt`, optional `files` (local text files to include),
`system_instruction`, `model`, and `temperature`.

### Making videos

The `make_video` tool generates a short clip with Google's Veo model and saves it as an `.mp4` under
`videos/`. You don't need to write the Veo prompt yourself. Describe the video you want and Claude writes
the prompt, for example:

- "Make a 9:16 video of a cat waving hello on a sunny windowsill."
- "Make an 8-second product shot of a coffee mug rotating on a marble counter."

Video needs **billing turned on** for your Gemini API key (in Google AI Studio). The free tier rejects every
video request with `429 RESOURCE_EXHAUSTED`. Veo charges per second of video, so check Google's pricing page.
Each clip takes a few minutes to generate.

The tool takes `prompt`, optional `output_path`, `aspect_ratio` (`16:9` or `9:16`), `duration_seconds`,
`negative_prompt`, and `model`. It defaults to the cheapest model, `veo-3.1-lite-generate-preview`.
Set `VEO_MODEL` to `veo-3.1-fast-generate-preview` or `veo-3.1-generate-preview` for higher quality at a higher price.

## 2. Gemini drafts, Claude reviews

```bash
python3 collab.py "Design a rate limiter for a REST API"
```

## Choosing models

Set `GEMINI_MODEL` (default `gemini-3.5-flash`) or `CLAUDE_MODEL` (default `claude-opus-5-5`)
to override. For example, `export GEMINI_MODEL=gemini-2.5-pro`.
