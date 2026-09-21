import multiprocessing as mp
import os
import re

import sympy as sp
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)
from mcp.server.mcpserver import MCPServer

mcp = MCPServer("calc-mcp")

TIMEOUT_SECONDS = 10
MAX_INPUT_LEN = 300

_NAMES = (
    "sin cos tan cot sec csc asin acos atan sinh cosh tanh asinh acosh atanh "
    "exp log sqrt cbrt Abs sign floor ceiling factorial gamma erf "
    "pi E I oo"
).split()
# Symbol/Integer/Float/Rational are needed by parse_expr's own generated code.
_INTERNAL = ("Symbol", "Integer", "Float", "Rational")
_GLOBALS = {
    "__builtins__": {},
    **{n: getattr(sp, n) for n in _NAMES + list(_INTERNAL)},
    "ln": sp.log,
}
_TRANSFORMS = standard_transformations + (implicit_multiplication_application, convert_xor)
_ATTR_ACCESS = re.compile(r"\.\s*[A-Za-z_]")


def _parse(text: str) -> sp.Basic:
    if len(text) > MAX_INPUT_LEN:
        raise ValueError("input too long")
    if "__" in text or _ATTR_ACCESS.search(text) or any(c in text for c in "'\"`;\\"):
        raise ValueError(f"disallowed characters in expression: {text!r}")
    return parse_expr(text, global_dict=dict(_GLOBALS), transformations=_TRANSFORMS, evaluate=True)


def _sym(name: str) -> sp.Symbol:
    if not re.fullmatch(r"[A-Za-z]\w{0,15}", name):
        raise ValueError(f"bad variable name: {name!r}")
    return sp.Symbol(name)


def _fmt(result) -> str:
    return f"result: {result}\nlatex: {sp.latex(result)}"


def _worker(queue, fn, args, simplify_result):
    try:
        raw = fn(*args)
        queue.put(("raw", _fmt(raw)))
        if simplify_result:
            queue.put(("ok", _fmt(sp.simplify(raw))))
        else:
            queue.put(("ok", _fmt(raw)))
    except Exception as e:  # noqa: BLE001 - report any math/parse error to caller
        queue.put(("err", f"{type(e).__name__}: {e}"))


def _run(fn, *args, simplify_result: bool = False) -> str:
    """Run fn(*args) in a child process so a hanging computation can be killed.

    With simplify_result, the raw result is kept as a fallback if simplify is too slow.
    """
    ctx = mp.get_context("fork")
    queue = ctx.Queue()
    proc = ctx.Process(target=_worker, args=(queue, fn, args, simplify_result), daemon=True)
    proc.start()
    proc.join(TIMEOUT_SECONDS)
    timed_out = proc.is_alive()
    if timed_out:
        proc.kill()
        proc.join()
    msgs = {}
    try:
        while True:
            kind, payload = queue.get(timeout=0.5)
            msgs[kind] = payload
    except Exception:  # noqa: BLE001 - queue drained
        pass
    if "ok" in msgs:
        return msgs["ok"]
    if "err" in msgs and "raw" not in msgs:
        return f"error: {msgs['err']}"
    if "raw" in msgs:
        return msgs["raw"] + f"\nnote: simplify did not finish in {TIMEOUT_SECONDS}s; result is unsimplified"
    if timed_out:
        return f"error: timed out after {TIMEOUT_SECONDS}s (no closed form found in time)"
    return "error: computation crashed"


def _differentiate(expr, var, order, simplify_input):
    e = _parse(expr)
    if simplify_input:
        e = sp.simplify(e)
    return sp.diff(e, _sym(var), order)


def _integrate(expr, var):
    r = sp.integrate(_parse(expr), _sym(var))
    if r.has(sp.Integral):
        raise ValueError("no closed form found")
    return r


def _integrate_definite(expr, var, lower, upper):
    r = sp.integrate(_parse(expr), (_sym(var), _parse(lower), _parse(upper)))
    if r.has(sp.Integral):
        raise ValueError("no closed form found")
    return r


def _limit(expr, var, point, direction):
    return sp.limit(_parse(expr), _sym(var), _parse(point), direction)


def _series(expr, var, point, n):
    return sp.series(_parse(expr), _sym(var), _parse(point), n)


def _solve(equation, var):
    if "=" in equation:
        left, right = equation.split("=", 1)
        eq = sp.Eq(_parse(left), _parse(right))
    else:
        eq = _parse(equation)
    return sp.solve(eq, _sym(var))


def _simplify(expr):
    return sp.simplify(_parse(expr))


@mcp.tool()
def differentiate(
    expr: str,
    var: str = "x",
    order: int = 1,
    simplify_input: bool = False,
    simplify_result: bool = False,
) -> str:
    """Derivative of expr with respect to var. Example: expr="x**2*sin(x)".

    For a large or messy expr, set simplify_input=True (simplify before differentiating)
    and simplify_result=True (simplify the derivative). Both are off by default.
    """
    if not 1 <= order <= 10:
        return "error: order must be 1..10"
    return _run(_differentiate, expr, var, order, simplify_input, simplify_result=simplify_result)


@mcp.tool()
def integrate_indefinite(expr: str, var: str = "x", simplify_result: bool = False) -> str:
    """Antiderivative of expr (no constant of integration). Example: expr="x*exp(x)".

    Set simplify_result=True to simplify the answer.
    """
    return _run(_integrate, expr, var, simplify_result=simplify_result)


@mcp.tool()
def integrate_definite(
    expr: str, lower: str, upper: str, var: str = "x", simplify_result: bool = False
) -> str:
    """Definite integral of expr from lower to upper. Bounds may be "0", "pi", "oo", "-oo".

    Set simplify_result=True to simplify the answer.
    """
    return _run(_integrate_definite, expr, var, lower, upper, simplify_result=simplify_result)


@mcp.tool()
def limit(
    expr: str, point: str, var: str = "x", direction: str = "+-", simplify_result: bool = False
) -> str:
    """Limit of expr as var approaches point. direction is "+", "-" or "+-" (two-sided).

    Set simplify_result=True to simplify the answer.
    """
    if direction not in ("+", "-", "+-"):
        return 'error: direction must be "+", "-" or "+-"'
    return _run(_limit, expr, var, point, direction, simplify_result=simplify_result)


@mcp.tool()
def series(expr: str, point: str = "0", var: str = "x", n: int = 6) -> str:
    """Taylor series of expr around point, up to (not including) order n."""
    if not 1 <= n <= 30:
        return "error: n must be 1..30"
    return _run(_series, expr, var, point, n)


@mcp.tool()
def solve(equation: str, var: str = "x") -> str:
    """Solve equation for var. Use "=" or give an expression equal to zero. Example: "x**2 - 4 = 0"."""
    return _run(_solve, equation, var)


@mcp.tool()
def simplify(expr: str) -> str:
    """Simplify an expression. Example: "sin(x)**2 + cos(x)**2"."""
    return _run(_simplify, expr)


if __name__ == "__main__":
    if os.environ.get("MCP_TRANSPORT") == "http":
        mcp.run("streamable-http", host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
    else:
        mcp.run()
