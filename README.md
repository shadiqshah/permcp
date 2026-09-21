# yo-babes

Minimal MCP server. One tool, `greet`, returns `yo babes how are you`.

Built on the official `mcp` Python SDK v2 (`MCPServer`, formerly `FastMCP`).

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python server.py                    # stdio (default)
MCP_TRANSPORT=http python server.py # streamable-http on http://0.0.0.0:8000/mcp
```

## Test with the MCP Inspector

```bash
mcp dev server.py
```

Needs Node.js (the command fetches the Inspector via `npx`). Open the printed URL, then list tools and run `greet`.

## Claude Desktop

Add to `claude_desktop_config.json`. Use absolute paths.

```json
{
  "mcpServers": {
    "yo-babes": {
      "command": "/absolute/path/to/.venv/bin/python",
      "args": ["/absolute/path/to/server.py"]
    }
  }
}
```

## Claude Code

```bash
claude mcp add yo-babes -- /absolute/path/to/.venv/bin/python /absolute/path/to/server.py
```

## Remote clients (ChatGPT etc.) over HTTP

Start the server in HTTP mode:

```bash
MCP_TRANSPORT=http python server.py
```

Expose port 8000 with one of:

```bash
cloudflared tunnel --url http://localhost:8000
# or
ngrok http 8000
```

Use the public URL plus `/mcp`, e.g. `https://<random>.trycloudflare.com/mcp`.

The server has no auth. Anyone with the URL can call it. Stop the tunnel when done.
