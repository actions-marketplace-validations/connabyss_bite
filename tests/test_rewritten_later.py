"""h2 #1329: Bite flagged commit e1f7c12c ("no test noticed"), but a6ed24e later in the same pull request rewrote
that exact code, and a test notices the rewrite: the pull request's final code was guarded. Now a gap whose code a
later commit rewrote, when Bite checked that later commit in the same run and a test noticed it, is skipped with
that said. When the rewrite isn't noticed either, the gap stands. No key, no network."""

import json
import re
import os
import subprocess
import sys
from pathlib import Path

RECENT = str(Path(__file__).resolve().parent.parent / "recent.py")
GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"]
START = "def total(xs):\n    return sum(xs)\n\n\ndef label(x):\n    return str(x)\n"
FIRST = "def total(xs):\n    return round(sum(xs), 1)\n\n\ndef label(x):\n    return str(x)\n"
REWRITE = "def total(xs):\n    return round(sum(xs), 2)\n\n\ndef label(x):\n    return str(x)\n"


def run(tmp_path, rewrite_test):
    root = tmp_path / "shop"
    root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    steps = [("Start", {"shop.py": START, "test_label.py": "from shop import label\n\n\ndef test_label():\n"
                                                           "    assert label(1) == '1'\n"}),
             ("Fix total rounding", {"shop.py": FIRST}),
             ("Fix total rounding to cents", {"shop.py": REWRITE, "test_total.py": rewrite_test})]
    for msg, files in steps:
        for name, text in files.items():
            (root / name).write_text(text, encoding="utf-8", newline="\n")
        subprocess.run([*GIT, "add", "-A"], cwd=root, check=True)
        subprocess.run([*GIT, "commit", "-q", "-m", msg], cwd=root, check=True)
    (root / ".bite.ini").write_text(f'[bite]\ntest_command = "{sys.executable}" -m pytest -q -p no:cacheprovider\n')
    p = subprocess.run([sys.executable, RECENT, "--free", "--json"], cwd=root, capture_output=True, text=True,
                       encoding="utf-8", timeout=300, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    return {c["subject"]: c for c in json.loads(p.stdout)["commits"]}, p.stderr


def test_a_gap_rewritten_later_by_a_noticed_commit_is_skipped(tmp_path):
    good = "from shop import total\n\n\ndef test_total():\n    assert total([0.11, 0.22]) == 0.33\n"
    cs, log = run(tmp_path, good)
    assert cs["Fix total rounding to cents"]["result"] == "noticed", (cs, log)
    first = cs["Fix total rounding"]
    assert first["result"] == "skipped" and "rewritten later" in str(first), (first, log)
    # The line printed while checking said no test noticed it; a later line must say it's not flagged after all,
    # or the list and the summary disagree (node-semver c570a348 on CH's PC).
    sha = first["sha"][:8]
    assert re.search(rf"^  {sha} ➖ after all, not flagged: \w{{8}} later rewrote", log, re.M), log


def test_the_gap_stands_when_the_rewrite_isnt_noticed_either(tmp_path):
    weak = "from shop import total\n\n\ndef test_total():\n    assert total([1]) == 1\n"
    cs, log = run(tmp_path, weak)
    assert cs["Fix total rounding"]["result"] == "no_test_noticed", (cs, log)
