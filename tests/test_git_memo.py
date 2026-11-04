"""Fewer process starts (2026-11-04): Bite asked git the same question about a fixed commit up to 7 times in one
run, and every git start costs tens of milliseconds on Windows. Questions about full commit ids are answered once;
anything that can move (HEAD, a branch, the working tree) is still asked every time. No key, no network."""

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import repo  # noqa: E402


def make(tmp_path):
    g = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"]
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "a.py").write_text("x = 1\n")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run([*g, "commit", "-qm", "one"], cwd=tmp_path, check=True)
    return repo.git(tmp_path, "rev-parse", "HEAD")


def counting(monkeypatch):
    calls = []
    real = subprocess.run

    def run(args, *a, **k):
        calls.append(list(args))
        return real(args, *a, **k)
    monkeypatch.setattr(repo.subprocess, "run", run)
    return calls


def test_a_question_about_a_fixed_commit_starts_git_once(tmp_path, monkeypatch):
    sha = make(tmp_path)
    calls = counting(monkeypatch)
    for _ in range(3):
        assert repo.git(tmp_path, "cat-file", "blob", f"{sha}:a.py") == "x = 1"
        assert repo.git(tmp_path, "diff-tree", "--no-commit-id", "-r", sha) is not None
    assert len(calls) == 2, calls


def test_questions_about_things_that_move_are_asked_every_time(tmp_path, monkeypatch):
    sha = make(tmp_path)
    calls = counting(monkeypatch)
    assert repo.git(tmp_path, "show", "HEAD:a.py") == "x = 1"
    (tmp_path / "a.py").write_text("x = 2\n")
    assert repo.git(tmp_path, "diff", sha, "--", "a.py")  # against the working tree: changed since
    (tmp_path / "a.py").write_text("x = 1\n")
    assert repo.git(tmp_path, "diff", sha, "--", "a.py") == ""  # and back
    (tmp_path / "a.py").write_text("x = 2\n")
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false",
                    "commit", "-qam", "two"], cwd=tmp_path, check=True)
    assert repo.git(tmp_path, "show", "HEAD:a.py") == "x = 2"  # a new answer once HEAD moved
    assert len([c for c in calls if c[1] != "-c"]) == 4, calls  # every one asked


def test_the_practice_projects_pytest_runs_load_no_plugins():
    # set for this suite by conftest.py: each practice pytest start skips importing pytest-xdist and other plugins
    assert os.environ.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD") == "1"


def test_a_failed_question_is_asked_again(tmp_path, monkeypatch):
    sha = make(tmp_path)
    objects = tmp_path / ".git" / "objects"
    hidden = tmp_path / "objects_away"
    objects.rename(hidden)  # git can't read for a moment (an antivirus scan, a network drive hiccup)
    assert repo.git(tmp_path, "cat-file", "blob", f"{sha}:a.py") is None
    hidden.rename(objects)
    assert repo.git(tmp_path, "cat-file", "blob", f"{sha}:a.py") == "x = 1"


def test_a_range_is_never_kept():
    sha = "a" * 40
    assert repo.fixed(("diff-tree", sha))
    assert not repo.fixed(("show", f"{sha}..main"))  # main can move
