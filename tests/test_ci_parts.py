"""CI splits the slow Windows and Mac test jobs across 2 machines (2026-11-04): each takes every other test
(--part K/2). Together they must run every test exactly once, and the checks main requires must still pass only
when every part passed. No key, no network."""

import re
import subprocess
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
FLOW = (KIT / ".github" / "workflows" / "tests.yml").read_text(encoding="utf-8")


def collected(*args):
    out = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", *args],
                         cwd=KIT, capture_output=True, text=True).stdout
    return [ln for ln in out.splitlines() if "::" in ln]


def test_the_parts_together_run_every_test_exactly_once():
    whole = collected()
    one, two = collected("--part", "1/2"), collected("--part", "2/2")
    assert one and two and len(whole) > 300
    assert sorted(one + two) == sorted(whole)  # none twice, none left out
    assert abs(len(one) - len(two)) <= 1
    # the slow self-test parts are shared out, not all on one machine
    assert any("test_selftest" in t for t in one) and any("test_selftest" in t for t in two)


def test_each_required_check_needs_all_of_its_parts():
    assert "--part ${{ matrix.part }}/${{ matrix.os == 'ubuntu-latest' && 1 || 2 }}" in FLOW
    test_job = FLOW[FLOW.index("\n  test:\n"):]
    assert "needs: part" in test_job and "if: always()" in test_job  # reports even when a part fails
    assert "want=${{ matrix.os == 'ubuntu-latest' && 1 || 2 }}" in test_job and '[ "$n" -eq "$want" ]' in test_job
    # named "test (os, python)" like the checks main requires: a matrix job named test, over the same os and python
    assert re.search(r"\n  test:\n(?:(?!\n  \w).)*?os: \[ubuntu-latest, windows-latest, macos-latest\]\n"
                     r"\s+python: \[\"3.10\", \"3.13\"\]", FLOW, re.S)
    # a part marks itself passed only after its tests did (a failed step stops the job before this)
    part = FLOW[FLOW.index("\n  part:\n"):FLOW.index("\n  test:\n")]
    assert part.index("python -m pytest") < part.index("echo ok > passed.txt") < part.index("upload-artifact")
