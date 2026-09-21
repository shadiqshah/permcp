# AGENTS.md

Context for an AI assistant continuing work on this repo. Read `README.md` first for usage.

## What this is

`permcp` is a single-file MCP server (`server.py`) exposing SymPy calculus and algebra tools to chat models. The server has no LLM. The calling model picks the tool and arguments. The server computes exactly and returns text.

## Commands

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pytest -q                                   # about 20 s, mostly timeout tests
python server.py                            # stdio
MCP_TRANSPORT=http PORT=8001 python server.py   # HTTP at /mcp
```

Run `pytest -q` after every change. Add a test for every new tool or behavior.

## Code map (`server.py`)

- `_parse` and `_GLOBALS`: the input sandbox. `parse_expr` runs Python `eval`, so this is the security boundary. `_GLOBALS` holds a name whitelist and empty `__builtins__`. `_parse` rejects `__`, attribute access, quotes and long input.
- `_INTERNAL` (Symbol, Integer, Float, Rational) must stay in `_GLOBALS`. The parser's own generated code calls them. Removing them gives `NameError: name 'Symbol' is not defined`.
- `_sym`: validates variable names.
- `_differentiate`, `_integrate`, `_integrate_definite`, `_limit`, `_series`, `_solve`, `_simplify`: pure SymPy helpers. They return a SymPy object or raise.
- `_worker` and `_run`: run a helper in a forked child process with a `TIMEOUT_SECONDS` limit and kill it on timeout. `_worker` sends the raw result first, then the simplified one. On a simplify timeout, `_run` returns the raw result plus a `note:`.
- Tool functions (`@mcp.tool()`): thin wrappers that validate ranges and call `_run`. Their docstrings are the only guidance the calling model sees, so word them carefully.

## Rules that must hold

1. Never call `sympify`, `eval` or `exec` on user input outside `_parse`.
2. Never widen the whitelist with anything that can reach files, the OS or Python internals.
3. Every computation goes through `_run` so a hang cannot block the server.
4. Tools return strings. Failures start with `error:`. Do not raise out of a tool.
5. `mcp` is pinned to `>=2,<3`. The v1 name `FastMCP` does not exist in v2.

## Gotchas

- `_run` uses `multiprocessing.get_context("fork")`. Windows has no `fork`, so the server does not work there as written.
- `_run` waits `queue.get(timeout=0.5)` once at the end of each call, which adds about 0.5 s to every call. Known and unfixed. Stop draining once an `ok` or `err` message arrives.
- Bind address is `0.0.0.0` in HTTP mode on purpose. Binding `127.0.0.1` turns on the SDK's Host-header check, which rejects tunnel hostnames (cloudflared, ngrok).
- Quick tunnels change URL on every restart. Browser connectors cache the tool list, so re-add the connector after changing tools.
- Some SymPy results are equivalent but differently shaped (`sec(x)` vs `1/cos(x)`). Tests compare exact strings, so a SymPy upgrade can change output text.

## Ideas not done yet

- `simplify_result` for `series`, `solve` and `simplify`.
- Server-level `instructions` on `MCPServer` and richer tool docstrings, to steer the calling model (for example, use `simplify_input` for long expressions).
- More tools: partial derivatives, multiple integrals, ODE solving (`dsolve`), matrix operations, numeric evaluation.
- Optional bearer-token auth for public deployment.
- Fix the fixed 0.5 s wait in `_run`.
- Permanent hosting (named Cloudflare tunnel, Fly, Render) with a Dockerfile.
- CI running `pytest`.

## Non-goals

No LLM calls inside the server. No file or network access from tools.
