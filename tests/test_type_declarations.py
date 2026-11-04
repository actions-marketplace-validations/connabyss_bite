"""dayjs on CH's PC (11-03): commits that changed only types/index.d.ts were checked and flagged "no test
noticed". A .d.ts file holds types only, so no test runs it: it now counts as code the tests can't run, like a file
in another language. No key, no network."""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import recent  # noqa: E402
import repo  # noqa: E402

GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"]


def test_a_type_declaration_file_is_code_the_tests_cant_run(tmp_path):
    root = tmp_path / "lib"
    (root / "types").mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    (root / ".bite.ini").write_text("[bite]\ntest_command = npm test\n")
    (root / "index.ts").write_text("export const total = (xs: number[]) => xs.reduce((a, b) => a + b, 0);\n")
    (root / "types" / "index.d.ts").write_text("export declare function total(xs: number[]): number;\n")
    subprocess.run([*GIT, "add", "-A"], cwd=root, check=True)
    subprocess.run([*GIT, "commit", "-q", "-m", "start"], cwd=root, check=True)
    (root / "types" / "index.d.ts").write_text("export declare function total(xs: readonly number[]): number;\n")
    (root / "index.ts").write_text("export const total = (xs: readonly number[]) => xs.reduce((a, b) => a + b, 0);\n")
    subprocess.run([*GIT, "commit", "-qam", "Fix total's types"], cwd=root, check=True)
    c = {"sha": repo.git(root, "rev-parse", "HEAD"), "subject": "Fix total's types", "body": ""}
    recent.files_of(root, c, repo.load_cfg(root))
    assert c["other_lang"] == ["types/index.d.ts"], c
    assert c["code"] == ["index.ts"], c
