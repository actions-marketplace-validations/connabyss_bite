"""A folder argument that doesn't exist was reported as "unknown option", which sends a newcomer looking at
Bite's flags instead of their path. Name the missing folder and the two things that fix it."""

import subprocess
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
RECENT = str(KIT / "recent.py")


def test_a_missing_folder_is_not_called_an_unknown_option(tmp_path):
    missing = tmp_path / "no-such-dir"
    p = subprocess.run([sys.executable, RECENT, "--free", str(missing)], cwd=tmp_path, capture_output=True,
                       text=True, timeout=300)
    out = p.stdout + p.stderr
    assert p.returncode == 2, out
    assert f"Bite: there's no folder at {missing}." in out, out
    assert "Check the path, or drag the folder into this window to type it." in out, out
    assert "unknown option" not in out, out


def test_a_flag_typo_still_says_unknown_option(tmp_path):
    p = subprocess.run([sys.executable, RECENT, "--free", "--no-such-flag"], cwd=tmp_path, capture_output=True,
                       text=True, timeout=300)
    out = p.stdout + p.stderr
    assert p.returncode == 2, out
    assert "unknown option '--no-such-flag'" in out, out
    assert "Did you mean" not in out, out


def test_a_close_flag_typo_suggests_the_right_option(tmp_path):
    p = subprocess.run([sys.executable, RECENT, "--free", "--frees"], cwd=tmp_path, capture_output=True,
                       text=True, timeout=300)
    out = p.stdout + p.stderr
    assert p.returncode == 2, out
    assert "Bite: unknown option '--frees'. Did you mean --free? Run bite --help for the options." in out, out
