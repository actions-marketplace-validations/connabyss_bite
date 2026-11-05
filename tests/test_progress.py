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


def no_ticker_left():
    """Wait for the "still running" printer of an earlier test's runs to end. Woken as that run ended, it can miss its
    turn on a busy machine (a CI Mac, 2026-11-05) until this test's run has begun: it then keeps waiting out the
    earlier test's 30-second TICK and prints nothing while this test looks for a line."""
    deadline = time.monotonic() + 10
    while recent._TICKER[0] is not None and time.monotonic() < deadline:
        time.sleep(0.01)
    assert recent._TICKER[0] is None, "an earlier test's test run is still going"


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
    p = subprocess.run([sys.executable, RECENT, "--free", "--any", "--verbose"], cwd=root, capture_output=True,
                       text=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    log = p.stdout + p.stderr
    assert "running the tests with the change in..." in log, log
    assert "with the change taken out" in log, log
    assert "a test noticed the change was gone: running them once more to make sure it wasn't luck" in log, log
    # Without --verbose the log is calm (CH, 2026-11-02: "confusing and messy"): no line per test run, only the
    # result of each check.
    calm = subprocess.run([sys.executable, RECENT, "--free", "--any", "--again"], cwd=root, capture_output=True,
                          text=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"}).stdout
    assert "Fix total adding one too many" in calm and "noticed by" in calm, calm
    assert "running the tests with the change" not in calm and "once more" not in calm, calm


def test_a_long_test_run_says_it_is_still_running(monkeypatch, capsys):
    # On CH's PC (2026-11-02) each run of a 34-second suite left the log silent, which looks stuck to a newcomer.
    no_ticker_left()
    fake_runs(monkeypatch, secs=0.35)
    monkeypatch.setattr(recent, "JOBS", [1])
    monkeypatch.setattr(recent, "TICK", 0.1)
    monkeypatch.setattr(recent, "PROGRESS", {"start": time.monotonic(), "done": 0, "total": 0})  # outside a check
    recent.doing({"sha": "abcdef1234"}, "running the tests with the change in...")
    recent.run_tests(None, "a")
    out = capsys.readouterr().out
    assert "still running the tests, under 1 sec so far..." in out, out  # outside the free check (bite live)
    time.sleep(0.3)  # and it stops when the run ends
    assert "still running" not in capsys.readouterr().out


def test_runs_side_by_side_share_one_still_running_line(monkeypatch, capsys):
    # With --jobs 2 each run printed its own line every 30s, interleaved and hard to follow (CH, 2026-11-02).
    both = threading.Barrier(2)

    def run(fcfg, folder):
        both.wait()  # both runs are going on before the first tick (a slow machine starts one late)
        time.sleep(0.6)
        return {"ok": True, "out": "", "why": ""}
    no_ticker_left()
    monkeypatch.setattr(recent.bite, "run_tests", run)
    monkeypatch.setattr(recent, "TICK", 0.25)
    monkeypatch.setattr(recent, "PROGRESS", {"start": time.monotonic(), "done": 1, "total": 4})
    ts = [threading.Thread(target=recent._timed, args=(None, n)) for n in ("a", "b")]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    ticks = [ln.strip() for ln in capsys.readouterr().out.splitlines() if "still" in ln]
    assert ticks and ticks[0].startswith("still checking: 1 of 4 done, "), ticks
    assert len(ticks) <= 3, ticks  # one line per tick for both runs, not one per run


def test_times_are_spelled_out():
    assert recent.spelled(45) == "45 sec" and recent.spelled(210) == "3 min 30 sec" and recent.spelled(120) == "2 min"


def test_the_log_spells_out_times():
    # CH (2026-11-02): "what is 3m". "They took 1m 25s with it in" and "210s, $0.00" now say it in words.
    assert recent.took({"secs": 85}) == "1 min 25 sec"
    src = Path(RECENT).read_text(encoding="utf-8")
    assert "Took {spelled(time.time() - t0)}, spent $" in src
