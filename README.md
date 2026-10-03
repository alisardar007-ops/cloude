# Claude + Gemini Pro

Two ways to use Claude and Gemini Pro together:

1. **`gemini_mcp_server.py`**: an MCP server that gives Claude Code an `ask_gemini` tool.
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

## 2. Gemini drafts, Claude reviews

```bash
python3 collab.py "Design a rate limiter for a REST API"
```

## Choosing models

Set `GEMINI_MODEL` (default `gemini-3.5-flash`) or `CLAUDE_MODEL` (default `claude-opus-5-5`)
to override. For example, `export GEMINI_MODEL=gemini-2.5-pro`.
