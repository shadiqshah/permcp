# calc-mcp

MCP server for exact calculus and algebra, backed by SymPy. Built on the official `mcp` Python SDK v2.

## Tools

| Tool | Example |
|------|---------|
| `differentiate(expr, var="x", order=1, simplify_input=False, simplify_result=False)` | `x**2*sin(x)` |
| `integrate_indefinite(expr, var="x")` | `x*exp(x)` |
| `integrate_definite(expr, lower, upper, var="x")` | `sin(x)`, `0`, `pi` |
| `limit(expr, point, var="x", direction="+-")` | `sin(x)/x`, `0` |
| `series(expr, point="0", var="x", n=6)` | `exp(x)` |
| `solve(equation, var="x")` | `x**2 - 4 = 0` |
| `simplify(expr)` | `sin(x)**2 + cos(x)**2` |

`simplify_result` (also on both integrals and `limit`) simplifies the answer; `simplify_input` simplifies the expression before differentiating. Both are off by default. If simplify runs past the 10 s limit, the raw result is returned with a note.

Each tool returns `result:` (plain text) and `latex:`. `^` works as power, `3x` as `3*x`, `oo` is infinity.

Safety: input is parsed with no Python builtins, attribute access and dunder names are rejected, and every computation runs in a child process killed after 10 s.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python server.py                            # stdio
MCP_TRANSPORT=http python server.py         # http://0.0.0.0:8000/mcp
MCP_TRANSPORT=http PORT=8001 python server.py
```

## Claude Code

```bash
claude mcp add calc -- /absolute/path/to/.venv/bin/python /absolute/path/to/server.py
```

## Claude Desktop

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

## Browser AI (claude.ai, ChatGPT)

```bash
MCP_TRANSPORT=http python server.py
cloudflared tunnel --url http://localhost:8000
```

Add `https://<random>.trycloudflare.com/mcp` as a custom connector. No auth: anyone with the URL can use it.
