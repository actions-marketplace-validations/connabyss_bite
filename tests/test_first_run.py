"""A newcomer's first run on their own small repo, walked through by hand (2026-11-02) before Hack Week. Three dead
ends, each fixed here, and each test failed before its fix. No key, no network.

1. `uvx --from bite-check bite --free` put Bite's own private Python first on PATH, so the tests ran with a Python
   that has no pytest and none of the project's packages: "pytest isn't installed for this Python".
2. A repo whose commits never say "fix" and never added tests ended with "(--any checks them anyway.)", and no
   command to copy.
3. A tiny repo whose few commits changed no code said "Try a larger --last", which can't help: Bite already saw
   every commit there is."""

import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
PY = sys.executable


def git(root, *a):
    return subprocess.run(["git", *a], cwd=root, check=True, capture_output=True, text=True).stdout


def commit(root, msg):
    git(root, "add", "-A")
    git(root, "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", "commit", "-q", "-m", msg)


def bite(root, *args, env=None, py=PY):
    return subprocess.run([py, str(KIT / "recent.py"), *args], cwd=root, capture_output=True, text=True,
                          timeout=300, env=env).stdout


def shop(tmp_path, fix_msg="Fix total rounding"):
    root = tmp_path / "shop"
    (root / "tests").mkdir(parents=True)
    git(root, "init", "-q")
    (root / "shop.py").write_text("def total(xs):\n    return sum(xs)\n")
    (root / "tests" / "test_shop.py").write_text("from shop import total\n\n\ndef test_total():\n"
                                                 "    assert total([1, 2]) == 3\n")
    commit(root, "start")
    (root / "shop.py").write_text("def total(xs):\n    return round(sum(xs), 2)\n")
    commit(root, fix_msg)
    return root


def test_run_through_uvx_uses_the_projects_python_not_bites_own(tmp_path):
    root = shop(tmp_path)
    own = tmp_path / "uv-cache" / "bite-env"  # stands in for uvx's private environment, which has no pytest
    venv.create(own, with_pip=False)
    bin_dir = own / ("Scripts" if os.name == "nt" else "bin")
    own_py = next(p for p in (bin_dir / "python.exe", bin_dir / "python3", bin_dir / "python") if p.exists())
    env = {k: v for k, v in os.environ.items() if k not in ("VIRTUAL_ENV", "PYTHONHOME", "PYTHONPATH")}
    # uvx's PATH: its own bin first, then the user's (here: the Python that has pytest, as the project's would)
    env["PATH"] = os.pathsep.join([str(bin_dir), str(Path(PY).parent), env.get("PATH", "")])
    assert shutil.which("python", path=env["PATH"]) or shutil.which("python3", path=env["PATH"])
    out = bite(root, "--free", env=env, py=str(own_py))
    assert "isn't installed for this Python" not in out, out
    assert "noticed" in out.lower(), out  # the check actually ran the tests


def test_no_claims_and_no_new_tests_gives_the_command_to_check_anyway(tmp_path):
    root = shop(tmp_path, fix_msg="round the total")
    out = bite(root, "--free")
    assert "bite --free --any" in out, out


def test_a_tiny_repo_with_no_code_changes_doesnt_say_try_a_larger_last(tmp_path):
    root = tmp_path / "notes"
    (root / "tests").mkdir(parents=True)
    git(root, "init", "-q")
    (root / "notes.py").write_text("X = 1\n")
    (root / "tests" / "test_notes.py").write_text("def test_x():\n    assert True\n")
    (root / "README.md").write_text("# notes\n")
    commit(root, "start")
    (root / "README.md").write_text("# my notes\n")
    commit(root, "Fix the title")
    out = bite(root, "--free")
    assert "Try a larger --last" not in out and "every commit in this repository" in out, out


def test_the_package_name_is_also_a_command_so_uvx_bite_check_works():
    # `uvx bite-check --free` and `pipx run bite-check --free` look for a command named after the package.
    import re
    scripts = (KIT / "pyproject.toml").read_text(encoding="utf-8").split("[project.scripts]", 1)[1].split("\n[", 1)[0]
    assert re.search(r'^bite-check = "recent:main"', scripts, re.M), scripts
