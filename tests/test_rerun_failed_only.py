"""CH's run on Bite's own repo took 3.5 minutes for 2 commits: the whole suite ran 8 times. The luck check (run the
tests once more with the change out) and the piece check (each piece of a commit taken out alone) ran the whole
suite each time. With pytest they now run only the tests that noticed the change, and the whole suite only when
those pass. No key, no network."""

import os
import subprocess
import sys
from pathlib import Path

RECENT = str(Path(__file__).resolve().parent.parent / "recent.py")
GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"]


def repo(root, start, fix, tests):
    root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    for msg, files in (("Start", {"shop.py": start, **tests}), ("Fix total and tidy the label", {"shop.py": fix})):
        for name, text in files.items():
            (root / name).write_text(text, encoding="utf-8", newline="\n")
        subprocess.run([*GIT, "add", "-A"], cwd=root, check=True)
        subprocess.run([*GIT, "commit", "-q", "-m", msg], cwd=root, check=True)
    (root / ".bite.ini").write_text(f'[bite]\ntest_command = "{sys.executable}" -m pytest -q -p no:cacheprovider\n')
    return root


def bite(root):
    p = subprocess.run([sys.executable, RECENT, "--free", "--json"], cwd=root, capture_output=True, text=True,
                       encoding="utf-8", timeout=300, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    import json
    return json.loads(p.stdout)["commits"][0], p.stderr


START = "def total(xs):\n    return sum(xs)\n\n\ndef label(x):\n    return str(x)\n"
FIX = "def total(xs):\n    return round(sum(xs), 2)\n\n\ndef label(x):\n    return str(x).strip()\n"


def test_the_slow_tests_run_only_with_the_change_in_and_out(tmp_path):
    runs = tmp_path / "slow_runs.txt"
    root = repo(tmp_path / "shop", START, FIX, {
        "test_total.py": "from shop import total, label\n\n\ndef test_total():\n    assert total([0.1, 0.2]) == 0.3\n\n\n"
                         "def test_label():\n    assert label(' a ') == 'a'\n",
        "test_slow.py": f"def test_slow():\n    with open({str(runs)!r}, 'a') as f:\n        f.write('x')\n"})
    c, log = bite(root)
    assert c["result"] == "noticed", (c, log)
    # Before: with the change in, out, the luck check, and the 2 pieces: 5 whole-suite runs. Now 2.
    assert runs.read_text() == "xx", (runs.read_text(), log)


def test_a_test_that_fails_on_its_own_cant_vouch_for_a_piece(tmp_path):
    # test_total needs test_a_setup to run first, so on its own it always fails. Run alone, it would seem to notice
    # every piece, and hide that nothing tests the label change. Bite sees it fail with the change in too, and lets
    # the whole suite decide.
    root = repo(tmp_path / "shop", START, FIX, {
        "test_shop.py": "import shop\nfrom shop import total\n\n\ndef test_a_setup():\n    shop.ready = True\n\n\n"
                        "def test_total():\n    assert getattr(shop, 'ready', False)\n"
                        "    assert total([0.1, 0.2]) == 0.3\n"})
    c, log = bite(root)
    assert c["result"] == "no_test_noticed" and "label" in str(c), (c, log)
