"""#154 made the luck check and the piece check rerun only the pytest tests that noticed a change. Go, Rust and
.NET projects still ran their whole suite for each of those, so a first run there took several times as long as it
had to. Now go test, cargo test and dotnet test rerun only the tests that failed too, and every other runner (or a
command Bite can't safely change) still runs the whole suite. No key, no network."""

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
HERE = Path(".")

GO_OUT = """--- FAIL: TestTotal (0.00s)
    shop_test.go:8: got 0.30000000000000004
--- FAIL: TestCases (0.00s)
    --- FAIL: TestCases/empty (0.00s)
FAIL
FAIL\tshop\t0.002s
"""
CARGO_OUT = """running 3 tests
test tests::rounds ... FAILED
test tests::empty ... ok
test it_works ... FAILED

failures:
"""
DOTNET_OUT = """  Failed Shop.Tests.TotalTests.Rounds [12 ms]
  Error Message:
   Assert.Equal() Failure
  Failed Shop.Tests.LabelTests.Trims [1 ms]
"""


def test_go_reruns_only_the_tests_that_failed():
    assert recent.only_these("go test -count=1 ./...", GO_OUT, HERE) == 'go test -run "^(TestTotal|TestCases)$" -count=1 ./...'
    # A -run the project had is replaced, not added to (go test keeps only the last one).
    assert recent.only_these("go test -run Shop ./...", GO_OUT, HERE) == 'go test -run "^(TestTotal|TestCases)$" ./...'


def test_cargo_reruns_only_the_tests_that_failed():
    assert recent.only_these("cargo test", CARGO_OUT, HERE) == "cargo test -- --exact tests::rounds it_works"
    assert recent.only_these("cargo test -- --test-threads=1", CARGO_OUT, HERE) == \
        "cargo test -- --test-threads=1 --exact tests::rounds it_works"


def test_dotnet_reruns_only_the_tests_that_failed():
    assert recent.only_these('dotnet test Shop.sln --filter "Category=Fast"', DOTNET_OUT, HERE) == \
        'dotnet test Shop.sln --filter "FullyQualifiedName=Shop.Tests.TotalTests.Rounds|' \
        'FullyQualifiedName=Shop.Tests.LabelTests.Trims"'


def test_the_whole_suite_answers_when_its_unclear():
    assert recent.only_these("npm test", "  ✕ adds up (3 ms)\n", HERE) == ""  # npm test: any runner, any output
    assert recent.only_these("mvn test", "[ERROR] ShopTest.total:12 expected", HERE) == ""
    assert recent.only_these("go test ./... && go vet ./...", GO_OUT, HERE) == ""  # more than one command
    assert recent.only_these("go test ./...", "FAIL\tshop [build failed]\n", HERE) == ""  # no test named
    assert recent.only_these("cargo test", "test src/lib.rs - total (line 3) ... FAILED\n", HERE) == ""  # a doc example
    assert recent.only_these("dotnet test", "  Failed Shop.Tests.T.Adds(a: 1, b: 2) [1 ms]\n", HERE) == ""  # a theory case
    many = "".join(f"--- FAIL: Test{i} (0.00s)\n" for i in range(41))
    assert recent.only_these("go test ./...", many, HERE) == ""


def git_commit(root, msg):
    subprocess.run([*GIT, "add", "-A"], cwd=root, check=True)
    subprocess.run([*GIT, "commit", "-q", "-m", msg], cwd=root, check=True)


def bite(root):
    p = subprocess.run([sys.executable, RECENT, "--free", "--json"], cwd=root, capture_output=True, text=True,
                       encoding="utf-8", timeout=600, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    import json
    return json.loads(p.stdout)["commits"][0], p.stderr


GO_START = "package shop\n\nimport \"strings\"\n\nfunc Total(a, b float64) float64 { return a + b }\n\n" \
           "func Label(s string) string { return strings.ToUpper(s) }\n"
GO_FIX = "package shop\n\nimport (\n\t\"math\"\n\t\"strings\"\n)\n\n" \
         "func Total(a, b float64) float64 { return math.Round((a+b)*100) / 100 }\n\n" \
         "func Label(s string) string { return strings.ToUpper(strings.TrimSpace(s)) }\n"


@pytest.mark.skipif(not shutil.which("go"), reason="needs go")
def test_go_the_slow_tests_run_only_with_the_change_in_and_out(tmp_path):
    runs = tmp_path / "slow_runs.txt"
    root = tmp_path / "shop"
    root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    (root / "go.mod").write_text("module shop\n\ngo 1.18\n")
    (root / "shop.go").write_text(GO_START)
    (root / "shop_test.go").write_text(
        'package shop\n\nimport (\n\t"os"\n\t"testing"\n)\n\n'
        'func TestTotal(t *testing.T) {\n\tif Total(0.1, 0.2) != 0.3 {\n\t\tt.Fatal(Total(0.1, 0.2))\n\t}\n}\n\n'
        'func TestLabel(t *testing.T) {\n\tif Label(" a ") != "A" {\n\t\tt.Fatal(Label(" a "))\n\t}\n}\n\n'
        f'func TestSlow(t *testing.T) {{\n\tf, _ := os.OpenFile(`{runs}`, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)\n'
        '\tf.WriteString("x")\n\tf.Close()\n}\n')
    (root / ".bite.ini").write_text("[bite]\ntest_command = go test -count=1 ./...\n")
    git_commit(root, "Start")
    (root / "shop.go").write_text(GO_FIX)
    git_commit(root, "Fix total rounding and trim the label")
    c, log = bite(root)
    assert c["result"] == "noticed", (c, log)
    # With the change in, then out. Before, the luck check and the piece check each ran the whole suite again too.
    assert runs.read_text() == "xx", (runs.read_text(), log)


RS_START = "pub fn total(a: f64, b: f64) -> f64 {\n    a + b\n}\n\npub fn label(s: &str) -> String {\n    s.to_uppercase()\n}\n"
RS_FIX = "pub fn total(a: f64, b: f64) -> f64 {\n    ((a + b) * 100.0).round() / 100.0\n}\n\n" \
         "pub fn label(s: &str) -> String {\n    s.trim().to_uppercase()\n}\n"


@pytest.mark.skipif(not shutil.which("cargo"), reason="needs cargo")
def test_cargo_the_slow_tests_run_only_with_the_change_in_and_out(tmp_path):
    runs = tmp_path / "slow_runs.txt"
    root = tmp_path / "shop"
    (root / "src").mkdir(parents=True)
    (root / "tests").mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    (root / "Cargo.toml").write_text('[package]\nname = "shop"\nversion = "0.1.0"\nedition = "2021"\n')
    (root / ".gitignore").write_text("target\n")
    (root / "src" / "lib.rs").write_text(RS_START)
    path = str(runs).replace("\\", "\\\\")
    (root / "tests" / "shop.rs").write_text(
        "#[test]\nfn total() {\n    assert_eq!(shop::total(0.1, 0.2), 0.3);\n}\n\n"
        "#[test]\nfn label() {\n    assert_eq!(shop::label(\" a \"), \"A\");\n}\n\n"
        "#[test]\nfn slow() {\n    use std::io::Write;\n    let mut f = std::fs::OpenOptions::new().append(true)"
        f".create(true).open(\"{path}\").unwrap();\n    f.write_all(b\"x\").unwrap();\n}}\n")
    (root / ".bite.ini").write_text("[bite]\ntest_command = cargo test\ntest_covers = src/*, tests/*\n")
    git_commit(root, "Start")
    (root / "src" / "lib.rs").write_text(RS_FIX)
    git_commit(root, "Fix total rounding and trim the label")
    c, log = bite(root)
    assert c["result"] == "noticed", (c, log)
    assert runs.read_text() == "xx", (runs.read_text(), log)


def test_a_quoted_cross_in_a_traceback_is_not_a_test_name():
    # pytest prints the failing line's source; a ✕ inside it (as in a test of jest output) was read as a jest
    # failure, and Bite's PR comment named `adds up (3 ms)\n", HERE) == ""` as the test that noticed.
    out = '>       assert f("  ✕ adds up (3 ms)\\n", HERE) == ""\nFAILED tests/test_x.py::test_total - assert 1\n'
    assert recent.caught_by(out) == "`test_total`"
    assert recent.caught_by("  ✓ ok (1 ms)\n  ✕ adds up (3 ms)\n") == "`adds up`"
