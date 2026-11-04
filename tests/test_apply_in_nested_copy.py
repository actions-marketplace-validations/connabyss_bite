"""The dotenv hunt (2026-11-03): on npm projects Bite's copies live in node_modules/bite_tmp, inside the project's
own git folder. There, git apply read the patch's paths from the project's top, matched nothing, changed nothing,
and said it worked, so "taken out of today's code" ran today's code unchanged, and all 8 dotenv "its test is gone"
were false. No key, no network."""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import recent  # noqa: E402

DIFF = (b"diff --git a/shop.js b/shop.js\n--- a/shop.js\n+++ b/shop.js\n@@ -1 +1 @@\n"
        b"-exports.total = (a, b) => a + b;\n+exports.total = (a, b) => Math.round((a + b) * 100) / 100;\n")
FIXED = "exports.total = (a, b) => Math.round((a + b) * 100) / 100;\n"


def test_taking_a_change_out_of_a_copy_inside_the_project_changes_the_copy(tmp_path):
    root = tmp_path / "proj"
    copy = root / "node_modules" / "bite_tmp" / "bite_copy"
    copy.mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    (copy / "shop.js").write_text(FIXED, newline="\n")
    assert recent.git_apply_ok(copy, DIFF, "-R", "--check")
    assert recent.git_apply_ok(copy, DIFF, "-R")
    assert (copy / "shop.js").read_text() == "exports.total = (a, b) => a + b;\n"
    # And a patch that doesn't fit is refused there, not waved through.
    assert not recent.git_apply_ok(copy, DIFF, "-R", "--check")
