"""Reading failing test names from test output must stay quick on any line (CodeQL alert #3: a pytest line full of
"::" made the old pattern backtrack for ever, so one odd line of output could hang Bite)."""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import recent  # noqa: E402

KIT = Path(__file__).resolve().parent.parent


def test_a_line_full_of_colons_does_not_hang():
    # Run in its own process with a time limit, so a slow pattern fails the test instead of hanging the suite.
    code = "import recent; recent.caught_by('FAILED ' + '::' * 40 + ' ')"
    subprocess.run([sys.executable, "-c", code], cwd=KIT, timeout=10, check=True)


def test_pytest_names_still_read_the_last_part():
    assert recent.caught_by("FAILED tests/t.py::TestA::test_one - assert 1 == 2\n") == "`test_one`"
    assert recent.caught_by("FAILED tests/t.py::test_two[a-b]\n") == "`test_two[a-b]`"
    assert recent.caught_by("ERROR tests/t.py::TestA::TestB::test_three\n") == "`test_three`"
