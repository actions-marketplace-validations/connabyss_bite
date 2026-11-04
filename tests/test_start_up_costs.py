"""Every Bite run, and every test that starts one, paid for things it didn't use (2026-11-04): asyncio was imported
at start-up (2/3 of Bite's start-up time; only the paid step needs it), and the reruns of a few tests started all of
pytest-xdist's workers (-n auto) for one or two tests. No key, no network."""

import subprocess
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KIT))
import recent  # noqa: E402
import repo  # noqa: E402


def test_starting_bite_doesnt_import_asyncio():
    out = subprocess.run([sys.executable, "-c", "import sys, recent; print('asyncio' in sys.modules)"], cwd=KIT,
                         capture_output=True, text=True, check=True).stdout
    assert out.strip() == "False"


def test_a_few_tests_rerun_in_one_process():
    assert recent.one_process("python -m pytest -q -n auto -p no:cacheprovider tests/a.py") == \
        "python -m pytest -q -p no:cacheprovider tests/a.py"
    for cmd in ("pytest -n 4 --dist loadfile x.py", "pytest -nauto x.py", "pytest --numprocesses=3 x.py",
                "pytest -n=2 --dist=worksteal x.py"):
        assert recent.one_process(cmd) == "pytest x.py", cmd
    assert recent.one_process("pytest -q x.py") == "pytest -q x.py"  # nothing to drop
    assert recent.one_process("npm test -- -n 3") == "npm test -- -n 3"  # not pytest: left alone


def project(tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_a.py").write_text("def test_x():\n    assert True\n")
    (tmp_path / ".bite.ini").write_text(f"[bite]\ntest_command = {sys.executable} -m pytest -q -n auto tests\n")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    cfg = repo.load_cfg(tmp_path)
    return recent.at(cfg, tmp_path)


def test_the_commits_own_tests_run_without_xdist(tmp_path):
    fcfg = project(tmp_path)
    own = recent.own_tests(fcfg, tmp_path, {"test_code": ["tests/test_a.py"]})
    assert "tests/test_a.py" in own.test_cmd and " -n " not in f" {own.test_cmd} ", own.test_cmd


def test_the_tests_that_failed_rerun_without_xdist(tmp_path):
    fcfg = project(tmp_path)
    sub = recent.failed_only(fcfg, tmp_path, "FAILED tests/test_a.py::test_x - assert False\n1 failed in 0.1s\n")
    assert sub is not None and "test_x" in sub.test_cmd and " -n " not in f" {sub.test_cmd} ", sub.test_cmd
