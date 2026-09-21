"""Run with: pytest -q. Tools are called directly as plain functions."""
import pytest

import server as S


def first_line(out: str) -> str:
    return out.splitlines()[0]


@pytest.mark.parametrize(
    "call, expected",
    [
        (lambda: S.differentiate("x**2*sin(x)"), "result: x**2*cos(x) + 2*x*sin(x)"),
        (lambda: S.differentiate("x^4", order=2), "result: 12*x**2"),
        (lambda: S.differentiate("3x + 2y"), "result: 3"),
        (lambda: S.integrate_indefinite("x*exp(x)"), "result: (x - 1)*exp(x)"),
        (lambda: S.integrate_definite("sin(x)", "0", "pi"), "result: 2"),
        (lambda: S.integrate_definite("exp(-x**2)", "-oo", "oo"), "result: sqrt(pi)"),
        (lambda: S.integrate_definite("sin(x)/x", "0", "oo"), "result: pi/2"),
        (lambda: S.limit("sin(x)/x", "0"), "result: 1"),
        (lambda: S.limit("1/x", "0", direction="+"), "result: oo"),
        (lambda: S.limit("(1+3/x)**(2*x)", "oo"), "result: exp(6)"),
        (lambda: S.series("exp(x)", n=4), "result: 1 + x + x**2/2 + x**3/6 + O(x**4)"),
        (lambda: S.solve("x**2 - 4 = 0"), "result: [-2, 2]"),
        (lambda: S.solve("x**3 - 6*x**2 + 11*x - 6 = 0"), "result: [1, 2, 3]"),
        (lambda: S.simplify("sin(x)**2 + cos(x)**2"), "result: 1"),
    ],
)
def test_known_answers(call, expected):
    assert first_line(call()) == expected


def test_simplify_flags():
    e = "log(sqrt((1+sin(x))/(1-sin(x))))"
    assert first_line(S.differentiate(e, simplify_result=True)) == "result: 1/cos(x)"
    assert "1/cos(x)" not in S.differentiate(e)  # raw form is the messy fraction


@pytest.mark.parametrize(
    "expr", ["().__class__", "__import__('os')", "(1).real", "'a'", "x;y", "x" * 400]
)
def test_rejects_unsafe_input(expr):
    assert S.differentiate(expr).startswith("error:")


def test_bad_arguments():
    assert S.differentiate("x", order=99).startswith("error:")
    assert S.limit("x", "0", direction="up").startswith("error:")
    assert S.series("x", n=0).startswith("error:")
    assert S.differentiate("x", var="1bad").startswith("error:")


def test_no_closed_form():
    out = S.integrate_definite("x**x", "0", "1")
    assert out.startswith("error:") and "no closed form" in out


def test_timeout_kills_hanging_work(monkeypatch):
    import time

    monkeypatch.setattr(S, "TIMEOUT_SECONDS", 1)
    monkeypatch.setattr(S, "_simplify", lambda expr: time.sleep(30))
    start = time.time()
    assert S.simplify("x").startswith("error: timed out")
    assert time.time() - start < 5


def test_simplify_timeout_falls_back_to_raw(monkeypatch):
    import time

    monkeypatch.setattr(S, "TIMEOUT_SECONDS", 2)
    monkeypatch.setattr(S.sp, "simplify", lambda e, *a, **k: time.sleep(30))
    out = S.differentiate("x**3", simplify_result=True)
    assert first_line(out) == "result: 3*x**2"
    assert "note: simplify did not finish" in out
