"""A newcomer reads "a test failed" as bad news. When Bite takes a change out and a test fails, that's the good
result (the test caught it), so wherever Bite says a test failed for a ✅, it says so in the same breath."""

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import live  # noqa: E402

RECENT = str(Path(__file__).resolve().parent.parent / "recent.py")


def test_bite_live_calls_the_failure_good_news():
    line = live.say({"status": "guarded", "code": ["shop.py"], "caught": "`test_total`"})
    assert line.startswith("Bite ✅ a test noticed, good news")
    assert "failed (`test_total`)" in line and "good result" in line


def test_the_demo_says_a_failing_test_is_the_good_result():
    p = subprocess.run([sys.executable, RECENT, "--demo"], capture_output=True, text=True, encoding="utf-8",
                       timeout=300, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    out = p.stdout + p.stderr
    assert "✅ means that with the change taken out, a test failed. That's the good result" in out, out
    report = next(ln for ln in out.splitlines() if "report.html" in ln).split(": ", 1)[1].strip()
    assert "That's the good result: the test caught it" in Path(report).read_text(encoding="utf-8")


def test_a_why_line_drops_taps_escaped_diff_dump():
    # node-semver on CH's Windows PC (11-03): the why: line said "TypeError: LRU is not a constructor\r", with a
    # literal backslash-r, taken from tap's escaped diff dump of the error.
    import recent
    out = ("TypeError: LRU is not a constructor\r\n"
           "            +    TypeError: LRU is not a constructor\\r\r\n"
           "            TypeError: LRU is not a constructor\\r\r\n")
    assert recent.fail_why({"out": out, "why": "exit 1"}) == "TypeError: LRU is not a constructor"
