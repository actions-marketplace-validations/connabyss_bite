"""bot/merge_shards.py: the weekly self-check runs on several machines at once (bite --shard K/N); one last job
gathers what each found into one report for bot/self_check.py. No gap may get lost on the way. No network."""

import os
import subprocess
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KIT / "bot"))
import merge_shards  # noqa: E402

PART = "# Bite: changes no test noticed\n\nintro\n\n## 1. {sha} {title}\n\n- What Bite saw: nothing noticed\n\n```\nsteps\n```\n"


def part(root, name, *gaps, test=None):
    d = root / name / "bite_proof"
    d.mkdir(parents=True)
    if gaps:
        text = PART.format(sha=gaps[0][0], title=gaps[0][1])
        for i, (sha, title) in enumerate(gaps[1:], 2):
            text += f"\n## {i}. {sha} {title}\n\nmore\n"
        (d / "FREE_REPORT.md").write_text(text, encoding="utf-8")
    if test:
        (d / "missing_tests" / "tests").mkdir(parents=True)
        (d / "missing_tests" / "tests" / test).write_text("def test_x():\n    pass\n")


def test_every_parts_gaps_and_tests_end_up_in_one_report(tmp_path):
    parts = tmp_path / "parts"
    part(parts, "shard-1", ("aaaaaaaa", "Fix a"), test="test_a.py")
    part(parts, "shard-2")  # a part where every change was noticed writes no report
    part(parts, "shard-3", ("bbbbbbbb", "Fix b"), ("cccccccc", "Fix c"), test="test_b.py")
    out = tmp_path / "bite_proof"
    r = subprocess.run([sys.executable, str(KIT / "bot" / "merge_shards.py"), str(parts), str(out)],
                       capture_output=True, text=True, check=True)
    assert r.stdout.strip() == "aaaaaaaa,bbbbbbbb,cccccccc"
    report = (out / "FREE_REPORT.md").read_text(encoding="utf-8")
    import self_check
    assert self_check.gaps(report) == [("aaaaaaaa", "Fix a"), ("bbbbbbbb", "Fix b"), ("cccccccc", "Fix c")]
    assert "## 3. cccccccc Fix c" in report
    assert sorted(p.name for p in (out / "missing_tests" / "tests").iterdir()) == ["test_a.py", "test_b.py"]


def test_no_gaps_anywhere_writes_no_report(tmp_path):
    parts = tmp_path / "parts"
    part(parts, "shard-1")
    part(parts, "shard-2")
    assert merge_shards.merge(parts, tmp_path / "bite_proof") == []
    assert not (tmp_path / "bite_proof" / "FREE_REPORT.md").exists()


def test_every_parts_remembered_checks_are_kept_for_next_time(tmp_path):
    parts = tmp_path / "parts"
    for i, sha in enumerate(("aaaa", "bbbb"), 1):
        d = parts / f"part-{i}" / "bite_proof"
        d.mkdir(parents=True)
        (d / "checked.json").write_text(f'{{"{sha}": {{"key": "k", "undo": "guarded"}}}}')
    merge_shards.merge(parts, tmp_path / "out")
    import json
    assert set(json.loads((tmp_path / "out" / "checked.json").read_text())) == {"aaaa", "bbbb"}


def test_one_table_of_every_change_every_machine_checked(tmp_path):
    import json
    parts = tmp_path / "parts"
    for i, (sha, result, label) in enumerate([("aaaa1111", "noticed", "noticed by test_a"),
                                               ("bbbb2222", "no_test_noticed", "NO TEST NOTICED")], 1):
        d = parts / f"part-{i}"
        d.mkdir(parents=True)
        (d / "results.json").write_text(json.dumps({"commits": [
            {"sha": sha * 5, "subject": f"Fix {sha}", "result": result, "label": label}]}))
    summary = tmp_path / "summary.md"
    p = subprocess.run([sys.executable, str(KIT / "bot" / "merge_shards.py"), str(parts), str(tmp_path / "out")],
                       capture_output=True, text=True, encoding="utf-8", env={**os.environ, "GITHUB_STEP_SUMMARY": str(summary)})
    table = (tmp_path / "out" / "SUMMARY.md").read_text(encoding="utf-8")
    assert "`aaaa1111` | Fix aaaa1111 | ✅ noticed by test_a" in table and "`bbbb2222` | Fix bbbb2222 | ❌ NO TEST NOTICED" in table
    assert "2 checked: 1 ✅" in table and table in summary.read_text(encoding="utf-8")
    assert "Gathered 2 checked changes from 2 machines: 1 with a test that noticed" in p.stderr
