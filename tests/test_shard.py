"""--shard K/N and --only: one long check split across several machines (2026-11-02: Bite's own weekly check took
about 3 hours on one machine). Each part checks a different share of the commits, together they check every one,
and --only checks just the commits named. No key, no network."""

import re
import subprocess
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
PY = sys.executable


def git(root, *a):
    return subprocess.run(["git", *a], cwd=root, check=True, capture_output=True, text=True).stdout


def make(tmp_path):
    root = tmp_path / "proj"
    (root / "tests").mkdir(parents=True)
    git(root, "init", "-q")
    (root / ".bite.ini").write_text(f"[bite]\ntest_command = {PY} -m pytest -q -p no:cacheprovider\n")
    (root / "shop.py").write_text("def a():\n    return 1\n")
    (root / "tests" / "test_shop.py").write_text("import shop\n\n\ndef test_a():\n    assert shop.a() == 1\n")
    shas = []
    for i, name in enumerate(["start", "Fix b", "Fix c", "Fix d", "Fix e"]):
        if i:
            with open(root / "shop.py", "a") as f:
                f.write(f"\n\ndef {name[-1]}():\n    return {i}\n")
        git(root, "add", "-A")
        git(root, "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", "commit", "-q", "-m", name)
        shas.append(git(root, "rev-parse", "HEAD").strip())
    return root, shas[1:]


def checked(root, *args):
    out = subprocess.run([PY, str(KIT / "recent.py"), "--free", "--any", "--free-checks", "10", *args], cwd=root,
                         capture_output=True, text=True, timeout=300).stdout
    return set(re.findall(r"^  ([0-9a-f]{8}) ", out, re.M)), out


def test_the_parts_split_the_commits_and_together_check_every_one(tmp_path):
    root, shas = make(tmp_path)
    one, out1 = checked(root, "--shard", "1/2")
    two, out2 = checked(root, "--shard", "2/2")
    assert one and two and not one & two, out1 + out2
    assert one | two == {s[:8] for s in shas}, out1 + out2


def test_only_checks_just_the_commits_named(tmp_path):
    root, shas = make(tmp_path)
    got, out = checked(root, "--only", f"{shas[0][:8]},{shas[2][:10]}")
    assert got == {shas[0][:8], shas[2][:8]}, out


def test_only_finds_a_commit_older_than_the_last_ones_looked_at(tmp_path):
    # The 11-03 hunt: --only 0864b3ce said "Nothing to check" because Bite only looked among the last 40 commits.
    root, shas = make(tmp_path)
    got, out = checked(root, "--last", "1", "--only", shas[0][:8])
    assert got == {shas[0][:8]}, out


def test_a_shard_that_isnt_one_of_the_parts_is_refused(tmp_path):
    root, _ = make(tmp_path)
    r = subprocess.run([PY, str(KIT / "recent.py"), "--free", "--shard", "3/2"], cwd=root, capture_output=True,
                       text=True)
    assert r.returncode == 2 and "--shard 2/5" in r.stdout


def test_help_explains_shard_and_only_in_plain_words():
    out = subprocess.run([sys.executable, str(KIT / "recent.py"), "--help"], capture_output=True, text=True,
                         encoding="utf-8").stdout
    assert "split the check into 5 parts and run part 2" in out and "in about a fifth of the time" in out
    assert re.search(r"^ +bite --only 1a2b3c4d +check just the commits named", out, re.M), out
