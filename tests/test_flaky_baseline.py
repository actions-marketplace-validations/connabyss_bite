"""h2's Hypothesis test failed once on Bite's cold copy, so 2 commits showed as "tests already fail" and were
skipped, though the tests passed on every run after. Now when the tests fail with nothing taken out, Bite runs
them once more before giving up on that commit. No key, no network."""

import json
import os
import subprocess
import sys
from pathlib import Path

RECENT = str(Path(__file__).resolve().parent.parent / "recent.py")
GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"]


def test_a_baseline_that_fails_once_by_luck_is_run_again(tmp_path):
    marker = tmp_path / "ran_once"
    root = tmp_path / "shop"
    root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    flaky = (f"import os\n\n\ndef test_flaky():\n    if not os.path.exists({str(marker)!r}):\n"
             f"        open({str(marker)!r}, 'w').close()\n        assert False, 'cold start'\n")
    total = "from shop import total\n\n\ndef test_total():\n    assert total([0.1, 0.2]) == 0.3\n"
    steps = [("Start", {"shop.py": "def total(xs):\n    return sum(xs)\n", "test_flaky.py": flaky}),
             ("Fix total rounding", {"shop.py": "def total(xs):\n    return round(sum(xs), 2)\n", "test_total.py": total})]
    for msg, files in steps:
        for name, text in files.items():
            (root / name).write_text(text, encoding="utf-8", newline="\n")
        subprocess.run([*GIT, "add", "-A"], cwd=root, check=True)
        subprocess.run([*GIT, "commit", "-q", "-m", msg], cwd=root, check=True)
    (root / ".bite.ini").write_text(f'[bite]\ntest_command = "{sys.executable}" -m pytest -q -p no:cacheprovider\n')
    p = subprocess.run([sys.executable, RECENT, "--free", "--json"], cwd=root, capture_output=True, text=True,
                       encoding="utf-8", timeout=300, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    c = json.loads(p.stdout)["commits"][0]
    assert c["result"] == "noticed", (c, p.stderr)
