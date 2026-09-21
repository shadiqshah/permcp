# permcp

An [MCP](https://modelcontextprotocol.io) server that gives AI assistants exact calculus and algebra, powered by [SymPy](https://www.sympy.org). Language models often get symbolic math wrong. This server computes it instead of guessing.

The server contains no LLM and makes no model calls. The chat model decides which tool to call. The server runs that call deterministically and returns the result.

## Tools

| Tool | Arguments | Example |
|------|-----------|---------|
| `differentiate` | `expr`, `var="x"`, `order=1`, `simplify_input=False`, `simplify_result=False` | `x**2*sin(x)` |
| `integrate_indefinite` | `expr`, `var="x"`, `simplify_result=False` | `x*exp(x)` |
| `integrate_definite` | `expr`, `lower`, `upper`, `var="x"`, `simplify_result=False` | `sin(x)`, `0`, `pi` |
| `limit` | `expr`, `point`, `var="x"`, `direction="+-"`, `simplify_result=False` | `sin(x)/x`, `0` |
| `series` | `expr`, `point="0"`, `var="x"`, `n=6` | `exp(x)` |
| `solve` | `equation`, `var="x"` | `x**2 - 4 = 0` |
| `simplify` | `expr` | `sin(x)**2 + cos(x)**2` |

- Every tool returns text: `result:` (plain) and `latex:`. Failures return a string starting with `error:`.
- Expression syntax: `**` or `^` for powers, implicit multiplication (`3x`), `pi`, `E`, `I`, `oo` (infinity), and functions `sin cos tan cot sec csc asin acos atan sinh cosh tanh asinh acosh atanh exp log ln sqrt cbrt Abs sign floor ceiling factorial gamma erf`.
- `simplify_input` (differentiate only) simplifies the expression before differentiating. `simplify_result` simplifies the answer. If simplify does not finish within the time limit, the raw result comes back with a `note:` line.
- `direction` for `limit` is `+`, `-` or `+-` (two-sided). Ranges: `order` 1..10, `n` 1..30.

## Safety

The server can sit behind a public URL, so input handling is strict:

- Expressions are parsed with no Python builtins and a fixed whitelist of names.
- Attribute access, dunder names, quotes, backticks, `;` and `\` are rejected. Input over 300 characters is rejected.
- Each computation runs in a child process that is killed after 10 seconds.
- There is no authentication. Anyone with the URL can use the server. It has no side effects, so the worst case is CPU load.

## Install

Needs Python 3.10+ on Linux or macOS (the timeout uses `fork`).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python server.py                             # stdio (default)
MCP_TRANSPORT=http python server.py          # streamable HTTP on http://0.0.0.0:8000/mcp
MCP_TRANSPORT=http PORT=8001 python server.py
```

Test interactively with the MCP Inspector (needs Node.js): `mcp dev server.py`.

## Use it

### Claude Code

```bash
claude mcp add calc -- /absolute/path/to/.venv/bin/python /absolute/path/to/server.py
```

### Claude Desktop

Add to `claude_desktop_config.json` and restart the app:

```json
{
  "mcpServers": {
    "calc": {
      "command": "/absolute/path/to/.venv/bin/python",
      "args": ["/absolute/path/to/server.py"]
    }
  }
}
```

### Browser chat (claude.ai, ChatGPT)

Browser clients need a public HTTPS URL. Run the HTTP server, then expose it:

```bash
MCP_TRANSPORT=http python server.py
cloudflared tunnel --url http://localhost:8000     # or: ngrok http 8000
```

Add `https://<random>.trycloudflare.com/mcp` as a custom connector:

- **claude.ai:** Settings, Connectors, Add custom connector (paid plan). Enable it per chat from the `+` menu.
- **ChatGPT:** Settings, Connectors, Advanced, enable Developer mode, then create a connector (paid plan).

A quick tunnel gets a new URL on every restart, so re-add the connector each time. If you change the tools, remove and re-add the connector so the client drops its cached tool list. A permanent URL needs a named Cloudflare tunnel or a hosted deployment.

## Test

```bash
pip install -r requirements-dev.txt
pytest -q
```

## Try it

Paste into a chat with the connector enabled:

> Use the calc tools for all of this. Differentiate `log(sqrt((1+sin(x))/(1-sin(x))))` and give the simplest form. Evaluate the integral of `sin(x)/x` from 0 to infinity. Find the limit of `(1 + 3/x)^(2x)` as x goes to infinity.

Expected: `1/cos(x)`, `pi/2`, `exp(6)`.

## Project layout

```
server.py            all server code
test_server.py       pytest suite
requirements.txt     runtime deps (mcp 2.x, sympy)
requirements-dev.txt test deps
AGENTS.md            notes for AI assistants working on this repo
```

Built on the official `mcp` Python SDK v2, where `FastMCP` is now `MCPServer` (`from mcp.server.mcpserver import MCPServer`).
