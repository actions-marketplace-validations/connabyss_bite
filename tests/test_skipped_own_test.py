"""markedjs/marked e7c4f64c fixed --no-clobber and added the one test that can tell old code from new, with
{ skip: process.platform === 'win32' }. On Windows that test was skipped, so with the fix taken out every test
still passed, and Bite said "its tests didn't notice". Now a test the commit added that was skipped in the run is
named instead: it couldn't notice here. No key, no network."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import recent  # noqa: E402

RECENT = str(Path(__file__).resolve().parent.parent / "recent.py")
GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"]
NODE_OUT = """▶ bin
  ✔ writes the output file (1.2ms)
  ﹣ does not follow an existing dangling symlink with --no-clobber (0.6826ms) # SKIP
✔ bin (3.1ms)
ℹ tests 2
ℹ skipped 1
"""


def test_the_skipped_tests_are_read_by_name():
    names = [next(g for g in m.groups() if g) for m in recent.SKIPPED_TEST.finditer(NODE_OUT)]
    assert names == ["does not follow an existing dangling symlink with --no-clobber"]
    tap = "ok 3 - rounds to cents # SKIP not on windows\n--- SKIP: TestRounds (0.00s)\ntest tests::rounds ... ignored\n"
    assert [next(g for g in m.groups() if g) for m in recent.SKIPPED_TEST.finditer(tap)] == \
        ["rounds to cents", "TestRounds", "rounds"]


@pytest.mark.skipif(not shutil.which("node"), reason="needs node")
def test_a_fix_whose_own_test_is_skipped_here_is_not_called_unnoticed(tmp_path):
    root = tmp_path / "shop"
    (root / "test").mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    (root / "package.json").write_text('{"name": "shop", "scripts": {"test": "node --test"}}\n')
    (root / "shop.js").write_text("exports.total = (xs) => xs.reduce((a, b) => a + b, 0);\n")
    (root / "test" / "other.test.js").write_text(
        "const { it } = require('node:test');\nit('runs', () => {});\n")
    subprocess.run([*GIT, "add", "-A"], cwd=root, check=True)
    subprocess.run([*GIT, "commit", "-q", "-m", "Start"], cwd=root, check=True)
    (root / "shop.js").write_text("exports.total = (xs) => Math.round(xs.reduce((a, b) => a + b, 0) * 100) / 100;\n")
    (root / "test" / "shop.test.js").write_text(
        "const { it } = require('node:test');\nconst assert = require('node:assert');\nconst { total } = require('../shop');\n"
        f"it('rounds totals to cents', {{ skip: process.platform === '{sys.platform}' }}, () => {{\n"
        "  assert.strictEqual(total([0.1, 0.2]), 0.3);\n});\n")
    subprocess.run([*GIT, "add", "-A"], cwd=root, check=True)
    subprocess.run([*GIT, "commit", "-q", "-m", "Fix total rounding"], cwd=root, check=True)
    p = subprocess.run([sys.executable, RECENT, "--free", "--json"], cwd=root, capture_output=True, text=True,
                       encoding="utf-8", timeout=300, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    c = json.loads(p.stdout)["commits"][0]
    assert c["result"] == "skipped" and "rounds totals to cents" in c["label"] + str(c), (c, p.stderr)


def test_a_subtest_added_inside_a_skipped_parent_counts_as_skipped(tmp_path):
    # dotenv 7c675904 (11-03, CH's Windows PC): the commit added a subtest inside the existing
    # t.test('POSIX signal forwarding', { skip: process.platform === 'win32' }). tap prints only the parent,
    # "ok 1 - POSIX signal forwarding # SKIP", so the subtest's own name never shows.
    root = tmp_path / "cli"
    (root / "tests").mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    head = "const t = require('tap')\n\n"
    parent = ("t.test('POSIX signal forwarding', { skip: process.platform === 'win32' }, async ct => {\n"
              "  ct.test('forwards SIGTERM', async () => {})\n")
    tail = "})\n\nt.test('reads the file', async () => {})\n"
    f = root / "tests" / "test-cli-signals.js"
    f.write_text(head + parent + tail)
    subprocess.run([*GIT, "add", "-A"], cwd=root, check=True)
    subprocess.run([*GIT, "commit", "-q", "-m", "start"], cwd=root, check=True)
    f.write_text(head + parent + "  ct.test('exits when the command dies from a signal', async () => {})\n" + tail)
    subprocess.run([*GIT, "commit", "-qam", "fix(cli): exit when the command dies from SIGPIPE"], cwd=root, check=True)
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True).stdout.strip()
    c = {"sha": sha, "test_code": ["tests/test-cli-signals.js"]}
    out = "    ok 1 - POSIX signal forwarding # SKIP\n    ok 2 - reads the file\n# { total: 2, pass: 1, skip: 1 }\n"
    assert recent.own_test_skipped(root, c, out) == "POSIX signal forwarding"
    # A skipped test the commit didn't touch says nothing about it.
    other = "    ok 1 - POSIX signal forwarding\n    ok 2 - reads the file # SKIP\n"
    assert recent.own_test_skipped(root, c, other) == ""
