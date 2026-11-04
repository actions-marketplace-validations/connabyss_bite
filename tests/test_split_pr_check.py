"""Bite's own pull request check, split across machines (2026-11-04): each part checks some commits (--shard K/N),
and the bite job runs the action with what the parts remembered, so it re-checks only what's left. 17 commits took
about 30 minutes on one machine. No key, no network."""

import re
import subprocess
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
PY = sys.executable
FLOW = (KIT / ".github" / "workflows" / "bite.yml").read_text(encoding="utf-8")
ACTION = (KIT / "action.yml").read_text(encoding="utf-8")


def git(root, *a):
    return subprocess.run(["git", *a], cwd=root, check=True, capture_output=True, text=True).stdout


def commit(root, msg):
    git(root, "add", "-A")
    git(root, "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", "commit", "-q", "-m", msg)
    return git(root, "rev-parse", "HEAD").strip()[:8]


def bite(root, *args):
    return subprocess.run([PY, str(KIT / "recent.py"), "--free", "--any", "--free-checks", "10", *args], cwd=root,
                          capture_output=True, text=True, timeout=300).stdout


def plan(commits):
    """Run the plan job's script as the workflow does: its outputs for a pull request of this many commits."""
    import json
    import os
    import shutil
    import tempfile
    import pytest
    bash = shutil.which("bash")
    if not bash or os.name == "nt":
        pytest.skip("the plan step runs in bash on Linux")
    script = re.search(r"  plan:.*?run: \|\n(.*?)\n\n", FLOW, re.S)[1]
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "out"
        subprocess.run([bash, "-c", script], check=True, env={**os.environ, "COMMITS": str(commits),
                                                              "GITHUB_OUTPUT": str(out)})
        got = dict(ln.split("=", 1) for ln in out.read_text().splitlines())
    return json.loads(got["parts"]), int(got["total"])


def test_each_commit_gets_a_machine_of_its_own_up_to_the_action_limit():
    max_commits = int(re.search(r"max-commits:.*?default: \"(\d+)\"", ACTION, re.S)[1])
    assert plan(3) == ([1, 2, 3], 3)
    assert plan(1) == ([1], 1)
    assert plan(0) == ([1], 1)  # a matrix of nothing fails the whole run
    assert plan(25) == (list(range(1, max_commits + 1)), max_commits)
    # every part 1..N runs, and each takes its share of N: together they check every commit
    assert "part: ${{ fromJSON(needs.plan.outputs.parts) }}" in FLOW
    assert "--shard ${{ matrix.part }}/${{ needs.plan.outputs.total }}" in FLOW
    # one commit needs no part machine: the bite job (which runs whatever the parts did) checks it itself
    assert "if: fromJSON(needs.plan.outputs.total) > 1" in re.search(r"\n  part:.*?steps:", FLOW, re.S)[0]


def test_the_parts_match_the_action_run():
    # What a part remembers counts in the action's run only with the same options (they're in the ✅'s key).
    part = re.search(r"bite --free .*?--part-runs (\d+)", FLOW)[1]
    assert re.search(r"args: --part-runs (\d+)", FLOW)[1] == part
    max_commits = re.search(r"max-commits:.*?default: \"(\d+)\"", ACTION, re.S)[1]
    assert f'[ "$n" -gt {max_commits} ] && n={max_commits}' in FLOW  # the same commits as the action checks
    assert f'[ "$n" -gt {max_commits} ] && n={max_commits}' in re.search(r"  plan:.*?\n\n", FLOW, re.S)[0]


def test_the_gathered_memory_is_where_the_action_restores_it_from():
    restore = re.search(r"restore-keys: \|\n\s+(bite-checked-\$\{\{ github.event.pull_request.number)", ACTION)[1]
    saved = re.search(r"cache/save@.*?path: (\S+)\n\s+key: (.+)", FLOW, re.S)
    assert saved[1] == "bite_proof/checked.json"  # a cache is only found again under the same path
    assert re.search(r"cache/restore@.*?path: (\S+)", ACTION, re.S)[1] == saved[1]
    assert saved[2].startswith(restore)
    assert "needs: part" in FLOW and "if: always()" in FLOW  # the check named bite still reports when a part fails


def test_parts_gathered_leave_nothing_noticed_to_check_again(tmp_path):
    root = tmp_path / "proj"
    (root / "tests").mkdir(parents=True)
    git(root, "init", "-q")
    (root / ".bite.ini").write_text(f"[bite]\ntest_command = {PY} -m pytest -q -p no:cacheprovider\n")
    (root / "shop.py").write_text("def total(xs):\n    return sum(xs)\n")
    commit(root, "start")
    shas = []
    for name in ("a", "b", "c"):  # three fixes, each with its own test
        with open(root / "shop.py", "a") as f:
            f.write(f"\n\ndef {name}(x):\n    return x + 1\n")
        (root / "tests" / f"test_{name}.py").write_text(f"import shop\n\n\ndef test_{name}():\n"
                                                        f"    assert shop.{name}(1) == 2\n")
        shas.append(commit(root, f"Fix {name}"))
    for k in (1, 2):  # two machines, each with its own copy of the project
        part = tmp_path / f"m{k}"
        git(tmp_path, "clone", "-q", str(root), str(part))
        out = bite(part, "--shard", f"{k}/2")
        assert "noticed by" in out, out
        dest = tmp_path / "parts" / f"bite-part-{k}"
        dest.mkdir(parents=True)
        (dest / "checked.json").write_bytes((part / "bite_proof" / "checked.json").read_bytes())
    subprocess.run([PY, str(KIT / "bot" / "merge_shards.py"), str(tmp_path / "parts"), str(root / "bite_proof")],
                   check=True, capture_output=True)
    out = bite(root)
    assert "3 commits checked before with" in out, out
    for sha in shas:
        assert any(ln.startswith(f"  {sha} ") and "noticed by test_" in ln for ln in out.splitlines()), out
