"""The free check of one commit took over 8 minutes on Bite's own pull request check, with the log quiet after "free
check of 1". Two fixes: with --jobs, a failing test run that had the machine to itself anyway isn't run a second
time, and each test run gets a line in the log saying what it is."""

import os
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import recent  # noqa: E402

RECENT = str(Path(recent.__file__))
GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "commit.gpgsign=false"]


def fake_runs(monkeypatch, secs=0.0):
    calls = []

    def run(fcfg, folder):
        calls.append(folder)
        time.sleep(secs)
        return {"ok": False, "out": "", "why": "a test failed"}
    monkeypatch.setattr(recent.bite, "run_tests", run)
    monkeypatch.setattr(recent, "JOBS", [2])
    return calls


def test_a_failing_run_alone_on_the_machine_is_not_run_twice(monkeypatch):
    calls = fake_runs(monkeypatch)
    assert not recent.run_tests(None, "a")["ok"]
    assert calls == ["a"]


def test_a_failing_run_beside_another_is_run_again_alone(monkeypatch):
    calls = fake_runs(monkeypatch, secs=0.3)
    ts = [threading.Thread(target=recent.run_tests, args=(None, name)) for name in ("a", "b")]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    assert sorted(calls) == ["a", "a", "b", "b"]


def test_a_failing_run_beside_another_can_leave_the_confirming_to_the_next_run(monkeypatch):
    calls = fake_runs(monkeypatch, secs=0.3)
    out = {}
    ts = [threading.Thread(target=lambda n=name: out.update({n: recent.run_tests(None, n, confirm=False)}))
          for name in ("a", "b")]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    assert sorted(calls) == ["a", "b"]  # not run again here: the flaky rerun, alone, confirms it
    assert out["a"]["shared"] and out["b"]["shared"]
    assert not recent.run_tests(None, "c", alone=True)["ok"]
    assert sorted(calls) == ["a", "b", "c"]


def test_the_log_says_what_each_test_run_is():
    root = Path(tempfile.mkdtemp(prefix="bite_progress_"))
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    steps = [("Start", {"price.py": "def total(a, b):\n    return a + b + 1\n",
                        "test_price.py": "from price import total\n\n\ndef test_ok():\n    assert total(1, 1) >= 2\n"}),
             ("Fix total adding one too many", {"price.py": "def total(a, b):\n    return a + b\n",
                                                "test_price.py": "from price import total\n\n\n"
                                                                 "def test_ok():\n    assert total(1, 1) == 2\n"})]
    for subject, files in steps:
        for name, text in files.items():
            (root / name).write_text(text, encoding="utf-8", newline="\n")
        subprocess.run([*GIT, "add", "-A"], cwd=root, check=True)
        subprocess.run([*GIT, "commit", "-q", "-m", subject], cwd=root, check=True)
    p = subprocess.run([sys.executable, RECENT, "--free", "--any"], cwd=root, capture_output=True, text=True,
                       encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    log = p.stdout + p.stderr
    assert "running the tests with the change in..." in log, log
    assert "with the change taken out" in log, log
    assert "once more, to rule out a test that fails by luck" in log, log
