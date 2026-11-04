"""Bite's check on its own pull requests took 13 minutes for 3 commits: for each one the whole suite ran with the
change in, then again with it taken out. A commit that brings its own test is now checked with that test first:
when it fails with the change out, fails again, and passes with the change back in, the change is noticed, and
the whole suite runs only once (with the change in, to know the tests pass there). When the commit's own tests
don't notice it, the whole suite decides as before. No key, no network."""

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import recent  # noqa: E402

RECENT = str(Path(__file__).resolve().parent.parent / "recent.py")
GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"]
START = "def total(xs):\n    return sum(xs)\n"
FIX = "def total(xs):\n    return round(sum(xs), 2)\n"


def repo(root, slow_runs, fix_files, ini=""):
    root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    start = {"shop.py": START, "test_slow.py": f"def test_slow():\n    with open({str(slow_runs)!r}, 'a') as f:\n"
                                               "        f.write('x')\n"}
    for msg, files in (("Start", start), ("Fix total rounding", {"shop.py": FIX, **fix_files})):
        for name, text in files.items():
            (root / name).parent.mkdir(parents=True, exist_ok=True)
            (root / name).write_text(text, encoding="utf-8", newline="\n")
        subprocess.run([*GIT, "add", "-A"], cwd=root, check=True)
        subprocess.run([*GIT, "commit", "-q", "-m", msg], cwd=root, check=True)
    (root / ".bite.ini").write_text(ini or f'[bite]\ntest_command = "{sys.executable}" -m pytest -q -p no:cacheprovider\n')
    return root


def bite(root):
    p = subprocess.run([sys.executable, RECENT, "--free", "--json"], cwd=root, capture_output=True, text=True,
                       encoding="utf-8", timeout=300, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    return json.loads(p.stdout)["commits"][0], p.stderr


OWN = "from shop import total\n\n\ndef test_total():\n    assert total([0.1, 0.2]) == 0.3\n"


def test_the_whole_suite_runs_once_when_the_commits_own_test_notices(tmp_path):
    runs = tmp_path / "slow_runs.txt"
    c, log = bite(repo(tmp_path / "shop", runs, {"test_total.py": OWN}))
    assert c["result"] == "noticed" and "test_total" in str(c), (c, log)
    assert runs.read_text() == "x", (runs.read_text(), log)  # with the change in only; before, out too


def test_the_whole_suite_decides_when_the_commits_own_test_doesnt_notice(tmp_path):
    runs = tmp_path / "slow_runs.txt"
    weak = "from shop import total\n\n\ndef test_total():\n    assert total([1]) == 1\n"
    c, log = bite(repo(tmp_path / "shop", runs, {"test_total.py": weak}))
    assert c["result"] == "its_tests_didnt_notice", (c, log)
    assert runs.read_text() == "xx", (runs.read_text(), log)


def test_an_own_test_that_fails_on_its_own_cant_vouch(tmp_path):
    # The commit's test needs a fixture that only another file sets up, so alone it fails with the change in too.
    # It mustn't count as noticing: the whole suite runs with the change out, and it passes there.
    runs = tmp_path / "slow_runs.txt"
    needy = ("import shop\n\n\ndef test_total():\n    assert getattr(shop, 'ready', False)\n"
             "    assert shop.total([1]) == 1\n")
    files = {"test_a_setup.py": "import shop\n\n\ndef test_setup():\n    shop.ready = True\n", "test_total.py": needy}
    c, log = bite(repo(tmp_path / "shop", runs, files))
    assert c["result"] == "its_tests_didnt_notice", (c, log)


def test_only_files_the_projects_own_command_runs(tmp_path):
    folder = tmp_path
    for f in ("tests/unit/test_a.py", "other/test_b.py", "tests/selftest.py"):
        (folder / f).parent.mkdir(parents=True, exist_ok=True)
        (folder / f).write_text("")

    class Cfg:
        contain = ""
        box_test_cmd = ""
        project = folder
    fcfg = Cfg()
    fcfg.test_cmd = "python -m pytest -q tests"
    assert "tests/unit/test_a.py" in recent.own_tests(fcfg, folder, {"test_code": ["tests/unit/test_a.py"]}).test_cmd
    assert recent.own_tests(fcfg, folder, {"test_code": ["other/test_b.py"]}) is None  # outside what it runs
    assert recent.own_tests(fcfg, folder, {"test_code": ["tests/selftest.py"]}) is None  # not a pytest file name
    fcfg.test_cmd = "python -m pytest -q"
    (folder / "pyproject.toml").write_text('[tool.pytest.ini_options]\ntestpaths = ["tests"]\n')  # Bite's own
    assert recent.own_tests(fcfg, folder, {"test_code": ["tests/unit/test_a.py"]}) is not None
    assert recent.own_tests(fcfg, folder, {"test_code": ["other/test_b.py"]}) is None  # outside testpaths
    (folder / "pytest.ini").write_text("[pytest]\ntestpaths = tests/*\n")
    assert recent.own_tests(fcfg, folder, {"test_code": ["tests/unit/test_a.py"]}) is None  # a pattern: unclear
    fcfg.test_cmd = "npm test"
    assert recent.own_tests(fcfg, folder, {"test_code": ["test_a.py"]}) is None
