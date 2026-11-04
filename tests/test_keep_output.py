"""The eemeli/yaml hunt: there was no way to see what the tests printed in a check, so hand-checking how Bite read
a run needed a wrapper around the test command. --keep-output now saves each commit's test output, with the change
in and taken out, in bite_proof/output/<commit>.txt. No key, no network."""

import os
import subprocess
import sys
from pathlib import Path

RECENT = str(Path(__file__).resolve().parent.parent / "recent.py")
GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"]


def test_keep_output_saves_what_the_tests_printed(tmp_path):
    root = tmp_path / "shop"
    root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    (root / "shop.py").write_text("def total(xs):\n    return sum(xs)\n")
    (root / ".bite.ini").write_text(f'[bite]\ntest_command = "{sys.executable}" -m pytest -q -p no:cacheprovider\n')
    subprocess.run([*GIT, "add", "-A"], cwd=root, check=True)
    subprocess.run([*GIT, "commit", "-q", "-m", "Start"], cwd=root, check=True)
    (root / "shop.py").write_text("def total(xs):\n    return round(sum(xs), 2)\n")
    (root / "test_total.py").write_text("from shop import total\n\n\ndef test_rounds_to_cents():\n"
                                        "    assert total([0.1, 0.2]) == 0.3\n")
    subprocess.run([*GIT, "add", "-A"], cwd=root, check=True)
    subprocess.run([*GIT, "commit", "-q", "-m", "Fix total rounding"], cwd=root, check=True)
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True).stdout.strip()
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    p = subprocess.run([sys.executable, RECENT, "--free", "--keep-output"], cwd=root, capture_output=True, text=True,
                       encoding="utf-8", timeout=300, env=env)
    saved = root / "bite_proof" / "output" / f"{sha[:8]}.txt"
    assert saved.exists(), p.stdout + p.stderr
    text = saved.read_text(encoding="utf-8")
    assert "===== the tests with the change in: passed =====" in text, text
    assert "taken out" in text and "test_rounds_to_cents" in text, text
    # Without the flag, nothing extra is kept.
    saved.unlink()
    subprocess.run([sys.executable, RECENT, "--free", "--again"], cwd=root, capture_output=True, text=True,
                   encoding="utf-8", timeout=300, env=env)
    assert not saved.exists()
