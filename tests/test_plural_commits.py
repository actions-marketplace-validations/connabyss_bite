"""Bite printed "1 commits changed code" and "Checked 1 commit(s)" for a single commit. Read aloud, "(s)" is
noise and "1 commits" is a typo; say "1 commit" and "2 commits" instead."""

import subprocess
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
RECENT = str(KIT / "recent.py")


def git(root, *a):
    return subprocess.run(["git", *a], cwd=root, check=True, capture_output=True, text=True).stdout


def commit(root, msg):
    git(root, "add", "-A")
    git(root, "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", "commit", "-q", "-m", msg)


def test_a_single_checked_commit_is_not_plural(tmp_path):
    root = tmp_path / "shop"
    (root / "tests").mkdir(parents=True)
    git(root, "init", "-q")
    (root / "shop.py").write_text("def total(a, b):\n    return a + b + 1\n")
    (root / "tests" / "test_shop.py").write_text(
        "from shop import total\n\n\ndef test_total():\n    assert total(1, 1) == 2\n")
    commit(root, "Start")
    (root / "shop.py").write_text("def total(a, b):\n    return a + b\n")
    commit(root, "Fix total adding one too many")

    p = subprocess.run([sys.executable, RECENT, "--free", "--last", "1"], cwd=root, capture_output=True,
                       text=True, timeout=300)
    out = p.stdout + p.stderr
    assert "Bite: 1 commit changed code in the last 1." in out, out
    assert "Checked 1 commit:" in out, out
    assert "1 commits" not in out and "commit(s)" not in out, out
