"""Faster for users (2026-11-02): --jobs checks several commits at the same time on one machine, and a commit
checked before with ✅ isn't run again unless something it depends on changed. Neither may hide a real gap.
No key, no network."""

import re
import subprocess
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
PY = sys.executable

# Fails whenever another run of it is going at the same time, like tests that use the same port or database.
CLASH = ("import os, time, tempfile, pathlib\n\n\ndef test_alone():\n"
         "    lock = pathlib.Path(tempfile.gettempdir()) / ('bite_clash_' + os.environ.get('CLASH_ID', ''))\n"
         "    try:\n        fd = os.open(lock, os.O_CREAT | os.O_EXCL)\n    except FileExistsError:\n"
         "        raise AssertionError('another run is using it')\n"
         "    try:\n        time.sleep(1.5)\n    finally:\n        os.close(fd)\n        os.remove(lock)\n")


def git(root, *a):
    return subprocess.run(["git", *a], cwd=root, check=True, capture_output=True, text=True).stdout


def commit(root, msg):
    git(root, "add", "-A")
    git(root, "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", "commit", "-q", "-m", msg)
    return git(root, "rev-parse", "HEAD").strip()[:8]


def bite(root, *args, env=None):
    import os
    e = dict(os.environ, **(env or {}))
    return subprocess.run([PY, str(KIT / "recent.py"), "--free", "--any", "--free-checks", "10", *args], cwd=root,
                          capture_output=True, text=True, timeout=300, env=e).stdout


def line(out, sha):
    return next((ln for ln in out.splitlines() if ln.startswith(f"  {sha} ")), "")


def project(tmp_path):
    root = tmp_path / "proj"
    (root / "tests").mkdir(parents=True)
    git(root, "init", "-q")
    (root / ".bite.ini").write_text(f"[bite]\ntest_command = {PY} -m pytest -q -p no:cacheprovider\n")
    (root / "shop.py").write_text("def total(xs):\n    return sum(xs)\n")
    (root / "tests" / "test_shop.py").write_text("import shop\n\n\ndef test_total():\n    assert shop.total([1, 2]) == 3\n")
    commit(root, "start")
    return root


def test_tests_that_clash_side_by_side_cant_hide_a_gap(tmp_path):
    root = project(tmp_path)
    (root / "tests" / "test_clash.py").write_text(CLASH)
    commit(root, "a test that needs the machine to itself")
    shas = []
    for name in ("a", "b", "c"):  # three changes no test looks at
        with open(root / "shop.py", "a") as f:
            f.write(f"\n\ndef {name}():\n    return '{name}'\n")
        shas.append(commit(root, f"Fix {name}"))
    out = bite(root, "--jobs", "3", "--only", ",".join(shas), env={"CLASH_ID": str(tmp_path.name)})
    assert "3 at a time" in out, out
    for sha in shas:
        assert "NO TEST NOTICED" in line(out, sha), out


def test_a_remembered_check_is_asked_again_once_its_test_is_deleted(tmp_path):
    root = project(tmp_path)
    (root / "shop.py").write_text("def total(xs):\n    return round(sum(xs), 2)\n")
    (root / "tests" / "test_round.py").write_text("import shop\n\n\ndef test_round():\n"
                                                  "    assert shop.total([0.1, 0.2]) == 0.3\n")
    fix = commit(root, "Fix total rounding")
    first = bite(root)
    assert "noticed by test_round" in line(first, fix), first
    again = bite(root)
    assert "checked before with the same tests and settings" in again and "noticed" in line(again, fix), again
    (root / "tests" / "test_round.py").unlink()  # the test that guarded it is deleted later
    commit(root, "tidy tests")
    after = bite(root)
    assert "checked before" not in after, after
    assert "noticed by test_round" not in line(after, fix), after


def test_a_remembered_check_is_asked_again_once_its_test_is_weakened(tmp_path):
    root = project(tmp_path)
    (root / "shop.py").write_text("def total(xs):\n    return round(sum(xs), 2)\n")
    (root / "tests" / "test_round.py").write_text("import shop\n\n\ndef test_round():\n"
                                                  "    assert shop.total([0.1, 0.2]) == 0.3\n")
    fix = commit(root, "Fix total rounding")
    assert "noticed by test_round" in line(bite(root), fix)
    # the test still exists, but no longer checks the rounding the fix added
    (root / "tests" / "test_round.py").write_text("import shop\n\n\ndef test_round():\n"
                                                  "    assert shop.total([1, 2]) == 3\n")
    commit(root, "simplify test")
    after = bite(root)
    assert "checked before" not in after, after  # asked again, not taken from memory
    # and it says what a run with no memory says (Bite checks a fix at its own commit, so a later weakened test
    # doesn't turn it into a gap; the memory must not change that answer either way)
    fresh = bite(root, "--again")
    assert line(after, fix).split()[1:4] == line(fresh, fix).split()[1:4], (after, fresh)


def test_a_new_dependency_version_asks_again(tmp_path):
    root = project(tmp_path)
    (root / "shop.py").write_text("def total(xs):\n    return round(sum(xs), 2)\n")
    (root / "tests" / "test_round.py").write_text("import shop\n\n\ndef test_round():\n"
                                                  "    assert shop.total([0.1, 0.2]) == 0.3\n")
    fix = commit(root, "Fix total rounding")
    bite(root)
    assert "checked before" in bite(root)
    (root / "requirements.txt").write_text("decimal-helpers==2.0\n")
    commit(root, "bump a library")
    assert "checked before" not in bite(root)

def test_a_slow_run_says_what_makes_the_next_one_faster():
    sys.path.insert(0, str(KIT))
    import recent
    from types import SimpleNamespace
    slow = recent.slow_tip(600, 5, SimpleNamespace(test_cmd="python -m pytest -q"))
    assert "about 10 minutes" in slow and "--jobs 4" in slow and "--shard 1/4" in slow and "-n auto" in slow
    assert "-n auto" not in recent.slow_tip(600, 5, SimpleNamespace(test_cmd="python -m pytest -n auto"))
    assert "-n auto" not in recent.slow_tip(600, 5, SimpleNamespace(test_cmd="npm test"))
    assert recent.slow_tip(60, 5, SimpleNamespace(test_cmd="npm test")) == ""


def test_a_slow_step_shows_it_is_still_working(capsys):
    sys.path.insert(0, str(KIT))
    import recent
    import time as t
    with recent.heartbeat(every=0.05):
        t.sleep(0.3)
    out = capsys.readouterr().out
    assert "still working" in out and "$0.00 so far" in out
    with recent.heartbeat(every=0.05):
        pass
    t.sleep(0.2)
    assert "still working" not in capsys.readouterr().out  # it stops when the step is done
