"""Runs Bite's offline self-test (tests/selftest.py) under pytest. No key, no network.
Its "ok"/"FAIL" lines print as they run (pytest's -s is on in pyproject.toml), so a slow PC doesn't look frozen.

The self-test is split into parts ("# --- part ---" lines), one pytest test each, so pytest -n auto runs them side
by side: as one process it took 50 sec on Linux while the other cores waited, the slowest test of the suite
(2026-11-04). The same checks run; `python tests/selftest.py` still runs them all in one go."""

import ast
import subprocess
import sys
from pathlib import Path

import pytest

SELFTEST = Path(__file__).with_name("selftest.py")
LINES = SELFTEST.read_text(encoding="utf-8").splitlines()
PARTS = sum(ln == "# --- part ---" for ln in LINES)


@pytest.mark.parametrize("part", range(1, PARTS + 1))
def test_selftest(part):
    r = subprocess.run([sys.executable, str(SELFTEST), "--part", str(part)])
    assert r.returncode == 0, f"a self-test check in part {part} failed: see the FAIL lines above"


def test_every_check_is_in_exactly_one_part():
    # A check above the first part or below the end would run in every part, or in none if a part forgot it.
    first = LINES.index("# --- part ---") + 1
    end = LINES.index("# --- end of parts ---") + 1
    outside = [n.lineno for n in ast.parse("\n".join(LINES)).body
               if (n.lineno < first or n.lineno > end) and not isinstance(n, (ast.FunctionDef, ast.ClassDef))
               and "check(" in ast.unparse(n) and "_part(" not in ast.unparse(n)]
    assert PARTS >= 2 and not outside, f"checks outside the parts, at lines {outside}"
