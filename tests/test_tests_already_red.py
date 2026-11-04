"""On validator.js, Bite ran 40 checks against a suite that failed before it changed anything (the test command
skipped a build step), and only said "tests failed here" 40 times. Now, when the first 2 commits it checks fail
with nothing taken out and the tests fail on the newest commit too, Bite stops and says so once. When the newest
commit's tests pass (a later commit fixed them), it goes on checking as before. No key, no network."""

import json
import os
import subprocess
import sys
from pathlib import Path

RECENT = str(Path(__file__).resolve().parent.parent / "recent.py")
GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"]


def repo(root, runs, fixed_at_the_end=False):
    root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    # The test needs a file a build step would make (built.py): Bite's copies don't have it, so every run fails.
    test = (f"def test_shop():\n    with open({str(runs)!r}, 'a') as f:\n        f.write('x')\n"
            "    import built  # noqa: F401\n    from shop import total\n    assert total([1]) == 1\n")
    steps = [("Start", {"shop.py": "def total(xs):\n    return sum(xs)\n", "test_shop.py": test})]
    for i in range(8):
        steps.append((f"Fix total rounding, case {i}", {"shop.py": f"def total(xs):\n    return round(sum(xs), {i + 2})\n"}))
    if fixed_at_the_end:
        steps.append(("Add the built module", {"built.py": "X = 1\n"}))
    for msg, files in steps:
        for name, text in files.items():
            (root / name).write_text(text, encoding="utf-8", newline="\n")
        subprocess.run([*GIT, "add", "-A"], cwd=root, check=True)
        subprocess.run([*GIT, "commit", "-q", "-m", msg], cwd=root, check=True)
    (root / ".bite.ini").write_text(f'[bite]\ntest_command = "{sys.executable}" -m pytest -q -p no:cacheprovider\n')
    return root


def bite(root):
    p = subprocess.run([sys.executable, RECENT, "--free", "--json"], cwd=root, capture_output=True, text=True,
                       encoding="utf-8", timeout=300, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    return json.loads(p.stdout)["commits"], p.stderr


def test_bite_stops_when_the_tests_already_fail_today(tmp_path):
    runs = tmp_path / "runs.txt"
    commits, log = bite(repo(tmp_path / "shop", runs))
    assert "Your tests already fail before Bite changes anything, on the newest commit too" in log, log
    assert "instead of checking the other 4" in log and "Bite ran: " in log, log
    # 2 commits (each run twice, in case a failure was luck) and the newest one; before, all 6 Bite checks by default.
    assert len(runs.read_text()) == 5, (runs.read_text(), log)
    checked = [c for c in commits if c.get("result")]
    assert len(checked) == 2 and all(c["result"] == "tests_fail" for c in checked), commits


def test_bite_goes_on_when_a_later_commit_fixed_the_tests(tmp_path):
    runs = tmp_path / "runs.txt"
    commits, log = bite(repo(tmp_path / "shop", runs, fixed_at_the_end=True))
    assert "already fail before Bite changes anything" not in log, log
    assert len([c for c in commits if c.get("result")]) == 6, commits  # all 6 it checks by default, as before
