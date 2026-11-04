"""A newcomer opens a terminal and pastes the one line from the README (2026-11-02, on Windows). The terminal opens in
C:\\WINDOWS\\system32, not in a project, and Bite only said "not inside a git repository": a dead end for someone who
doesn't know what cd or a git repository is. Now a run outside a project shows the demo and says how to point Bite at
a project (drag its folder into the window), Bite takes that folder as an argument, and `python -m bite_check` runs
Bite with nothing but Python and pip, when the `bite` command isn't on PATH. No key, no network."""

import os
import subprocess
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent


def run(cwd, *args, module=False):
    cmd = [sys.executable, "-m", "bite_check", *args] if module else [sys.executable, str(KIT / "recent.py"), *args]
    env = {**os.environ, "PYTHONPATH": str(KIT)} if module else None
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", timeout=300, env=env)


def git(root, *a):
    subprocess.run(["git", *a], cwd=root, check=True, capture_output=True)


def shop(root):
    root.mkdir()
    git(root, "init", "-q")
    (root / "shop.py").write_text("def total(xs):\n    return sum(xs)\n")
    (root / "test_shop.py").write_text("import unittest\nfrom shop import total\n\n\nclass T(unittest.TestCase):\n"
                                       "    def test_total(self):\n        self.assertEqual(total([1, 2]), 3)\n")
    (root / ".bite.ini").write_text(f'[bite]\ntest_command = "{sys.executable}" -m unittest\n')
    for msg in ("start", "Fix total rounding"):
        if msg != "start":
            (root / "shop.py").write_text("def total(xs):\n    return round(sum(xs), 2)\n")
        git(root, "add", "-A")
        git(root, "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", "commit", "-q", "-m", msg)
    return root


def test_outside_a_project_shows_the_demo_and_how_to_check_your_own(tmp_path):
    p = run(tmp_path, "--free")
    assert p.returncode == 0, p.stdout + p.stderr
    assert "isn't a project with git history" in p.stdout
    assert "NO TEST NOTICED" in p.stdout and "noticed by test_discount_never_below_zero" in p.stdout
    assert "drag your project's folder into this" in p.stdout


def test_a_folder_argument_checks_that_project_without_cd(tmp_path):
    root = shop(tmp_path / "my shop")  # a space in the name, as a dragged Windows path often has
    p = run(tmp_path, "--free", str(root))
    assert p.returncode == 0, p.stdout + p.stderr
    assert "Fix total rounding" in p.stdout and "demo" not in p.stdout.lower()
    assert (root / "bite_proof" / "report.html").is_file()
    quoted = run(tmp_path, f'"{root}"', "--free")  # a drop that keeps its quotes
    assert quoted.returncode == 0 and "Fix total rounding" in quoted.stdout, quoted.stdout


def test_a_folder_that_isnt_a_project_says_so_plainly(tmp_path):
    (tmp_path / "photos").mkdir()
    p = run(tmp_path, "--free", str(tmp_path / "photos"))
    assert p.returncode == 1 and "isn't a project with git history" in p.stdout and "demo" not in p.stdout.lower()


def test_python_m_bite_check_runs_bite_and_ignores_the_projects_own_same_named_files(tmp_path):
    root = shop(tmp_path / "shop")
    (root / "recent.py").write_text("raise SystemExit('the project\\'s own recent.py was imported')\n")
    p = run(root, "--free", module=True)
    assert p.returncode == 0, p.stdout + p.stderr
    assert "Fix total rounding" in p.stdout
    assert "bite_check" in (KIT / "pyproject.toml").read_text(encoding="utf-8").split("py-modules", 1)[1].split("\n")[0]


def test_how_called_names_the_command_a_person_typed(monkeypatch):
    sys.path.insert(0, str(KIT))
    import recent
    for exe, argv0, want in [
        ("C:\\Users\\a\\AppData\\Local\\pipx\\pipx\\.cache\\1f2e\\Scripts\\python.exe", "C:\\x\\Scripts\\bite-check.exe",
         "pipx run bite-check"),
        ("C:\\Users\\a\\AppData\\Local\\uv\\cache\\archive-v0\\abc\\Scripts\\python.exe", "bite-check", "uvx bite-check"),
        ("/usr/bin/python3", "/home/a/.local/bin/bite", "bite"),
        ("/usr/bin/python3", "/site-packages/bite_check.py", "python -m bite_check"),
    ]:
        monkeypatch.setattr(sys, "executable", exe)
        monkeypatch.setattr(sys, "argv", [argv0])
        assert recent.how_called() == want, (exe, argv0)
