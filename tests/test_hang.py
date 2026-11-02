"""A fix that bounds a loop: with it taken out, the tests hang. That is the tests noticing, and Bite should say so
in about a minute, not wait out test_timeout (10 minutes) for every run of the check. Found on Scrapling, whose
"bound Cloudflare solver loops" fix stalled a free check for 25 minutes."""

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import bite  # noqa: E402
import live  # noqa: E402
import recent  # noqa: E402

HERE = str(Path(recent.__file__).resolve().parent)
GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "commit.gpgsign=false"]

LOOP = '''def first_ready(flags):
    i = 0
    while not flags[i % len(flags)]:
        i += 1
    return i % len(flags)
'''
BOUNDED = '''def first_ready(flags):
    for i, ok in enumerate(flags):
        if ok:
            return i
    return None
'''
TEST = ("from waiter import first_ready\n\n\ndef test_nothing_ready():\n    assert first_ready([False, False]) is None\n\n\n"
        "def test_second_ready():\n    assert first_ready([False, True]) == 1\n")
# Without the fix the hung run waits out this limit, so the time check below fails in two minutes, not ten.
SETTINGS = "[bite]\ntest_command = python -m pytest -q -p no:cacheprovider\ntest_timeout_seconds = 120\n"


def project() -> Path:
    root = Path(tempfile.mkdtemp(prefix="bite_hang_"))
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    steps = [("Start", {"waiter.py": LOOP, ".bite.ini": SETTINGS}),
             ("Fix first_ready looping forever when nothing is ready", {"waiter.py": BOUNDED, "test_waiter.py": TEST})]
    for subject, files in steps:
        for name, text in files.items():
            (root / name).write_text(text, encoding="utf-8", newline="\n")
        subprocess.run([*GIT, "add", "-A"], cwd=root, check=True)
        subprocess.run([*GIT, "commit", "-q", "-m", subject], cwd=root, check=True)
    return root


# A floor of 3 seconds instead of 60, so the test is quick; the rule (5 times the passing run) is the real one.
RUN = ("import sys; sys.path.insert(0, sys.argv[1]); import bite; bite.HANG_FLOOR = 3; import recent; "
       "sys.exit(recent.main(['--free', '--any', '--quick', '--json']))")


def test_a_hang_with_the_fix_taken_out_counts_as_noticed_and_stops_early():
    root = project()
    start = time.monotonic()
    p = subprocess.run([sys.executable, "-c", RUN, HERE], cwd=root, capture_output=True, text=True,
                       encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    took = time.monotonic() - start
    assert p.stdout.strip(), p.stderr
    r = next(c for c in json.loads(p.stdout)["commits"] if c["subject"].startswith("Fix first_ready"))
    assert r["result"] == "noticed", r
    assert "your tests hang" in r["detail"], r
    assert took < 90, f"the hung run was not stopped early: {took:.0f}s"


def test_the_cap_follows_the_passing_run():
    cfg = type("Cfg", (), {"test_timeout": 600})()
    assert bite.run_limit(cfg) == 600
    bite.cap_hang(cfg, {"secs": 2.0})
    assert bite.run_limit(cfg) == bite.HANG_FLOOR  # a quick suite: the floor
    bite.cap_hang(cfg, {"secs": 40.0})
    assert bite.run_limit(cfg) == 201
    bite.cap_hang(cfg, {"secs": 500.0})
    assert bite.run_limit(cfg) == 600  # never longer than test_timeout


def test_the_live_check_stops_a_hang_early_too(monkeypatch):
    root = project()
    monkeypatch.setattr(bite, "HANG_FLOOR", 3)
    subprocess.run([*GIT, "reset", "-q", "--soft", "HEAD~1"], cwd=root, check=True)  # the fix, not committed yet
    start = time.monotonic()
    r = live.check(root)
    assert r["status"] == "guarded", r
    assert r["hang"].startswith("stopped after"), r
    assert "they hang" in live.say(r)
    assert time.monotonic() - start < 90
