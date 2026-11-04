"""A fast run printed "they took 0 sec with it in" and "Took 0 sec", which reads as if no time passed. Say
"under 1 sec" below one second, and keep the existing rounding above it."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import recent  # noqa: E402


def test_a_sub_second_time_is_under_one_second_not_zero():
    assert recent.spelled(0) == "under 1 sec"
    assert recent.spelled(0.2) == "under 1 sec"
    assert recent.spelled(0.999) == "under 1 sec"


def test_a_full_second_still_reads_as_seconds():
    assert recent.spelled(1) == "1 sec"
    assert recent.spelled(1.4) == "1 sec"
    assert recent.spelled(59.4) == "59 sec"
    assert recent.spelled(60) == "1 min"
    assert recent.spelled(90) == "1 min 30 sec"
