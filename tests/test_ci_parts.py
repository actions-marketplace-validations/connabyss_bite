"""CI splits the slow Windows and Mac test jobs across 2 machines (2026-11-04): each takes every other test
(--part K/2). Together they must run every test exactly once. No key, no network."""

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


def test_windows_and_mac_run_in_2_parts_and_ubuntu_keeps_its_check_name():
    assert "--part ${{ matrix.part }}/${{ matrix.os == 'ubuntu-latest' && 1 || 2 }}" in FLOW
    assert re.search(r"part: \[1, 2\]\n\s+exclude:\n\s+- os: ubuntu-latest\n\s+part: 2\n", FLOW)
    # Ubuntu keeps the check name main requires; each Windows and Mac part is its own check
    assert "format('test ({0}, {1})', matrix.os, matrix.python)" in FLOW
    assert "format('tests part {0} ({1}, {2})', matrix.part, matrix.os, matrix.python)" in FLOW
