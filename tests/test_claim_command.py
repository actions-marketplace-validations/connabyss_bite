"""The test Bite or its worker writes runs with the project's own pytest command, minus its folders, plus that one
file. Options keep their values: `-n auto` used to lose its `auto`, so every written test failed to start (#142)."""

import subprocess
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KIT))
import recent  # noqa: E402


class Cfg:
    claim_cmd, contain, box_test_cmd = "", "", ""


def claim(tmp_path, test_cmd):
    (tmp_path / "tests").mkdir(exist_ok=True)
    (tmp_path / "src").mkdir(exist_ok=True)
    Cfg.test_cmd, Cfg.project = test_cmd, tmp_path
    return recent.claim_command(Cfg, "tests/test_bite_claim.py")


def test_options_keep_their_values_and_folders_are_dropped(tmp_path):
    assert claim(tmp_path, "python -m pytest -q -n auto -p no:cacheprovider") == \
        "python -m pytest -q -n auto -p no:cacheprovider tests/test_bite_claim.py"
    assert claim(tmp_path, "python -m pytest -n 4 tests src -k slow --maxfail 2") == \
        "python -m pytest -n 4 -k slow --maxfail 2 tests/test_bite_claim.py"
    assert claim(tmp_path, "pytest . -x tests/test_a.py tests/test_b.py::test_one") == \
        "pytest -x tests/test_bite_claim.py"


def test_a_written_test_runs_under_pytest_xdist(tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_bite_claim.py").write_text("def test_ok():\n    assert True\n")
    cmd = claim(tmp_path, f"{sys.executable} -m pytest -q -n auto -p no:cacheprovider")
    p = subprocess.run(cmd.split(), cwd=tmp_path, capture_output=True, text=True)
    assert p.returncode == 0 and "1 passed" in p.stdout, p.stdout + p.stderr
